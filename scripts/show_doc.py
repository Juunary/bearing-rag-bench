"""Print a document with section headings and numbered sentences, for writing eval anchors.

[EN]
- Role: helper for eval-set authoring. Shows the exact sentence strings the chunker will see,
  so an anchor can be copied verbatim (whitespace and punctuation included).
- Usage: uv run python scripts/show_doc.py en_rolling_element_bearing [--grep Käfig]
         uv run python scripts/show_doc.py --list            # all doc ids with size

[KO]
- 역할: 평가셋 작성 보조. 청커가 보는 문장 문자열을 그대로 보여 주어 anchor를 공백·구두점까지
  똑같이 복사할 수 있게 한다.
- 사용: 위 영문 예시와 같다. --grep은 특정 단어가 들어간 문장만 출력.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ragbench.chunking import SENT_SPLIT_RE  # noqa: E402
from ragbench.ingest import load_docs  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("doc_id", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--grep", help="only sentences containing this substring (case-insensitive)")
    args = ap.parse_args()
    docs = {d["doc_id"]: d for d in load_docs()}
    if args.list or not args.doc_id:
        for d in docs.values():
            print(f"{d['doc_id']:34} {d['lang']}  {d['n_chars']:6d} chars  {d['title']}")
        return
    d = docs[args.doc_id]
    print(f"# {d['doc_id']}  ({d['lang']})  {d['title']}  rev={d['revid']}\n")
    n = 0
    for s in d["sections"]:
        heading = " > ".join(s["path"]) or "(lead)"
        shown = False
        for para in s["text"].split("\n"):
            for sent in SENT_SPLIT_RE.split(para):
                if not sent.strip():
                    continue
                n += 1
                if args.grep and args.grep.lower() not in sent.lower():
                    continue
                if not shown:
                    print(f"\n== {heading}")
                    shown = True
                print(f"[{n:4d}] {sent}")


if __name__ == "__main__":
    main()
