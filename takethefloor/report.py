"""Plain-text / Markdown exports (accessible: no colour, headings + lists only)."""

from __future__ import annotations

from .parser import fmt_time

OUTCOME_TEXT = {
    "credit_drift": "Credited to the wrong person",
    "unattributed": "Repeated without naming the originator",
    "credited_build": "Built on with credit (healthy)",
}


def markdown_report(r: dict, title: str = "Meeting") -> str:
    out = [f"# TakeTheFloor report: {title}", ""]
    out += [
        f"- Floor Health score: **{r['floor_health']}/100**",
        f"- Airtime balance (1 − Gini): **{r['equity_index']}/100**",
        f"- Interruptions: **{r['counts']['interruptions']}** · Ideas credited to the wrong person: **{r['counts']['credit_drift']}**",
        f"- Analysis engine: {r['engine']}",
        "",
        "## Who held the floor",
        "",
        "| Person | Share of talk time | Turns | Interrupted by others | Interrupted others | Hedges per 100 words |",
        "|---|---|---|---|---|---|",
    ]
    for s in r["speakers"]:
        v = r["stats"][s]
        out.append(f"| {s} | {v['talk_share']:.0%} | {v['turns']} | {v['interrupted_by_others']} | {v['interrupted_others']} | {v['hedge_index']:.1f} |")
    out += ["", "## Idea credit", ""]
    if not r["credit_events"]:
        out.append("No repeated ideas detected.")
    for c in r["credit_events"]:
        out.append(
            f"- **{OUTCOME_TEXT[c['outcome']]}** — {c['summary']}: first raised by {c['originator']} at {fmt_time(c['original_time'])}, "
            f"repeated by {c['echoed_by']} at {fmt_time(c['echo_time'])}."
            + (f" Credit went to {c['credited_to']}." if c["credited_to"] else "")
        )
    out += ["", "## Interruptions", ""]
    real = [e for e in r["interruptions"] if e["label"] == "interruption"]
    if not real:
        out.append("No interruptions detected.")
    for e in real:
        out.append(f"- {fmt_time(e['time'])}: {e['interrupter']} took the floor from {e['interrupted']}. {e['reason']}")
    rc = r["recap"]
    out += ["", "## Plain-language recap", ""] + [f"- {x}" for x in rc.get("summary", [])]
    if rc.get("decisions"):
        out += ["", "### Decisions", ""] + [f"- {x}" for x in rc["decisions"]]
    if rc.get("action_items"):
        out += ["", "### Action items", ""]
        for a in rc["action_items"]:
            out.append(f"- {a.get('owner') or 'Unassigned'}: {a.get('task', '')}" + (f" (due {a['due']})" if a.get("due") else ""))
    if rc.get("open_questions"):
        out += ["", "### Open questions", ""] + [f"- {x}" for x in rc["open_questions"]]
    out += ["", "## Facilitator tips", ""] + [f"- {t}" for t in r["facilitator_tips"]]
    return "\n".join(out) + "\n"


def coach_markdown(name: str, c: dict) -> str:
    out = [f"# Private leadership notes for {name}", "", c.get("headline", ""), "", "## Strengths", ""]
    out += [f"- {x}" for x in c.get("strengths", [])]
    out += ["", "## Moves for next meeting", ""] + [f"- {x}" for x in c.get("moves", [])]
    out += ["", "## Say it word for word", ""] + [f"- \"{x}\"" for x in c.get("scripts", [])]
    if c.get("rewrites"):
        out += ["", "## Assertive rewrites", ""]
        for rw in c["rewrites"]:
            out += [f"- You said: \"{rw.get('original', '')}\"", f"  - Try: \"{rw.get('rewrite', '')}\""]
    return "\n".join(out) + "\n"
