"""Airtime metrics: who actually held the floor."""

from __future__ import annotations

from .parser import Turn


def speaker_stats(turns: list[Turn]) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for t in turns:
        s = stats.setdefault(
            t.speaker,
            {"speaker": t.speaker, "talk_seconds": 0.0, "words": 0, "turns": 0, "first_spoke": t.start},
        )
        s["talk_seconds"] += t.duration
        s["words"] += t.words
        s["turns"] += 1
    total_secs = sum(s["talk_seconds"] for s in stats.values()) or 1.0
    total_words = sum(s["words"] for s in stats.values()) or 1
    n = len(stats) or 1
    for s in stats.values():
        s["talk_share"] = s["talk_seconds"] / total_secs
        s["word_share"] = s["words"] / total_words
        s["avg_turn_words"] = s["words"] / s["turns"]
        s["fair_share"] = 1 / n
        s["share_vs_fair"] = s["talk_share"] / (1 / n)
    return stats


def equity_index(stats: dict[str, dict]) -> float:
    """1 − Gini coefficient of talk share, scaled 0–100 (100 = perfectly even airtime)."""
    shares = sorted(s["talk_share"] for s in stats.values())
    n = len(shares)
    if n < 2:
        return 100.0
    cum = sum((i + 1) * x for i, x in enumerate(shares))
    gini = (2 * cum) / (n * sum(shares)) - (n + 1) / n
    gini_max = (n - 1) / n
    return round(100 * (1 - gini / gini_max), 1)


def timeline(turns: list[Turn]) -> list[dict]:
    return [
        {"speaker": t.speaker, "start": t.start, "end": max(t.end, t.start + 0.5), "text": t.text, "idx": t.idx}
        for t in turns
    ]
