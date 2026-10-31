"""Small text helpers shared by the detectors."""

from __future__ import annotations

import math
import re
from collections import Counter

STOPWORDS = set(
    """a about above after again against all also am an and any are as at be because been before being
    below between both but by can could did do does doing down during each few for from further had has
    have having he her here hers herself him himself his how i if in into is it its itself just let lets
    me more most my myself no nor not now of off on once only or other our ours ourselves out over own
    really same she should so some such than that thats the their theirs them themselves then there these
    they this those through to too under until up very was we were what when where which while who whom
    why will with would you your yours yourself yourselves yeah yes okay ok um uh like think maybe kind
    sort guess actually basically so well right sure thing things something get got go going gonna want
    wanna need make one two way also still even much many lot bit dont im ive youre were weve theyre
    its isnt cant wont didnt doesnt said say says saying idea ideas plan good great sounds""".split()
)

_WORD = re.compile(r"[a-z][a-z0-9'\-]+")


def content_words(text: str) -> list[str]:
    words = [w.strip("'-") for w in _WORD.findall(text.lower())]
    return [_stem(w) for w in words if len(w) > 2 and w not in STOPWORDS]


def _stem(w: str) -> str:
    if w.endswith(("us", "ss", "is", "ous")):
        return w
    if w.endswith("uses") and len(w) > 6:  # campuses -> campus
        return w[:-2]
    for suf in ("ingly", "ing", "edly", "ed", "ies", "es", "s", "ly"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def cosine(a: list[str], b: list[str]) -> float:
    ca, cb = Counter(a), Counter(b)
    common = set(ca) & set(cb)
    if not common:
        return 0.0
    dot = sum(ca[w] * cb[w] for w in common)
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    return dot / (na * nb) if na and nb else 0.0


def shared(a: list[str], b: list[str]) -> set[str]:
    return set(a) & set(b)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\s+[—–]\s+|\s--\s", text.strip())
    return [p.strip() for p in parts if p and p.strip()]


def first_name(name: str) -> str:
    return name.split()[0] if name else name
