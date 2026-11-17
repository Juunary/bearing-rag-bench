from ragbench.cache import LLMCache
from ragbench.claimcheck import ClaimChecker, apply_policy, parse_support, split_claims, statement_text

PASSAGES = [{"chunk_id": "en_grease#2", "text": "Grease is a semisolid lubricant."},
            {"chunk_id": "kb_relubrication#0", "text": "재급지 주기는 운전 온도에 따라 줄인다."}]


class FakeChecker:
    """Says SUPPORTED unless the statement contains a word from `bad`; records the prompts it saw."""
    model_name, revision = "fake", "rev1"

    def __init__(self, bad=("needle",)):
        self.bad, self.calls, self.prompts = bad, 0, []

    def generate(self, messages, max_new_tokens=8):
        self.calls += 1
        self.prompts.append(messages[-1]["content"])
        statement = messages[-1]["content"].split("Statement:")[1]
        text = "NOT_SUPPORTED" if any(b in statement for b in self.bad) else "SUPPORTED"
        return {"text": text, "prompt_tokens": 50, "completion_tokens": 2, "seconds": 0.1}


def test_split_attaches_citation_only_fragments_and_skips_refusals():
    claims = split_claims("Grease is semisolid. [en_grease#2] It needs needle rollers [en_grease#2].")
    assert [c.cited for c in claims] == [["en_grease#2"], ["en_grease#2"]]
    assert statement_text(claims[0]) == "Grease is semisolid."
    assert split_claims("NO_ANSWER") == [] and split_claims("") == []


def test_split_keeps_a_citation_used_as_subject_and_drops_a_cut_citation():
    claims = split_claims("아니요. [kb_relubrication#0]에 따르면 주기를 줄입니다. 따라서 줄입니다. [kb_relub")
    assert [c.cited for c in claims] == [[], ["kb_relubrication#0"], []]
    assert statement_text(claims[2]) == "따라서 줄입니다."


def test_parse_support():
    assert parse_support("SUPPORTED") is True
    assert parse_support("not_supported.") is False and parse_support("Unsupported") is False
    assert parse_support("maybe") is None


def test_check_rules_cache_and_only_cited_passages(tmp_path):
    gen = FakeChecker()
    cc = ClaimChecker(gen, LLMCache(tmp_path / "c.sqlite"))
    ans = "Grease is semisolid [en_grease#2]. Use needle rollers [en_grease#2]. It is old. Also [en_other#1] says so."
    rep = cc.check(ans, PASSAGES)
    assert [c.supported for c in rep.claims] == [True, False, True, False]
    assert [c.reason for c in rep.claims] == ["model", "model", "inherited", "unknown_citation"]
    assert rep.model_calls == 3 and rep.unsupported == [1, 3] and rep.support_ratio == 0.5
    # 인용 없는 문장도 답변이 인용한 청크만 보고, 인용하지 않은 컨텍스트(재급지)는 보지 않는다
    assert all("재급지" not in p for p in gen.prompts)
    cc.check(ans, PASSAGES)
    assert gen.calls == 3                                   # 두 번째 검사는 캐시
    strict = ClaimChecker(FakeChecker(), None, strict=True).check(ans, PASSAGES)
    assert [c.reason for c in strict.claims][2] == "no_citation" and strict.model_calls == 2


def test_policies():
    cc = ClaimChecker(FakeChecker(), None)
    ans = "Grease is semisolid [en_grease#2]. Use needle rollers [en_grease#2]."
    rep = cc.check(ans, PASSAGES)
    assert apply_policy(ans, rep, "off").text == ans and apply_policy(ans, rep, "off").flagged == []
    assert apply_policy(ans, rep, "flag").flagged == [1] and not apply_policy(ans, rep, "flag").blocked
    s = apply_policy(ans, rep, "strip")
    assert s.text == "Grease is semisolid [en_grease#2]." and not s.blocked
    assert apply_policy(ans, rep, "block", min_support=1.0).blocked
    assert not apply_policy(ans, rep, "block", min_support=0.5).blocked
    bad = "Use needle rollers [en_grease#2]."
    assert apply_policy(bad, cc.check(bad, PASSAGES), "strip").blocked
