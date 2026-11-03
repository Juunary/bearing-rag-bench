"""Answer one question with the contexts of several retrieval variants -> experiments/results/<name>.md.

[EN]
- Role: after experiments/trace_retrieval.py shows where the chunks with the answer drop out, check whether the
  answer changes when they reach the generator. The question given to the generator is always the original one;
  only the context changes: the served top k, the served top 2k, the final top k of each English query variant
  (searched without translation, same stages as trace_retrieval.py), and the final top k of the query translated
  with the glossary hints (data/glossary.json; the PDF configs translate without it).
- Generation: base bf16 Qwen3-4B on cuda:1, the serving prompt cite_refuse_v1, the same answer validation as the
  pipeline (a refusal or an answer without valid citations is blocked). Cached in logs/human_round2_cache.sqlite.
- Usage: uv run python experiments/answer_variants.py --config configs/pdf/pdfth_x13_rrf_en_dense_en_rerank_en_text.json
  --question "..." --name d05_answer_variants [--variant "english query" ...] [--target id ...]

[KO]
- 역할: experiments/trace_retrieval.py로 답이 있는 청크가 빠지는 단계를 찾은 뒤, 그 청크가 생성 모델에 가면 답이 달라지는지
  확인한다. 생성 모델에 주는 질문은 항상 원래 질문이고 컨텍스트만 바꾼다: 실제 상위 k, 실제 상위 2k, 영어 질의 변형마다
  최종 상위 k(번역 없이 검색, trace_retrieval.py와 같은 단계), 용어집 힌트(data/glossary.json)로 번역한 질의의 최종 상위 k
  (PDF 설정은 용어집 없이 번역한다).
- 생성: 기반 bf16 Qwen3-4B(cuda:1), 서비스 프롬프트 cite_refuse_v1, 파이프라인과 같은 답변 검증(거절이나 유효한 인용이 없는
  답은 차단). 캐시 logs/human_round2_cache.sqlite.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from trace_retrieval import trace  # noqa: E402

from ragbench.cache import LLMCache, make_key  # noqa: E402
from ragbench.chunking import load_chunks  # noqa: E402
from ragbench.config import ExperimentConfig, set_seed  # noqa: E402
from ragbench.generation import Generator, build_messages  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.retrieval.factory import build_retriever, share_translator_model  # noqa: E402
from ragbench.translate import Translator, load_glossary  # noqa: E402
from ragbench.validation import validate_answer  # noqa: E402

PROMPT, MODEL, MAX_NEW = "cite_refuse_v1", "Qwen/Qwen3-4B-Instruct-2507", 256


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--variant", action="append", default=[], help="English query, searched without translation")
    ap.add_argument("--target", nargs="*", default=[], help="chunks to mark in the context lists")
    ap.add_argument("--name", required=True)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()
    cfg = ExperimentConfig.load(args.config)
    set_seed(cfg.seed)
    chunks = load_chunks(cfg.chunking)
    by_id = {c["chunk_id"]: c for c in chunks}
    retriever = build_retriever(cfg)
    retriever.index(chunks)
    generator = Generator(MODEL, device="cuda:1")
    share_translator_model(retriever, generator)
    cache = LLMCache(REPO / "logs" / "human_round2_cache.sqlite")

    served = [cid for cid, _ in retriever.search(args.question, 2 * args.k)]
    # 용어집 번역: 같은 모델·같은 번역 캐시, 질의 프롬프트에 용어 힌트만 붙는다
    gl = Translator(REPO / "logs" / "translate_cache.sqlite", glossary=load_glossary(REPO / "data" / "glossary.json"))
    gl.use_generator(generator)
    gl_query = gl.translate(args.question, "query")["text"]
    sets = [("served top %d" % args.k, None, served[:args.k]), ("served top %d" % (2 * args.k), None, served)]
    for v in args.variant:
        sets.append(("variant", v, trace(retriever, cfg, len(chunks), v, args.target, args.k)[1][:args.k]))
    sets.append(("glossary translation", gl_query, trace(retriever, cfg, len(chunks), gl_query, args.target, args.k)[1][:args.k]))

    out = [f"# Answers with variant contexts: {args.name}", "", f"Config: `{args.config.name}`, generator {MODEL}, prompt {PROMPT}.",
           "", f"Question (given to the generator in every row): {args.question}", ""]
    for label, query, ids in sets:
        messages = build_messages(PROMPT, args.question, [by_id[i] for i in ids])
        key = make_key(generator.model_name, generator.revision, messages, MAX_NEW)
        res = cache.get(key)
        if res is None:
            res = generator.generate(messages, max_new_tokens=MAX_NEW)
            cache.put(key, res)
        v = validate_answer(res["text"], ids)
        marked = ", ".join(f"**{i}**" if i in args.target else i for i in ids)
        out += [f"## {label}" + (f": {query}" if query else ""), "", f"Context: {marked}", "",
                f"Outcome: {'blocked (' + str(v.reason) + ')' if not v.ok else 'answered'}", "", "> " + res["text"].replace("\n", "\n> "), ""]
    text = "\n".join(out)
    (REPO / "experiments" / "results" / f"{args.name}.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
