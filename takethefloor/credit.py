"""Idea-credit tracking.

Detects the pattern people describe as "I said it, nobody heard; he said it, everyone loved it":

* an **original** idea raised by speaker A,
* an **echo** later in the meeting — a different speaker B restating the same idea,
* the **credit** that follows the echo (praise or "B's plan") while A's original went unacknowledged.

Outcomes per idea:

``credit_drift``    – B's echo was praised/attributed to B; A's original never was.
``unattributed``    – B restated A's idea without naming A (no explicit credit either way).
``credited_build``  – B built on the idea *and named A* — the healthy pattern, shown as a positive.
"""

from __future__ import annotations

import re

from .parser import Turn
from .text_utils import content_words, cosine, first_name, shared

PROPOSAL = re.compile(
    r"\b(we could|we should|what if|how about|i propose|i suggest|i recommend|let'?s|my idea|one idea|"
    r"maybe we|why don'?t we|we might|could we|option is|plan is|we can)\b",
    re.I,
)
PRAISE = re.compile(
    r"\b(great|good|love|brilliant|smart|nice|excellent|solid|strong|clever|perfect) (idea|plan|point|call|thinking|suggestion|thought)\b|"
    r"\blove (that|this|it)\b|\blet'?s (go with|do) (that|this|it)\b|\bthat'?s (it|the one|smart|brilliant|great)\b|"
    r"\bi'?m sold\b|\bagreed\b|\bwell said\b",
    re.I,
)


def _named(text: str, name: str) -> bool:
    fn = re.escape(first_name(name))
    return bool(re.search(rf"\b{fn}\b", text, re.I))


def _attributed_to(text: str, name: str) -> bool:
    fn = re.escape(first_name(name))
    pats = [
        rf"\b{fn}'?s (idea|plan|point|proposal|suggestion|approach|pricing|framework|model)\b",
        rf"\b(as|like|what) {fn} (said|suggested|mentioned|proposed)\b",
        rf"\b(thanks|thank you|nice one|great idea|good call|love that|well said|good point|great point),? {fn}\b",
        rf"\b{fn},? (that'?s|this is) (great|brilliant|smart|exactly|it)\b",
        rf"\b{fn} (is right|nailed it|has a point|gets it)\b",
        rf"\bgo with {fn}\b",
    ]
    return any(re.search(p, text, re.I) for p in pats)


def _credited_after(turns: list[Turn], k: int, who: str, window: int = 4) -> tuple[bool, str]:
    """Was the idea in turns[k] credited to ``who`` in the next few turns?"""
    for j in range(k + 1, min(k + 1 + window, len(turns))):
        t = turns[j]
        if t.speaker == who:
            continue
        if _attributed_to(t.text, who):
            return True, f"[{t.stamp}] {t.speaker}: {t.text[:160]}"
        if j <= k + 2 and PRAISE.search(t.text):
            return True, f"[{t.stamp}] {t.speaker}: {t.text[:160]}"
    return False, ""


BUILD_ON = re.compile(r"\b(building on|adding to|following up on|to build on|piggybacking on|going back to|plus one to|\+1 to)\b", re.I)
ADOPTION = re.compile(r"^\s*(let'?s go with|let'?s do|agreed|sounds good|okay,? so|so the plan|fine,)", re.I)


def _explicit_builds(turns: list[Turn], cw: list[list[str]]) -> dict[int, tuple[float, int]]:
    """Echo turns that openly credit another participant ("Building on Grace's audit...")."""
    found: dict[int, tuple[float, int]] = {}
    speakers = {t.speaker for t in turns}
    for j, b in enumerate(turns):
        if not BUILD_ON.search(b.text):
            continue
        for name in speakers - {b.speaker}:
            if not _named(b.text, name):
                continue
            prior = [i for i in range(j) if turns[i].speaker == name and len(cw[i]) >= 3]
            if not prior:
                continue
            i = max(prior, key=lambda k: (cosine(cw[k], cw[j]), -k))
            found[i] = (max(cosine(cw[i], cw[j]), 0.01), j)
    return found


def detect(turns: list[Turn], min_gap: float = 20.0, sim_threshold: float = 0.28, min_shared: int = 3) -> list[dict]:
    cw = [content_words(t.text) for t in turns]
    originals = [i for i, t in enumerate(turns) if (PROPOSAL.search(t.text) and len(cw[i]) >= 4) or len(cw[i]) >= 10]

    best_echo: dict[int, tuple[float, int]] = {}
    for j, b in enumerate(turns):
        if len(cw[j]) < 4:
            continue
        cands = []
        for i in originals:
            if i >= j:
                break
            a = turns[i]
            if b.start - a.start < min_gap:
                continue
            sim = cosine(cw[i], cw[j])
            if sim >= sim_threshold and len(shared(cw[i], cw[j])) >= min_shared:
                cands.append((i, sim))
        if not cands:
            continue
        origin_i = min(cands, key=lambda c: c[0])[0]  # earliest similar statement = the origin
        if turns[origin_i].speaker == b.speaker:
            continue
        sim = dict(cands)[origin_i]
        if origin_i not in best_echo or sim > best_echo[origin_i][0]:
            best_echo[origin_i] = (sim, j)

    for i, v in _explicit_builds(turns, cw).items():
        best_echo.setdefault(i, v)

    events: list[dict] = []
    for i, (sim, j) in sorted(best_echo.items()):
        a, b = turns[i], turns[j]
        orig_credit, _ = _credited_after(turns, i, a.speaker)
        echo_credit, evidence = _credited_after(turns, j, b.speaker)
        # explicit attribution anywhere later, e.g. "let's go with Mark's pricing plan"
        if not echo_credit:
            for t in turns[j + 1 :]:
                if t.speaker != b.speaker and _attributed_to(t.text, b.speaker) and len(shared(cw[i], content_words(t.text))) >= 1:
                    echo_credit, evidence = True, f"[{t.stamp}] {t.speaker}: {t.text[:160]}"
                    break
        names_origin = _named(b.text, a.speaker)

        if names_origin:
            outcome = "credited_build"
        elif echo_credit and not orig_credit:
            outcome = "credit_drift"
        elif not orig_credit and sim >= 0.45 and not ADOPTION.search(b.text):
            outcome = "unattributed"
        else:
            continue  # original was acknowledged; restating is just agreement

        overlap = sorted(shared(cw[i], cw[j]))
        events.append(
            {
                "outcome": outcome,
                "originator": a.speaker,
                "original_time": a.start,
                "original_text": a.text,
                "echoed_by": b.speaker,
                "echo_time": b.start,
                "echo_text": b.text,
                "credited_to": b.speaker if echo_credit and not names_origin else (a.speaker if names_origin else None),
                "credit_evidence": evidence,
                "similarity": round(sim, 2),
                "shared_terms": overlap[:8],
                "summary": None,
                "detected_by": "rules",
            }
        )
    order = {"credit_drift": 0, "unattributed": 1, "credited_build": 2}
    return sorted(events, key=lambda e: (order[e["outcome"]], e["original_time"]))
