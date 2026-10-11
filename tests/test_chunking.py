from ragbench.chunking import Span, chunk_document, pack, split_sentences
from ragbench.config import ChunkingConfig
from ragbench.evalset import locate_anchor, map_gold_to_chunks


def wc(text: str) -> int:          # cheap "tokenizer": whitespace words
    return len(text.split())


def hard_cut_words(text: str, limit: int):
    w = text.split()
    return [" ".join(w[i:i + limit]) for i in range(0, len(w), limit)]


DOC = {
    "doc_id": "d1", "lang": "en",
    "text": "One two three. Four five six.\nSeven eight nine ten. Eleven twelve.",
    "sections": [{"path": [], "level": 1, "text": "One two three. Four five six.\nSeven eight nine ten. Eleven twelve."}],
}


def test_split_sentences_offsets_are_exact():
    spans = split_sentences(DOC["text"], wc, hard_cut_words, 100)
    assert [s.text for s in spans] == ["One two three.", "Four five six.", "Seven eight nine ten.", "Eleven twelve."]
    for s in spans:
        assert DOC["text"][s.start:s.end] == s.text


def test_pack_respects_size_and_sentence_overlap():
    spans = split_sentences(DOC["text"], wc, hard_cut_words, 100)   # 3,3,4,2 tokens
    chunks = pack(spans, size=7, overlap=3)
    texts = [[s.text for s in c] for c in chunks]
    # chunk0: 3+3=6; "Seven..."(4) overflows -> new chunk seeded with "Four five six."(3 <= overlap 3)
    assert texts[0] == ["One two three.", "Four five six."]
    assert texts[1] == ["Four five six.", "Seven eight nine ten."]
    # "Eleven twelve."(2) overflows 7+2; tail "Seven..."(4) > overlap 3 -> no overlap this time
    assert texts[2] == ["Eleven twelve."]
    assert all(sum(s.n_tokens for s in c) <= 7 for c in chunks)


def test_overlap_never_pushes_chunk_over_size():
    spans = split_sentences(DOC["text"], wc, hard_cut_words, 100)   # 3,3,4,2
    chunks = pack(spans, size=6, overlap=3)
    # after chunk0 (6 tokens) the incoming sentence has 4 tokens -> overlap budget shrinks to 2,
    # so the 3-token tail is NOT carried over
    assert [s.text for s in chunks[1]] == ["Seven eight nine ten.", "Eleven twelve."]
    assert all(sum(s.n_tokens for s in c) <= 6 for c in chunks)


def test_oversized_sentence_is_hard_cut():
    spans = split_sentences("a b c d e f g.", wc, hard_cut_words, 3)
    assert [s.text for s in spans] == ["a b c", "d e f", "g."]


def test_chunk_document_text_slices_match_offsets():
    cfg = ChunkingConfig(unit="char", size=6, overlap=3)
    chunks = chunk_document(DOC, cfg, wc, hard_cut_words)
    for c in chunks:
        assert DOC["text"][c["char_start"]:c["char_end"]] == c["text"]
        assert c["chunk_id"] == f"d1#{c['idx']}"


def test_anchor_mapping_with_overlap_rule():
    cfg = ChunkingConfig(unit="char", size=5, overlap=0)
    chunks = chunk_document(DOC, cfg, wc, hard_cut_words)
    # sizes 3,3,4,2 with budget 5 -> one sentence per chunk
    assert [c["text"] for c in chunks] == ["One two three.", "Four five six.", "Seven eight nine ten.", "Eleven twelve."]
    gold = [{"doc_id": "d1", "anchor": "Seven eight nine ten.", "grade": 2},
            {"doc_id": "d1", "anchor": "Eleven  twelve.", "grade": 1}]   # double space -> fuzzy match
    rel = map_gold_to_chunks(gold, {"d1": DOC}, chunks, min_overlap=0.5)
    assert rel == {"d1#2": 2, "d1#3": 1}


def test_anchor_spanning_two_chunks_uses_min_overlap():
    cfg = ChunkingConfig(unit="char", size=5, overlap=0)
    chunks = chunk_document(DOC, cfg, wc, hard_cut_words)
    anchor = "Four five six.\nSeven eight"       # 14 chars in chunk 1, 11 chars in chunk 2 (of 26)
    gold = [{"doc_id": "d1", "anchor": anchor, "grade": 2}]
    assert map_gold_to_chunks(gold, {"d1": DOC}, chunks, min_overlap=0.5) == {"d1#1": 2}
    assert map_gold_to_chunks(gold, {"d1": DOC}, chunks, min_overlap=0.4) == {"d1#1": 2, "d1#2": 2}


def test_locate_anchor_missing_raises():
    import pytest
    with pytest.raises(ValueError):
        locate_anchor("abc", "zzz")
