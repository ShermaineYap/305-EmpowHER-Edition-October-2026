"""Interruption detection.

Two-stage design:

1. **Candidate detection (deterministic).** A speaker change is a candidate when the
   previous speaker was cut off mid-sentence (dash / ellipsis / no terminal punctuation)
   or when the timestamps overlap.
2. **Classification.** Not every overlap is rude. Conversation research distinguishes
   *backchannels* ("mm-hmm", "right"), *supportive / cooperative overlaps* ("yes — and the
   pilot data shows…") and true *interruptions* that take the floor away. A rule-based
   classifier handles this offline; when Gemma is available it re-labels each candidate
   with the surrounding context (see :mod:`takethefloor.gemma`).
"""

from __future__ import annotations

import re

from .parser import Turn
from .text_utils import content_words, shared

BACKCHANNELS = {
    "yeah", "yep", "yes", "right", "mm", "mhm", "mm-hmm", "uh-huh", "okay", "ok", "sure", "exactly",
    "totally", "true", "agreed", "nice", "cool", "got", "it", "gotcha", "hmm", "ah", "oh", "wow", "of",
    "course", "absolutely", "definitely", "go", "on", "sorry",
}
AGREEMENT_OPENERS = re.compile(
    r"^(yes|yeah|yep|exactly|totally|right|agreed|absolutely|definitely|and also|yes,? and|that's right|good point)\b",
    re.I,
)
CONTRAST = re.compile(
    r"\b(but|though|however|actually|no|wait|hold on|hang on|instead|let me|anyway|let's not|i wouldn'?t|i don'?t think|not really|sure, sure)\b",
    re.I,
)
CUT_OFF_END = re.compile(r"(—|–|--|-|\.\.\.|…)\s*$")
TERMINAL = re.compile(r"[.!?\"')\]]\s*$")


def _transcript_has_punctuation(turns: list[Turn]) -> bool:
    ends = sum(1 for t in turns if TERMINAL.search(t.text))
    return ends >= 0.4 * len(turns)


def _is_backchannel(text: str) -> bool:
    toks = re.findall(r"[a-z\-]+", text.lower())
    return 0 < len(toks) <= 4 and all(t in BACKCHANNELS for t in toks)


def detect(turns: list[Turn], timestamps_real: bool = True) -> list[dict]:
    punct = _transcript_has_punctuation(turns)
    events: list[dict] = []
    for i in range(len(turns) - 1):
        a, b = turns[i], turns[i + 1]
        if a.speaker == b.speaker:
            continue
        cut = bool(CUT_OFF_END.search(a.text)) or (punct and not TERMINAL.search(a.text))
        overlap = timestamps_real and (b.start < a.end - 0.3)
        if not (cut or overlap):
            continue

        resumed = i + 2 < len(turns) and turns[i + 2].speaker == a.speaker
        regained = False
        for j in range(i + 2, min(i + 6, len(turns))):
            if turns[j].speaker == a.speaker:
                if len(shared(content_words(a.text), content_words(turns[j].text))) >= 2:
                    regained = True
                break

        opener = b.text[:60]
        if _is_backchannel(b.text) and (resumed or b.words <= 2):
            label, conf, reason = "backchannel", 0.85, "Short acknowledgement; the speaker kept the floor."
        elif AGREEMENT_OPENERS.search(opener) and not CONTRAST.search(" ".join(b.text.split()[:8])):
            label, conf, reason = "supportive", 0.6, "Overlap opens with agreement and builds on the point."
        else:
            label, conf = "interruption", 0.75 if cut else 0.6
            reason = "Took the floor while the previous speaker was mid-sentence." if cut else "Started talking over the previous speaker."
            if CONTRAST.search(" ".join(b.text.split()[:8])):
                conf = min(conf + 0.15, 0.95)
                reason += " Redirected the topic."

        events.append(
            {
                "turn_idx": b.idx,
                "time": b.start,
                "interrupter": b.speaker,
                "interrupted": a.speaker,
                "cut_text": a.text[-160:],
                "taking_text": b.text[:200],
                "signal": "cut-off" if cut else "overlap",
                "label": label,
                "confidence": round(conf, 2),
                "reason": reason,
                "regained_floor": regained,
                "labeled_by": "rules",
            }
        )
    return events


def matrix(events: list[dict], speakers: list[str]) -> list[list[int]]:
    """counts[i][j] = number of times speaker i interrupted speaker j (true interruptions only)."""
    pos = {s: k for k, s in enumerate(speakers)}
    m = [[0] * len(speakers) for _ in speakers]
    for e in events:
        if e["label"] == "interruption" and e["interrupter"] in pos and e["interrupted"] in pos:
            m[pos[e["interrupter"]]][pos[e["interrupted"]]] += 1
    return m
