"""Orchestrates the full analysis of one meeting."""

from __future__ import annotations

import statistics
from concurrent.futures import ThreadPoolExecutor

from . import credit, fallbacks, gemma, hedges, interruptions, metrics
from .parser import Turn


def analyze(turns: list[Turn], client: gemma.GemmaClient | None = None, timestamps_real: bool = True) -> dict:
    client = client or gemma.GemmaClient(backend="offline")
    stats = metrics.speaker_stats(turns)
    speakers = sorted(stats, key=lambda s: -stats[s]["talk_share"])

    events = interruptions.detect(turns, timestamps_real=timestamps_real)
    hedge_hits = hedges.find_hedges(turns)
    h_index = hedges.hedge_index(hedge_hits, {s: v["words"] for s, v in stats.items()})
    credit_events = credit.detect(turns)

    recap_data = None
    if client.enabled:
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_int = pool.submit(gemma.label_interruptions, client, events, turns)
            f_recap = pool.submit(gemma.recap, client, turns, credit_events)
            events = f_int.result()
            recap_data = f_recap.result()
    recap_source = "gemma" if recap_data else "rules"
    recap_data = recap_data or fallbacks.recap(turns, credit_events)
    titles = recap_data.get("idea_titles") or {}
    for n, e in enumerate(credit_events, 1):
        e["summary"] = titles.get(str(n)) or " ".join(e["shared_terms"][:4]).title()

    for s in stats.values():
        name = s["speaker"]
        s["hedge_index"] = h_index.get(name, 0.0)
        s["interrupted_by_others"] = sum(1 for e in events if e["label"] == "interruption" and e["interrupted"] == name)
        s["interrupted_others"] = sum(1 for e in events if e["label"] == "interruption" and e["interrupter"] == name)
        s["ideas_credited_away"] = sum(1 for c in credit_events if c["outcome"] == "credit_drift" and c["originator"] == name)
        s["ideas_echoed_unnamed"] = sum(1 for c in credit_events if c["outcome"] in ("credit_drift", "unattributed") and c["echoed_by"] == name)

    equity = metrics.equity_index(stats)
    n_int = sum(1 for e in events if e["label"] == "interruption")
    n_drift = sum(1 for c in credit_events if c["outcome"] == "credit_drift")
    n_build = sum(1 for c in credit_events if c["outcome"] == "credited_build")
    health = max(0.0, min(100.0, 0.6 * equity + 40 - 7 * n_int - 12 * n_drift + 3 * n_build))
    duration = max((t.end for t in turns), default=0) - min((t.start for t in turns), default=0)
    return {
        "turns": turns,
        "speakers": speakers,
        "stats": stats,
        "equity_index": equity,
        "floor_health": round(health),
        "counts": {"interruptions": n_int, "credit_drift": n_drift, "credited_build": n_build},
        "duration": duration,
        "interruptions": events,
        "interruption_matrix": interruptions.matrix(events, speakers),
        "hedge_hits": hedge_hits,
        "credit_events": credit_events,
        "recap": recap_data,
        "recap_source": recap_source,
        "facilitator_tips": fallbacks.facilitator_tips(stats, events, credit_events, equity),
        "engine": client.label,
        "engine_error": client.last_error,
    }


def coach_evidence(result: dict, name: str) -> dict:
    s = result["stats"][name]
    hedge_vals = [v["hedge_index"] for v in result["stats"].values()]
    mine = [h for h in result["hedge_hits"] if h["speaker"] == name]
    return {
        "name": name,
        "share": s["talk_share"],
        "fair": s["fair_share"],
        "turns": s["turns"],
        "avg_words": s["avg_turn_words"],
        "hedge": s["hedge_index"],
        "hedge_median": statistics.median(hedge_vals) if hedge_vals else 0.0,
        "interrupted": s["interrupted_by_others"],
        "interrupter": s["interrupted_others"],
        "drifted": s["ideas_credited_away"],
        "echoed": s["ideas_echoed_unnamed"],
        "hedged_sentences": [h["sentence"] for h in mine],
        "rule_rewrites": [(h["sentence"], h["rewrite"]) for h in mine if h["rewrite"] != h["sentence"]],
    }


def coach(result: dict, name: str, client: gemma.GemmaClient | None = None) -> tuple[dict, str]:
    ev = coach_evidence(result, name)
    base = fallbacks.coach(ev)
    if client and client.enabled:
        g = gemma.coach(client, ev)
        if g:
            merged = {**base, **{k: v for k, v in g.items() if v}}
            return merged, "gemma"
    return base, "rules"
