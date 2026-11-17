import json
from collections import Counter

from ragbench.humangold import ITEMS_PATH, _label, assign_split, binary, build, dedupe, load_items


def test_label_mapping():
    assert _label({"correctness": "부분"}) == {"kind": "correctness", "value": "부분"}
    assert _label({"refusal": "적절", "note": "x"}) == {"kind": "refusal", "value": "적절"}
    assert _label({"correctness": "거절"}) == {"kind": "refusal", "value": None}
    assert _label({"evidence": "충분"}) is None
    assert binary("맞음") is True and binary("부분") is False and binary(None) is None


def test_dedupe_keeps_first_and_split_is_balanced_and_reproducible():
    items = [{"source": "kb1" if i % 2 else "r2", "question": f"q{i % 7}", "answer": "a",
              "label": {"kind": "correctness", "value": ["맞음", "부분", "틀림"][i % 3]}} for i in range(14)]
    d = dedupe(items)
    assert len(d) == 7 and d[0]["source"] == "r2"
    a = assign_split([dict(x) for x in d], seed=1)
    b = assign_split([dict(x) for x in d], seed=1)
    assert [x["split"] for x in a] == [x["split"] for x in b]
    c = Counter(x["split"] for x in a)
    assert abs(c["dev"] - c["test"]) <= 1


def test_committed_gold_file_matches_the_sources():
    # 저장된 items.jsonl은 원본 채점 파일에서 다시 만든 것과 같아야 한다 (원본만 고치고 다시 만들지 않으면 실패)
    rebuilt = build()
    stored = load_items(adjudicated=None)
    assert [json.dumps(x, ensure_ascii=False, sort_keys=True) for x in rebuilt] == \
           [json.dumps(x, ensure_ascii=False, sort_keys=True) for x in stored]
    assert len({x["id"] for x in stored}) == len(stored) and ITEMS_PATH.exists()


def test_adjudicated_labels_override(tmp_path):
    adj = tmp_path / "adj.json"
    first = load_items(adjudicated=None)[0]
    adj.write_text(json.dumps({"labels": {first["id"]: "틀림"}}), encoding="utf-8")
    it = load_items(adjudicated=adj)[0]
    assert it["label"]["value"] == "틀림" and it["label"]["adjudicated"] is True
