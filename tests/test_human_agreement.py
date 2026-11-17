import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
from analyze_human_agreement import parse_answers, weighted_agreement  # noqa: E402


def test_parse_answers_accepts_the_sheet_format_and_rejects_bad_lines():
    got = parse_answers("H01 | 정확성: 맞음 | 메모: 좋음\n\n# comment\nH02 | 거절: 부적절 | 메모:\nH03 | 정확성: 틀림")
    assert got["H01"] == {"kind": "correctness", "value": "맞음", "note": "좋음"}
    assert got["H02"]["kind"] == "refusal" and got["H03"]["value"] == "틀림"
    with pytest.raises(ValueError):
        parse_answers("H01 | 정확성: 애매")
    with pytest.raises(ValueError):
        parse_answers("H01 | 정확성: 맞음\nH01 | 정확성: 틀림")


def test_weighted_agreement_uses_stratum_weights():
    strata = {"correctness/맞음": {"pool": 40, "sampled": 4}, "correctness/틀림": {"pool": 4, "sampled": 4}}
    pairs = [("correctness/맞음", "맞음", "맞음")] * 4 + [("correctness/틀림", "틀림", "맞음")] * 4
    assert weighted_agreement(pairs, strata) == pytest.approx(40 / 44)
