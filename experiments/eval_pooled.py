"""Re-score the v2 retrieval runs with the pooled relevance labels -> experiments/results/v2_pooled.md.

[EN]
- Role: gold' = original gold chunks + pooled chunks that the judges labelled >= 1 (grade = the label).
  Every v2 run on the 384-token chunk set is re-scored from its stored rankings; nothing is retrieved again.
  Reports nDCG@10 / Recall@5 with the original and the pooled gold, the agreement of the system order
  (Kendall tau), the judges' accuracy on the controls, and paired comparisons on the pooled nDCG@10.
- The labels are AI judgements, not human ones; pooled numbers are a robustness check of the ranking of
  systems, not a replacement of the gold.
- Usage: uv run python experiments/eval_pooled.py

[KO]
- 역할: gold' = 원래 gold 청크 + 판정자가 1 이상으로 라벨한 풀 청크(등급 = 라벨). 384토큰 청크 세트의 모든
  v2 실행을 저장된 순위로 다시 채점한다(다시 검색하지 않음). 원래 gold와 풀링 gold의 nDCG@10 / Recall@5,
  시스템 순서의 일치(Kendall tau), 대조군에서의 판정자 정확도, 풀링 nDCG@10의 쌍체 비교를 보고한다.
- 라벨은 사람이 아닌 AI 판정이다. 풀링 숫자는 시스템 순위의 견고성 점검이며 gold를 대체하지 않는다.
- 사용: uv run python experiments/eval_pooled.py
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ragbench.evalset import load_queries  # noqa: E402
from ragbench.ingest import REPO  # noqa: E402
from ragbench.metrics import ndcg_at_k, recall_at_k  # noqa: E402
from ragbench.stats import compare  # noqa: E402

POOL = REPO / "eval" / "pool"


def kendall_tau(a: list[float], b: list[float]) -> float:
    conc = disc = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            s = (a[i] - a[j]) * (b[i] - b[j])
            conc += s > 0
            disc += s < 0
    return (conc - disc) / max(1, conc + disc)


def main() -> None:
    index = json.loads((POOL / "pool_index.json").read_text(encoding="utf-8"))
    labels: dict[str, dict] = {}
    for f in sorted(glob.glob(str(POOL / "label_output_*.json"))):
        for r in json.loads(Path(f).read_text(encoding="utf-8")):
            labels[r["id"]] = r
    missing = [i for i in index["items"] if i not in labels]
    out = ["# v2 pooled re-scoring", "", f"pool: {len(index['items'])} judged chunks, {len(missing)} without a label, depth {index['depth']}, {len(index['configs'])} configs", ""]

    # 대조군 정확도
    ctl = {"gold": [0, 0], "random": [0, 0]}
    for pid, it in index["items"].items():
        if it["control"] and pid in labels:
            ok = labels[pid]["label"] >= 1 if it["control"] == "gold" else labels[pid]["label"] == 0
            ctl[it["control"]][0] += ok
            ctl[it["control"]][1] += 1
    out += ["## Judge controls", "", f"- known gold chunks labelled >= 1: {ctl['gold'][0]}/{ctl['gold'][1]}",
            f"- random chunks of other documents labelled 0: {ctl['random'][0]}/{ctl['random'][1]}", ""]

    extra: dict[str, dict[str, int]] = {}      # qid -> {chunk_id: grade}
    for pid, it in index["items"].items():
        if not it["control"] and pid in labels and labels[pid]["label"] >= 1:
            extra.setdefault(it["qid"], {})[it["chunk_id"]] = int(labels[pid]["label"])
    n_added = sum(len(v) for v in extra.values())
    queries = {q["qid"]: q for q in load_queries(REPO / "eval" / "queries_v2.jsonl")}
    out += [f"pooled relevant chunks added to gold': {n_added} in {len(extra)} questions", ""]

    rows, scores = [], {}
    for name in index["configs"]:
        d = json.loads((REPO / "experiments" / "results" / f"{name}.json").read_text(encoding="utf-8"))
        o_nd, p_nd, o_rc, p_rc = [], [], [], []
        for q in d["per_query"]:
            g2 = {**q["gold"]}
            for cid, gr in extra.get(q["qid"], {}).items():
                g2[cid] = max(g2.get(cid, 0), gr)
            o_nd.append(ndcg_at_k(q["ranked"], q["gold"], 10)); p_nd.append(ndcg_at_k(q["ranked"], g2, 10))
            o_rc.append(recall_at_k(q["ranked"], q["gold"], 5)); p_rc.append(recall_at_k(q["ranked"], g2, 5))
        scores[name] = (np.array(o_nd), np.array(p_nd))
        rows.append((name, np.mean(o_nd), np.mean(p_nd), np.mean(o_rc), np.mean(p_rc)))
    out += ["## nDCG@10 and Recall@5, original gold vs pooled gold'", "", "| config | nDCG orig | nDCG pooled | R@5 orig | R@5 pooled |", "|---|---|---|---|---|"]
    for n, a, b, c, e in rows:
        out.append(f"| {n.removeprefix('v2_')} | {a:.3f} | {b:.3f} | {c:.3f} | {e:.3f} |")
    tau = kendall_tau([r[1] for r in rows], [r[2] for r in rows])
    out += ["", f"Kendall tau between the system order by original and by pooled nDCG@10: {tau:.3f} ({len(rows)} systems)", ""]

    first = next(iter(scores))
    qids = [q["qid"] for q in json.loads((REPO / "experiments" / "results" / f"{first}.json").read_text(encoding="utf-8"))["per_query"]]
    clusters = [queries[i]["gold"][0]["doc_id"] for i in qids]
    pairs = [("v2_b_rrf_en_rerank", "v2_b_rrf_rerank"), ("v2_b_bm25_en", "v2_b_bm25_kiwi"), ("v2_b_bm25_en", "v2_b_dense"),
             ("v2_x1_rrf3_rerank", "v2_b_rrf_en_rerank"), ("v2_x5_bm25_en_multi", "v2_b_bm25_en"), ("v2_x4_bm25_en_stem", "v2_b_bm25_en")]
    out += ["## Paired comparisons on pooled nDCG@10 (A - B)", "", "| A | B | mean diff | 95% CI (question) | 95% CI (cluster) | better/worse/tie |", "|---|---|---|---|---|---|"]
    for a, b in pairs:
        if a in scores and b in scores:
            c = compare(scores[a][1] - scores[b][1], clusters)
            out.append(f"| {a.removeprefix('v2_')} | {b.removeprefix('v2_')} | {c['mean']:+.3f} | {c['ci_iid'][0]:+.3f} .. {c['ci_iid'][1]:+.3f} | "
                       f"{c['ci_cluster'][0]:+.3f} .. {c['ci_cluster'][1]:+.3f} | {c['better']}/{c['worse']}/{c['tie']} |")
    text = "\n".join(out) + "\n"
    (REPO / "experiments" / "results" / "v2_pooled.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
