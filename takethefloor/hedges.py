"""Hedge Index — language that quietly gives away authority.

Hedges are not "wrong" (they can signal openness), but habitual minimisers, pre-apologies
and self-discounting make strong ideas sound optional. The index is hedges per 100 words,
and every hit is shown in context so people can judge for themselves.
"""

from __future__ import annotations

import re

from .parser import Turn
from .text_utils import split_sentences

# (category, pattern, explanation)
HEDGE_PATTERNS: list[tuple[str, str, str]] = [
    ("self-discount", r"\bthis (?:might|may|could) be (?:a )?(?:dumb|stupid|silly|crazy|bad)\b[^.?!]*", "Discounts the idea before anyone hears it."),
    ("self-discount", r"\b(?:i'?m|i am) (?:not sure|no expert)(?: (?:if|but|whether))?", "Signals low confidence up front."),
    ("self-discount", r"\bi could be wrong\b", "Invites people to dismiss the point."),
    ("self-discount", r"\b(?:feel free to ignore|ignore me if|you can ignore)\b[^.?!]*", "Gives permission to skip your idea."),
    ("apology", r"\b(?:sorry|i'?m sorry)\b(?:,? (?:but|to|if))?", "Apologising for taking up space."),
    ("minimiser", r"\b(?:just|only) (?:wanted|want|wondering|thinking|a thought|a quick|quickly|a small)\b", "Shrinks the contribution."),
    ("minimiser", r"\b(?:a little bit|a tiny|a small) (?:idea|thought|suggestion|point)\b", "Shrinks the contribution."),
    ("qualifier", r"\bi (?:think|feel) (?:like )?maybe\b", "Double hedge: 'I think' + 'maybe'."),
    ("qualifier", r"\b(?:kind of|sort of|kinda|sorta)\b", "Blurs a clear claim."),
    ("qualifier", r"\bi guess\b", "Sounds unsure about your own view."),
    ("qualifier", r"\bmaybe we could (?:possibly )?\b", "Turns a proposal into a maybe."),
    ("qualifier", r"\bif that'?s (?:okay|ok|alright)\b", "Asks permission for a normal contribution."),
    ("tag-question", r"(?:does that make sense|if that makes sense|you know what i mean|is that okay|right)\s*\?", "Seeks validation instead of a decision."),
]
_COMPILED = [(c, re.compile(p, re.I), why) for c, p, why in HEDGE_PATTERNS]

_STRIP = [
    (re.compile(r"^(?:(?:um+|uh+|so+|okay|ok|well|hmm),?\s+)+", re.I), ""),
    (re.compile(r"\b(?:sorry|i'?m sorry),?\s*(?:but|to|if)?\s*", re.I), ""),
    (re.compile(r"\bthis (?:might|may|could) be (?:a )?(?:dumb|stupid|silly|crazy|bad) (?:idea|question|thought)?,?\s*(?:but)?,?\s*", re.I), ""),
    (re.compile(r"\b(?:i'?m|i am) not sure (?:if|but|whether)?,?\s*", re.I), ""),
    (re.compile(r"\bi could be wrong,?\s*(?:but)?\s*", re.I), ""),
    (re.compile(r"\b(?:just|only) (?=wanted|want|wondering|thinking)", re.I), ""),
    (re.compile(r"\bi (?:think|feel) (?:like )?maybe we (?:could|can|should|might)\b", re.I), "I recommend we"),
    (re.compile(r"\bi (?:think|feel) (?:like )?maybe\b", re.I), "I recommend"),
    (re.compile(r"^maybe we (?:could|can|should|might) (?:possibly )?", re.I), "We should "),
    (re.compile(r"\bmaybe we (?:could|can|should|might) (?:possibly )?", re.I), "we should "),
    (re.compile(r"\b(?:kind of|sort of|kinda|sorta)\s+", re.I), ""),
    (re.compile(r"\bi guess\s*", re.I), ""),
    (re.compile(r",?\s*(?:does that make sense|if that makes sense|you know what i mean|is that okay|if that'?s (?:okay|ok|alright))\s*\??\s*$", re.I), "."),
    (re.compile(r"\b(?:feel free to ignore|ignore me if)[^.?!]*[.?!]?", re.I), ""),
]


def find_hedges(turns: list[Turn]) -> list[dict]:
    hits: list[dict] = []
    for t in turns:
        for sent in split_sentences(t.text):
            cats: list[tuple[str, str, str]] = []
            for cat, rx, why in _COMPILED:
                m = rx.search(sent)
                if m:
                    cats.append((cat, m.group(0), why))
            if cats:
                hits.append(
                    {
                        "speaker": t.speaker,
                        "time": t.start,
                        "turn_idx": t.idx,
                        "sentence": sent,
                        "hedges": [{"category": c, "phrase": p, "why": w} for c, p, w in cats],
                        "rewrite": assertive_rewrite(sent),
                        "rewritten_by": "rules",
                    }
                )
    return hits


def assertive_rewrite(sentence: str) -> str:
    out = sentence
    for rx, rep in _STRIP:
        out = rx.sub(rep, out)
    out = re.sub(r"\s{2,}", " ", out).strip(" ,")
    out = re.sub(r"\.\s*\.", ".", out)
    out = re.sub(r"\s+([.,?!])", r"\1", out)
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    if re.match(r"^(i recommend|we should)\b", out, re.I):
        out = re.sub(r"\?\s*$", ".", out)
    if out and out[-1] not in ".!?":
        out += "."
    if len(out.split()) < 3 or re.fullmatch(r"(?:that'?s )?(?:okay|ok|alright)\.?", out, re.I):
        return "(Cut this sentence. Let the idea stand on its own.)"
    return out


def hedge_index(hits: list[dict], words_by_speaker: dict[str, int]) -> dict[str, float]:
    counts: dict[str, int] = {}
    for h in hits:
        counts[h["speaker"]] = counts.get(h["speaker"], 0) + len(h["hedges"])
    return {s: round(100 * counts.get(s, 0) / max(w, 1), 2) for s, w in words_by_speaker.items()}
