from ragbench.ingest import clean_body, parse_sections

SAMPLE = """Lead para one.
Lead para two.


== History ==
Old stuff.
=== Early ===
Very old.
== See also ==
Other article
== Design ==
Design text.
"""


def test_sections_paths_and_drop():
    secs = parse_sections(SAMPLE)
    paths = [s["path"] for s in secs]
    assert paths == [[], ["History"], ["History", "Early"], ["Design"]]
    assert secs[0]["text"] == "Lead para one.\nLead para two."
    assert secs[2]["level"] == 3


def test_drop_is_language_aware():
    secs = parse_sections("Body.\n== 같이 보기 ==\n베어링\n== Einzelnachweise ==\nx\n")
    assert [s["path"] for s in secs] == [[]]


def test_clean_body_collapses_blank_runs():
    assert clean_body("a  b\n\n\n\nc d \n") == "a b\n\nc d"
