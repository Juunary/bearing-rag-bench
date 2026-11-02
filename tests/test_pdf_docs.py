import sys
from pathlib import Path

import pytest

from ragbench.chunking import chunk_set_id
from ragbench.config import ChunkingConfig
from ragbench.ingest import load_corpus

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_pdf_docs import build_doc  # noqa: E402

SRC = {"id": "pdf_x", "lang": "en", "title": "X", "landingUrl": "https://x", "url": "https://x/x.pdf", "license": "CC BY 4.0", "sha256": "0"}
META = {"pages": 2, "pdfEditorCommit": "abc"}


# 위키 코퍼스의 청크 세트 ID는 예전과 같아야 기존 청크·임베딩·번역 캐시가 계속 맞는다
def test_chunk_set_id_unchanged_for_wiki_and_suffixed_for_pdf():
    assert chunk_set_id(ChunkingConfig()) == "fixed_tok384_ov48"
    assert chunk_set_id(ChunkingConfig(corpus="wiki_pdf")) == "fixed_tok384_ov48_pdf"
    with pytest.raises(ValueError, match="unknown corpus"):
        load_corpus("pdf_only")


# 머리말·꼬리말·그림 글자는 빠지고, 제목은 절을 열고, 표는 행마다 한 줄, 참고문헌 절은 버린다
def test_build_doc_rules_and_block_offsets():
    rows = [
        {"page": 0, "kind": "paragraph", "role": "header", "text": "Running head"},
        {"page": 0, "kind": "paragraph", "role": "heading", "text": "1. Load ratings"},
        {"page": 0, "kind": "paragraph", "role": "body", "text": "The basic rating   life is L10."},
        {"page": 0, "kind": "table", "cells": [["Type", "C (kN)"], ["6205", "14.8"], ["", ""]], "rows": 3, "cols": 2},
        {"page": 0, "kind": "figure", "labels": ["0", "10"]},
        {"page": 0, "kind": "paragraph", "role": "body", "text": "Tabelle 3 Versuchsöle . . . . . . . . 55"},
        {"page": 1, "kind": "paragraph", "role": "footer", "text": "2"},
        {"page": 1, "kind": "paragraph", "role": "heading", "text": "5. References"},
        {"page": 1, "kind": "paragraph", "role": "body", "text": "[1] Someone, 2020."},
    ]
    d = build_doc(SRC, rows, META)
    assert [s["path"] for s in d["sections"]] == [["1. Load ratings"]]
    assert d["text"] == "The basic rating life is L10.\n| Type | C (kN) |\n| 6205 | 14.8 |"
    assert [(b["kind"], d["text"][b["start"]:b["end"]]) for b in d["blocks"]] == [
        ("paragraph", "The basic rating life is L10."), ("table", "| Type | C (kN) |\n| 6205 | 14.8 |")]
    assert d["source_type"] == "pdf" and d["extractor"]["pdf_editor_commit"] == "abc"


# 표 중간에서 시작하는 청크만 캡션·머리글을 반복하고, 두 줄 머리글(첫 행에 빈 칸)은 둘째 행까지 쓴다
def test_table_header_prefix_only_inside_a_table():
    from ragbench.chunking import table_header_prefix

    text = "TABLE II.—Load ratings\n|  | C (kN) |  |\n| Type | static | dynamic |\n| 6205 | 7.8 | 14.8 |\n| 6206 | 11.2 | 19.5 |"
    cap_end = text.index("\n")
    doc = {"text": text, "blocks": [{"kind": "paragraph", "start": 0, "end": cap_end},
                                    {"kind": "table", "start": cap_end + 1, "end": len(text)}]}
    assert table_header_prefix(doc, text.index("| 6206")) == "TABLE II.—Load ratings\n|  | C (kN) |  |\n| Type | static | dynamic |"
    assert table_header_prefix(doc, cap_end + 1) == ""          # 표 첫 행에서 시작하면 머리글이 이미 들어 있다
    assert table_header_prefix(doc, 0) == ""                    # 표 밖
    assert chunk_set_id(ChunkingConfig(corpus="wiki_pdf", table_header=True)) == "fixed_tok384_ov48_pdf_th"


# 두 줄 머리글의 둘째 줄에서 시작하는 청크도 첫 줄이 빠져 있으므로 머리글 전체를 붙인다
def test_table_header_prefix_when_chunk_starts_in_second_header_line():
    from ragbench.chunking import table_header_prefix

    text = "|  | C (kN) |  |\n| Type | static | dynamic |\n| 6205 | 7.8 | 14.8 |"
    doc = {"text": text, "blocks": [{"kind": "table", "start": 0, "end": len(text)}]}
    assert table_header_prefix(doc, text.index("| Type")) == "|  | C (kN) |  |\n| Type | static | dynamic |"
