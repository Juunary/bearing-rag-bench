from ragbench.tokenize import kiwi_tokenize, subword_tokenize, whitespace_tokenize


def test_whitespace_keeps_korean_particles_attached():
    toks = whitespace_tokenize("베어링은 베어링을 지지한다. Rolling-element Bearing!")
    assert toks == ["베어링은", "베어링을", "지지한다", "rolling", "element", "bearing"]


def test_kiwi_strips_particles_and_endings():
    toks = kiwi_tokenize("볼 베어링은 회전 마찰력을 줄이고 반경 및 축 하중을 지지한다.")
    assert "베어링" in toks and "베어링은" not in toks
    assert "은" not in toks and "을" not in toks and "." not in toks
    assert "줄이" in toks            # verb root kept


def test_kiwi_handles_latin_text_as_words():
    toks = kiwi_tokenize("Rolling-element bearings carry a load.")
    assert toks == ["rolling", "element", "bearings", "carry", "a", "load"]


def test_subword_splits_german_compound():
    toks = subword_tokenize("Kegelrollenlager")
    assert len(toks) >= 2 and "".join(toks) == "kegelrollenlager"


# ---- 영어 어간 추출 (영어 피벗 BM25 전용) ----
def test_en_stem_merges_inflections():
    from ragbench.tokenize import en_stem_tokenize

    toks = en_stem_tokenize("Bearings lubricated by lubrication")
    assert toks[0] == en_stem_tokenize("bearing")[0]                      # bearings == bearing
    assert toks[1] == toks[2] or toks[1].startswith("lubric")            # lubricated / lubrication는 같은 어간 계열


def test_en_stem_stop_drops_stopwords_before_stemming():
    from ragbench.tokenize import en_stem_stop_tokenize

    assert en_stem_stop_tokenize("the bearings of the wheel") == en_stem_stop_tokenize("bearings wheel")
    assert "the" not in en_stem_stop_tokenize("the load")
