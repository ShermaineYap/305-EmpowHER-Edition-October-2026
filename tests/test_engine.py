"""Tests: parser formats + detectors scored against the hand-labelled synthetic meetings."""

import json
from pathlib import Path

import pytest

from takethefloor import analyze, parse_transcript
from takethefloor.gemma import extract_json
from takethefloor.hedges import assertive_rewrite

DATA = Path(__file__).resolve().parents[1] / "data"
LABELS = json.loads((DATA / "demo_labels.json").read_text())


def _run(name):
    text = (DATA / name).read_text()
    return analyze(parse_transcript(text), timestamps_real="standup" not in name)


@pytest.mark.parametrize(
    "text,speakers",
    [
        ("[00:00:05] Aisha: Hello there.\n[00:00:09] Mark: Hi.", ["Aisha", "Mark"]),
        ("00:05 Aisha: Hello there.\n00:09 Mark: Hi.", ["Aisha", "Mark"]),
        ("Aisha (00:00:05): Hello there.\nMark (00:00:09): Hi.", ["Aisha", "Mark"]),
        ("Aisha  0:05\nHello there.\nMark  0:09\nHi.", ["Aisha", "Mark"]),
        ("Aisha: Hello there.\nMark: Hi.", ["Aisha", "Mark"]),
        ("WEBVTT\n\n1\n00:00:05.000 --> 00:00:08.000\n<v Aisha>Hello there.</v>\n\n2\n00:00:09.000 --> 00:00:10.000\nMark: Hi.\n", ["Aisha", "Mark"]),
    ],
)
def test_parser_formats(text, speakers):
    turns = parse_transcript(text)
    assert [t.speaker for t in turns] == speakers
    assert turns[0].text.startswith("Hello")
    assert turns[1].start > turns[0].start


def test_parser_merges_consecutive_same_speaker():
    turns = parse_transcript("[00:00:01] A: one.\n[00:00:02] A: two.\n[00:00:05] B: three.")
    assert len(turns) == 2 and turns[0].text == "one. two."


def test_parser_rejects_garbage():
    with pytest.raises(ValueError):
        parse_transcript("no speakers here at all")


@pytest.mark.parametrize("name", list(LABELS))
def test_interruptions_match_labels(name):
    r = _run(name)
    got = sorted((e["interrupter"], e["interrupted"]) for e in r["interruptions"] if e["label"] == "interruption")
    want = sorted((x["interrupter"], x["interrupted"]) for x in LABELS[name]["interruptions"])
    assert got == want


@pytest.mark.parametrize("name", list(LABELS))
def test_credit_matches_labels(name):
    r = _run(name)
    got = sorted((c["outcome"], c["originator"], c["echoed_by"]) for c in r["credit_events"])
    want = sorted((x["outcome"], x["originator"], x["echoed_by"]) for x in LABELS[name]["credit"])
    assert got == want


def test_backchannel_and_supportive_not_counted():
    r = _run("demo_product_launch.vtt")
    labels = {(e["interrupter"], e["label"]) for e in r["interruptions"]}
    assert ("Daniel", "backchannel") in labels
    assert ("Aisha", "supportive") in labels


def test_healthy_meeting_scores_higher():
    scores = {n: _run(n)["floor_health"] for n in LABELS}
    assert scores["demo_balanced_standup.txt"] > scores["demo_study_group.txt"] > scores["demo_product_launch.vtt"]


def test_hedge_rewrite():
    out = assertive_rewrite("Um, so, this might be a dumb idea, but I think maybe we could sort of shorten the onboarding to three screens?")
    assert out == "I recommend we shorten the onboarding to three screens."


def test_extract_json_handles_fences_and_chatter():
    assert extract_json('Sure! ```json\n{"a": [1, 2,]}\n``` hope that helps') == {"a": [1, 2]}
    assert extract_json('Here: [{"id": 1, "label": "x"}] done') == [{"id": 1, "label": "x"}]
    assert extract_json("no json") is None


class FakeGemma:
    """Stands in for the Gemini API so the Gemma merge path is tested without a key."""

    enabled = True
    label = "Gemma · fake"
    last_error = None

    def generate_json(self, prompt):
        if "Classify each moment" in prompt:
            n = prompt.count("\n#")+ (1 if prompt.lstrip().startswith("#") else 0)
            return [{"id": k, "label": "interruption", "reason": "fake"} for k in range(1, 30)]
        if "accessible meeting recaps" in prompt:
            return {"summary": ["Plain summary."], "decisions": ["D"], "action_items": [{"owner": "Mei Ling", "task": "Model pricing", "due": "Friday"}], "open_questions": [], "idea_titles": {"1": "Half-price student tier"}}
        if "leadership coach" in prompt:
            return {"headline": "H", "strengths": ["s"], "moves": ["m"], "scripts": ["x"], "rewrites": []}
        return None


def test_gemma_results_are_merged():
    from takethefloor.analysis import coach

    r = analyze(parse_transcript((DATA / "demo_product_launch.vtt").read_text()), client=FakeGemma())
    assert r["recap_source"] == "gemma" and r["recap"]["summary"] == ["Plain summary."]
    assert r["credit_events"][0]["summary"] == "Half-price student tier"
    assert all(e["labeled_by"] == "gemma" for e in r["interruptions"])
    c, src = coach(r, "Aisha", FakeGemma())
    assert src == "gemma" and c["moves"] == ["m"] and c["strengths"] == ["s"]


def test_rule_idea_title():
    from takethefloor.credit import idea_title

    assert idea_title("What if we launch a student tier at half the price of the pro plan, verified") == "Launch a student tier at half the price"
