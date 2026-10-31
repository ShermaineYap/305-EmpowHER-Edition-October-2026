"""Rule-based recap and coaching, used when Gemma is unavailable (and as a sanity baseline)."""

from __future__ import annotations

import re
from collections import Counter

from .parser import fmt_time
from .text_utils import content_words, split_sentences

DECISION = re.compile(r"\b(let'?s go with|we('ll| will) go with|decided|agreed|we('re| are) going (to|with)|final answer|locked in|so the plan is)\b", re.I)
ACTION = re.compile(r"\b(i'?ll|i will|can you|could you|will you|you'?ll|by (monday|tuesday|wednesday|thursday|friday|tomorrow|next week|end of (day|week)))\b", re.I)
QUESTION = re.compile(r"\?\s*$")


def recap(turns, credit_events) -> dict:
    sentences = [(t, s) for t in turns for s in split_sentences(t.text)]
    freq = Counter(w for t in turns for w in content_words(t.text))
    top = {w for w, _ in freq.most_common(12)}

    scored = sorted(
        ((sum(w in top for w in content_words(s)) / (len(s.split()) ** 0.5 or 1), t, s) for t, s in sentences if len(s.split()) >= 7),
        key=lambda x: -x[0],
    )
    picked = sorted(scored[:4], key=lambda x: x[1].start)
    summary = [f"{t.speaker} said: {s}" for _, t, s in picked]

    decisions = [f"{t.speaker} ({fmt_time(t.start)}): {s}" for t, s in sentences if DECISION.search(s)][:6]
    actions = []
    for t, s in sentences:
        if ACTION.search(s) and not QUESTION.search(s):
            owner = t.speaker if re.search(r"\bi'?ll|\bi will", s, re.I) else ""
            actions.append({"owner": owner, "task": s, "due": ""})
    questions = [f"{t.speaker}: {s}" for t, s in sentences if QUESTION.search(s) and len(s.split()) >= 6][-4:]
    titles = {str(n): e["summary"] for n, e in enumerate(credit_events, 1)}
    return {"summary": summary, "decisions": decisions, "action_items": actions[:8], "open_questions": questions, "idea_titles": titles}


def coach(e: dict) -> dict:
    name, share, fair = e["name"], e["share"], e["fair"]
    strengths, moves, scripts = [], [], []

    if share >= fair * 0.9:
        strengths.append(f"You held about {share:.0%} of the airtime — your voice was clearly present.")
    else:
        strengths.append(f"When you spoke, you averaged {e['avg_words']:.0f} words a turn — people heard complete thoughts.")
    if e["drifted"]:
        strengths.append("Your ideas were strong enough that others repeated them — that is influence, now make it visible.")
    if e["hedge"] <= e["hedge_median"]:
        strengths.append("Your language was direct: fewer hedges than the team median.")
    if e["interrupter"] == 0:
        strengths.append("You let others finish — that builds trust and psychological safety.")
    if e["echoed"] == 0 and len(strengths) < 3:
        strengths.append("You didn't repackage other people's ideas as your own.")
    strengths.append("You stayed engaged through the meeting.")

    if share < fair * 0.7:
        moves.append("Claim a turn in the first five minutes — early speakers set the agenda.")
    if e["interrupted"]:
        moves.append(f"Reclaim the floor when cut off (it happened {e['interrupted']}×): pause, then finish your sentence.")
        scripts.append("I'd like to finish my point, then I'd love to hear yours.")
    if e["drifted"]:
        moves.append("Name your idea when it comes back around, with the timestamp if you can.")
        scripts.append("Glad we're aligned — that's the proposal I raised earlier. Here's how I'd roll it out.")
    if e["hedge"] > e["hedge_median"]:
        moves.append("Lead with the recommendation, then the reasoning — drop the pre-apology.")
        scripts.append("My recommendation is ___. Here's why.")
    if e["interrupter"] >= 2:
        moves.append(f"Count to two before jumping in — you took the floor {e['interrupter']}× before others finished.")
        scripts.append("Sorry — please finish, then I'll add mine.")
    if e["echoed"]:
        moves.append("When you build on someone's idea, say their name first — credit is a leadership currency.")
        scripts.append("Building on what ___ said earlier...")
    moves += [
        "Close your key point with a clear ask or decision.",
        "Volunteer to own one action item and say it out loud.",
    ]
    scripts.append("To make this concrete, I'll take the next step on ___ by ___.")

    rewrites = [{"original": s, "rewrite": r} for s, r in e.get("rule_rewrites", [])[:3]]
    headline = (
        f"{name}, your ideas carried this meeting more than your airtime shows."
        if e["drifted"]
        else f"{name}, here's how to turn your presence into influence next time."
    )
    return {"headline": headline, "strengths": strengths[:3], "moves": moves[:3], "scripts": scripts[:3], "rewrites": rewrites}


def facilitator_tips(stats: dict, events: list[dict], credit_events: list[dict], equity: float) -> list[str]:
    tips = []
    quiet = [s for s, v in stats.items() if v["talk_share"] < 0.5 * v["fair_share"]]
    if equity < 70:
        tips.append("Airtime was uneven. Try a round-robin for key decisions so every person speaks once before open debate.")
    if quiet:
        tips.append(f"Invite {', '.join(quiet)} by name early, with a specific question — not 'any thoughts?'.")
    n_int = sum(1 for e in events if e["label"] == "interruption")
    if n_int >= 3:
        tips.append(f"{n_int} interruptions were detected. Agree a 'let them land' norm: the facilitator returns the floor to anyone cut off.")
    if any(c["outcome"] == "credit_drift" for c in credit_events):
        tips.append("At least one idea was credited to the wrong person. Capture ideas with names in the notes as they are raised.")
    if not tips:
        tips.append("This meeting looks healthy: balanced airtime and few interruptions. Keep the same structure.")
    return tips
