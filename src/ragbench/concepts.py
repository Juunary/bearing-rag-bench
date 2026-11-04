"""Concept bundle (data/concepts/*.md): pages with ko/en/de aliases, a short description and links, matched to queries.

[EN]
- Role: the bridge between a user's wording and the corpus wording. A query such as "oil seal" reaches the
  concept page "radial shaft seal", whose aliases (RWDR, Wellendichtring, ...) are what the documents say.
  The retrieval side (retrieval/concept.py) then ranks the chunks that mention the matched concepts.
- Page format (OKF-style, one Markdown file per concept, YAML front matter):
    ---
    id: radial_shaft_seal        # must equal the file stem
    type: concept
    title: radial shaft seal     # canonical English name (also used as an English alias)
    names: {en: [...], ko: [...], de: [...]}
    related: [sealing_lip, ...]  # ids of other pages in the bundle (1 hop is used at search time)
    docs: [en_radial_shaft_seal] # optional, document ids only (never chunk ids)
    ---
    Two to four neutral English sentences.
- Alias matching (`alias_in_text`, shared by query matching and chunk mapping so the two cannot drift):
  ko/de forms are case-insensitive substrings (ko also compared with spaces removed, so 오일씰 / 오일 씰에서 match);
  en forms match on word boundaries with an optional plural s/es; an all-uppercase abbreviation (RWDR) is
  case-sensitive. A matched form that is part of a longer matched form is dropped (as in translate.glossary_hint).
- Dense matching (cosine between the query and the page text) is a fallback used only when no alias matched,
  so a query without any concept keeps the retrieval it had.

[KO]
- 역할: 사용자의 표현과 문서의 표현 사이의 다리. "오일 씰"이라는 질문이 개념 페이지 "radial shaft seal"에 닿고, 그
  페이지의 별칭(RWDR, Wellendichtring, ...)이 문서가 쓰는 말이다. 검색 쪽(retrieval/concept.py)은 매칭된 개념이 나오는
  청크를 순위 매긴다.
- 페이지 형식: 개념당 마크다운 파일 하나, YAML 머리말(id = 파일 이름, type, title, names, related, docs) + 영어 설명 2~4문장.
- 별칭 매칭(`alias_in_text`, 질의 매칭과 청크 매핑이 같은 함수를 쓴다): ko/de는 대소문자 무시 부분 문자열(ko는 공백을 뺀
  형태도 비교), en은 단어 경계 + 복수형 s/es 허용, 전부 대문자 약어는 대소문자 구분. 더 긴 매칭 형태에 포함된 짧은 형태는
  버린다(translate.glossary_hint와 같은 규칙).
- dense 매칭은 별칭이 하나도 안 맞을 때만 쓰는 대체 수단이라, 개념이 없는 질문은 원래 검색 그대로다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

_FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)
_WS = re.compile(r"\s+")
LANGS = ("en", "ko", "de")


@dataclass
class Concept:
    id: str
    title: str
    names: dict[str, list[str]]
    related: list[str]
    docs: list[str]
    description: str
    type: str = "concept"
    verified: bool = False       # guide 페이지: 사람이 내용을 검수했는지

    def aliases(self) -> list[tuple[str, str]]:
        """[(lang, form)]; the title counts as an English form."""
        out = [("en", self.title)]
        for lang in LANGS:
            out += [(lang, f) for f in self.names.get(lang, []) if (lang, f) not in out]
        return out

    def page_text(self) -> str:
        """Text embedded for dense matching: title, every alias, then the description."""
        forms = [f for _, f in self.aliases()]
        return f"{self.title}. {'; '.join(forms)}. {self.description}".strip()


def parse_concept_page(text: str, path: Path) -> Concept:
    import yaml

    m = _FRONT.match(text)
    if not m:
        raise ValueError(f"{path}: missing YAML front matter")
    meta = yaml.safe_load(m.group(1)) or {}
    # concept = 검색 다리용 개념 페이지, guide = 답변 근거로 쓰는 정리된 지식 페이지(data/kb)
    if meta.get("type") not in ("concept", "guide"):
        raise ValueError(f"{path}: type must be 'concept' or 'guide'")
    cid = str(meta.get("id", ""))
    if cid != path.stem:
        raise ValueError(f"{path}: id {cid!r} must equal the file stem")
    names = {lang: [str(f).strip() for f in (meta.get("names") or {}).get(lang, []) if str(f).strip()] for lang in LANGS}
    title = str(meta.get("title", "")).strip()
    if not title and not any(names.values()):
        raise ValueError(f"{path}: a concept needs a title or at least one alias")
    first = next((f for lang in LANGS for f in names[lang]), "")
    return Concept(id=cid, title=title or first, names=names, related=[str(r) for r in meta.get("related") or []],
                   docs=[str(d) for d in meta.get("docs") or []], description=m.group(2).strip(),
                   type=str(meta["type"]), verified=bool(meta.get("verified", False)))


def load_concepts(directory: str | Path) -> list[Concept]:
    """Every *.md page in the directory, sorted by file name; an empty directory gives []."""
    concepts = [parse_concept_page(p.read_text(encoding="utf-8"), p) for p in sorted(Path(directory).glob("*.md"))]
    ids = [c.id for c in concepts]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate concept ids")
    for c in concepts:
        unknown = [r for r in c.related if r not in ids]
        if unknown:
            raise ValueError(f"{c.id}: related ids not in the bundle: {unknown}")
    return concepts


def _is_abbreviation(form: str) -> bool:
    letters = [ch for ch in form if ch.isalpha()]
    return len(letters) >= 2 and all(ch.isupper() for ch in letters)


def alias_in_text(form: str, lang: str, text: str) -> bool:
    """Does the alias occur in the text? Same rule for queries and chunks."""
    if not form or not text:
        return False
    if lang == "en" or _is_abbreviation(form):
        # 영어: 단어 경계 + 복수형. 약어는 대소문자 그대로 (rwdr 같은 우연한 소문자열을 막음)
        flags = 0 if _is_abbreviation(form) else re.IGNORECASE
        return re.search(r"(?<![A-Za-z0-9])" + re.escape(form) + r"(?:e?s)?(?![A-Za-z0-9])", text, flags) is not None
    low_form, low_text = form.lower(), text.lower()
    if low_form in low_text:
        return True
    # 한국어: 띄어쓰기 변형("오일씰")과 조사가 붙은 형태("씰에서")는 공백을 뺀 문자열끼리 비교하면 잡힌다
    return lang == "ko" and _WS.sub("", low_form) in _WS.sub("", low_text)


def drop_contained(found: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Drop (concept, lang, form) whose form is a proper part of another matched form (across concepts)."""
    forms = [f.lower() for _, _, f in found]
    return [x for x in found if not any(x[2].lower() != g and x[2].lower() in g for g in forms)]


@dataclass
class ConceptMatch:
    alias: dict[str, list[str]] = field(default_factory=dict)     # concept id -> matched forms
    dense: list[tuple[str, float]] = field(default_factory=list)  # (concept id, cosine), fallback only
    related: list[str] = field(default_factory=list)              # 1 hop from the matched ids, minus the matched ids
    titles: dict[str, str] = field(default_factory=dict)

    @property
    def ids(self) -> list[str]:
        return list(dict.fromkeys([*self.alias, *(c for c, _ in self.dense)]))

    @property
    def ids_with_related(self) -> list[str]:
        return [*self.ids, *self.related]

    @property
    def canonical_names(self) -> list[str]:
        return [self.titles[c] for c in self.ids]

    def to_dict(self) -> dict[str, Any]:
        return {"alias": self.alias, "dense": [[c, round(s, 4)] for c, s in self.dense], "related": self.related,
                "ids": self.ids, "canonical_names": self.canonical_names}


class ConceptMatcher:
    """Query -> concepts: alias matching first, dense matching only when no alias matched."""

    def __init__(self, concepts: list[Concept], embedder=None, dense_top: int = 1, dense_min: float = 0.55):
        self.concepts = concepts
        self.by_id = {c.id: c for c in concepts}
        self.embedder, self.dense_top, self.dense_min = embedder, dense_top, dense_min
        self.page_emb: np.ndarray | None = None

    def index(self) -> None:
        if self.embedder is not None and self.concepts and self.dense_top > 0:
            self.page_emb = self.embedder.encode([c.page_text() for c in self.concepts])

    def match_aliases(self, original: str, english: str) -> dict[str, list[str]]:
        found = []
        for c in self.concepts:
            for lang, form in c.aliases():
                # ko/de 별칭은 원문 질의에서, 영어 별칭은 원문(괄호 영어 포함)과 번역 질의 둘 다에서 찾는다
                texts = [original, english] if lang == "en" else [original]
                if any(alias_in_text(form, lang, t) for t in texts):
                    found.append((c.id, lang, form))
        out: dict[str, list[str]] = {}
        for cid, _, form in drop_contained(found):
            out.setdefault(cid, []).append(form)
        return out

    def match_dense(self, qvec: np.ndarray | None) -> list[tuple[str, float]]:
        if self.page_emb is None or qvec is None:
            return []
        sims = self.page_emb @ qvec
        order = np.argsort(-sims)[: self.dense_top]
        return [(self.concepts[i].id, float(sims[i])) for i in order if sims[i] >= self.dense_min]

    def match(self, original: str, english: str, qvec: np.ndarray | None = None) -> ConceptMatch:
        alias = self.match_aliases(original, english)
        dense = [] if alias else self.match_dense(qvec)
        ids = list(dict.fromkeys([*alias, *(c for c, _ in dense)]))
        related = [r for c in ids for r in self.by_id[c].related if r not in ids]
        return ConceptMatch(alias=alias, dense=dense, related=list(dict.fromkeys(related)),
                            titles={c.id: c.title for c in self.concepts})
