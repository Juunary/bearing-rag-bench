"""Knowledge bundle for serving: curated guide pages that answer a question when it matches one of them (kb_first).

[EN]
- Role: the serving-side counterpart of experiments/run_kb.py. The pages of data/kb (type "guide", written by an AI
  agent and reviewed by a person) are matched to the question with the same ConceptMatcher as the concept pages:
  alias match on the question and its English translation first, otherwise the best dense match (cosine of the
  question against the page text, bge-m3 shared with the dense retriever) above `dense_min`. When a page matches,
  the pipeline skips retrieval and gives the generator the bundle as context ("kb" path); otherwise it retrieves as
  usual ("rag" path). On the 20 practical questions of eval/kb this decision matched all 16 in-scope questions and
  none of the 4 out-of-scope ones (README, "정리된 지식 번들").
- Context modes: "all" = every page (about 10k tokens for 12 pages; the setting that was graded), "matched" = the
  matched pages plus their `related` pages (cheaper, not graded by a person).
- Bundle passages are cited as kb_<page id>#0, so output validation and the chat UI work unchanged.

[KO]
- 역할: experiments/run_kb.py의 서비스 쪽 구현. data/kb의 안내 페이지(type "guide", AI 초안 + 사람 검수)를 개념 페이지와 같은
  ConceptMatcher로 질문에 매칭한다: 질문·영어 번역의 별칭 일치 우선, 없으면 페이지 본문과의 dense 코사인(dense 검색기와 공유하는
  bge-m3)이 `dense_min` 이상인 상위 1개. 매칭되면 검색을 건너뛰고 번들을 컨텍스트로 생성한다("kb" 경로), 아니면 기존 검색("rag").
  eval/kb의 실무 질문 20개에서 이 분기는 주제 안 16개를 모두, 주제 밖 4개는 하나도 매칭하지 않았다.
- 컨텍스트: "all" = 페이지 전부(12쪽 약 1만 토큰, 사람이 채점한 설정), "matched" = 매칭 페이지 + related 페이지(더 싸지만 미채점).
- 번들 문단은 kb_<페이지 id>#0으로 인용되어 출력 검증과 채팅 UI가 그대로 동작한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ragbench.concepts import Concept, ConceptMatch, ConceptMatcher, load_concepts

CONTEXT_MODES = ("all", "matched")


def page_passage(c: Concept) -> dict[str, Any]:
    return {"chunk_id": f"kb_{c.id}#0", "doc_id": f"kb_{c.id}", "lang": "ko", "text": f"{c.title}\n{c.description}", "kb": True}


class KnowledgeBundle:
    def __init__(self, directory: str | Path, embedder=None, dense_min: float = 0.55, context: str = "all"):
        if context not in CONTEXT_MODES:
            raise ValueError(f"context must be one of {CONTEXT_MODES}, got {context!r}")
        self.directory, self.context = str(directory), context
        self.pages = load_concepts(directory)
        self.by_id = {c.id: c for c in self.pages}
        self.passages = {c.id: page_passage(c) for c in self.pages}
        self.matcher = ConceptMatcher(self.pages, embedder=embedder, dense_top=1, dense_min=dense_min)
        self.matcher.index()
        self.embedder = embedder

    @property
    def verified(self) -> int:
        return sum(c.verified for c in self.pages)

    def match(self, question: str, english: str | None = None) -> ConceptMatch:
        # 페이지가 한국어라 dense 매칭은 질문 원문을 임베딩한다 (실험 run_kb.py와 같은 규칙)
        qvec = self.embedder.encode_queries([question])[0] if self.embedder is not None else None
        return self.matcher.match(question, english or question, qvec)

    def context_for(self, m: ConceptMatch) -> list[dict[str, Any]]:
        if self.context == "all":
            return [self.passages[c.id] for c in self.pages]
        return [self.passages[i] for i in m.ids_with_related if i in self.passages]
