"""Generates the three SYNTHETIC demo meetings shipped with TakeTheFloor.

All names, companies and dialogue are fictional and were written for this hackathon.
Each meeting has hand-labelled ground truth (data/demo_labels.json) so the detectors can be
evaluated honestly — see tests/ and notebooks/.

Run:  python data/build_demo_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
WPS = 2.6  # words per second


def _schedule(script, start=4.0):
    """script rows: (speaker, text, gap_before_seconds). Negative gap = talks over previous speaker."""
    rows, clock = [], start
    for speaker, text, gap in script:
        begin = max(clock + gap, rows[-1]["start"] + 1.0 if rows else 0)
        dur = max(len(text.split()) / WPS, 0.8)
        rows.append({"speaker": speaker, "text": text, "start": round(begin, 2), "end": round(begin + dur, 2)})
        clock = begin + dur
    return rows


def _ts(sec, vtt=True):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}" if vtt else f"{int(h):02d}:{int(m):02d}:{int(s):02d}"


# ---------------------------------------------------------------------------------------------
# Meeting 1 — product launch sync (WebVTT, Zoom-style).  Planted: Aisha's student-tier idea is
# cut off by Mark, re-pitched by Mark later in the meeting and credited to Mark. Mei Ling is interrupted
# twice. Daniel backchannels. Priya hedges heavily but makes a supportive overlap.
# ---------------------------------------------------------------------------------------------
LAUNCH = [
    ("Mark", "Okay let's get started. Agenda today is the launch plan for StudyNest: pricing, onboarding, and launch channels. Leadership wants pricing locked by Friday, so that is the big one, and I want us out of here with a decision. I have a strong view on it but let's walk through everything first.", 0.5),
    ("Daniel", "Sounds good. Sales has been asking about pricing all week so I'm glad we're doing this.", 0.6),
    ("Mark", "Right. So my starting point is one flat plan at twelve dollars a month. Simple to explain, simple to sell, one line on the pricing page. Every company I have worked at that started with a complicated pricing page regretted it, because sales can't explain it and customers stall.", 0.5),
    ("Priya", "Sorry, I just wanted to ask, does that make sense for the free trial length, or is that a separate question?", 0.8),
    ("Mark", "Separate question, let's park it.", 0.4),
    ("Mei Ling", "I pulled the churn data from the beta. Users who signed up with a university email churned about half as often as everyone else, and most of them", 0.7),
    ("Mark", "Yeah, the beta was tiny though, I wouldn't read too much into it. Daniel, what are you hearing from prospects?", -1.2),
    ("Daniel", "Honestly price is the number one objection. Twelve dollars feels steep for a lot of people.", 0.5),
    ("Aisha", "What if we launch a student tier at half the price of the pro plan, verified with a student email, so we get into university campuses before the competitors and", 0.9),
    ("Mark", "Let's not overcomplicate it. Multiple tiers means more support tickets and a confusing pricing page. Priya, where are we on onboarding?", -1.0),
    ("Priya", "Um, so, this might be a dumb idea, but I think maybe we could sort of shorten the onboarding to three screens? I'm not sure if that's okay.", 0.9),
    ("Daniel", "Yeah.", -0.9),
    ("Priya", "Because right now people drop off at screen four, where we ask for payment details before they have seen any value.", 0.3),
    ("Aisha", "Yes, and if we move the payment step after the first study session, the trial actually shows value before we ask for anything.", -0.6),
    ("Priya", "Exactly, that's the flow I sketched. I can share the prototype after this.", 0.4),
    ("Mark", "Fine, Priya send that over and we will review it async. Next, launch channels. We have a modest budget, roughly what we spent on the beta, and I want most of it going where we can measure results in the first two weeks. Daniel?", 0.5),
    ("Daniel", "We've got the newsletter, the partner webinars, and paid social. I'd put most of the budget into paid social for the first month.", 0.5),
    ("Mei Ling", "Can I add one thing on channels? The beta users who came from referrals had the highest retention, so a referral reward might", 0.8),
    ("Daniel", "Paid social is just faster though, referrals take forever to ramp up.", -0.9),
    ("Mei Ling", "Okay.", 0.6),
    ("Mark", "Let's go with paid social as the main channel and revisit referrals in month two. We can always add channels later, but we can't get launch week back.", 0.5),
    ("Aisha", "I'll draft the launch announcement. I'd like it to mention the trial change once Priya's flow is confirmed.", 0.7),
    ("Mark", "Good. Okay, circling back to pricing, because we do need a decision.", 0.6),
    ("Daniel", "Mm-hmm.", 0.3),
    ("Mark", "What if we did a discounted tier for students, verified with a student email, priced at half the pro plan? That gets us onto university campuses early.", 0.4),
    ("Daniel", "Great idea, Mark. That solves the price objection I keep hearing.", 0.5),
    ("Priya", "Oh, I like that.", 0.4),
    ("Daniel", "Let's go with Mark's pricing plan for the student segment then.", 0.5),
    ("Aisha", "I think that's what I suggested earlier, the student tier.", 0.8),
    ("Mark", "Sure, sure. Anyway, Mei Ling, can you model what half price does to revenue by Friday?", -0.4),
    ("Mei Ling", "Yes, I'll build that model by Friday. I'll use the beta churn numbers for the student segment.", 0.6),
    ("Mark", "Great. Action items: Priya sends the prototype, Aisha drafts the announcement, Mei Ling models pricing, Daniel briefs sales. Thanks everyone.", 0.5),
]

# ---------------------------------------------------------------------------------------------
# Meeting 2 — university project group (bracket timestamps).  Planted: Nurul's poster idea gets
# re-pitched by Wei Jie and credited to him; Kavitha builds on Jason's idea AND names him
# (the healthy "credited build").
# ---------------------------------------------------------------------------------------------
STUDY = [
    ("Wei Jie", "Okay guys, for the data analytics assignment we need to pick a topic and split the work today.", 0.5),
    ("Nurul", "Sorry, maybe we could do something on public transport? Like analysing LRT ridership data and peak hour crowding in Klang Valley.", 0.8),
    ("Wei Jie", "Hmm, could be. Anyone else?", 0.6),
    ("Jason", "I found an open dataset on food prices from DOSM. We could look at how food inflation changed by state.", 0.7),
    ("Kavitha", "That's interesting. I think maybe we can combine it with household income data, if that makes sense?", 0.6),
    ("Wei Jie", "Let's think about what the lecturer wants. She said the topic must have a clear stakeholder.", 0.6),
    ("Nurul", "For transport the stakeholder would be Prasarana, and we could recommend extra trains at the most crowded stations during", 0.7),
    ("Wei Jie", "Actually, wait, does anyone know if the deadline is week ten or week eleven?", -0.8),
    ("Jason", "Week eleven, Friday.", 0.5),
    ("Kavitha", "Building on Jason's food price idea, we could make a dashboard showing which states are hit hardest, with income as the second layer.", 0.8),
    ("Jason", "Yes, I can clean the DOSM data this weekend.", 0.5),
    ("Wei Jie", "Okay. But I was also thinking about transport. What if we analyse LRT ridership and peak hour crowding, then recommend extra trains for the most crowded stations? Prasarana would be the stakeholder.", 0.9),
    ("Kavitha", "Oh that's a great idea, Wei Jie. Very clear stakeholder.", 0.5),
    ("Jason", "Agreed, Wei Jie's topic is stronger for the rubric.", 0.5),
    ("Nurul", "Okay.", 0.9),
    ("Wei Jie", "So the plan is the transport topic. I'll be the leader and do the presentation. Jason does data cleaning, Kavitha does the dashboard, Nurul does the report.", 0.6),
    ("Kavitha", "Can we keep the food price dashboard idea as a backup in case the LRT data is messy?", 0.6),
    ("Wei Jie", "Sure, backup. Let's meet again on Thursday.", 0.5),
]

# ---------------------------------------------------------------------------------------------
# Meeting 3 — a healthy daily stand-up (plain "Name: text", no timestamps).  Control case:
# balanced airtime, an idea that is credited properly, no interruptions.
# ---------------------------------------------------------------------------------------------
STANDUP = [
    ("Farah", "Morning everyone. Quick round, same order as always. Tom, you start."),
    ("Tom", "Yesterday I fixed the export bug. Today I'm writing tests for the CSV importer. No blockers."),
    ("Farah", "Thanks Tom. Grace?"),
    ("Grace", "I finished the accessibility audit. We fail colour contrast on the settings page. I recommend we switch the grey text to the darker token this sprint."),
    ("Farah", "Good catch, Grace. Let's add that to the sprint. Ravi?"),
    ("Ravi", "I'm pairing with Grace on the contrast fix after lunch. Building on Grace's audit, I'll also add an automated contrast check to the CI pipeline."),
    ("Grace", "That would be great, thank you Ravi."),
    ("Farah", "I'm meeting the client at three to confirm the release date. I'll share notes in the channel. Anything else before we wrap?"),
    ("Tom", "Nothing from me."),
    ("Farah", "Great, thanks all. Have a good day."),
]

LABELS = {
    "demo_product_launch.vtt": {
        "interruptions": [
            {"interrupter": "Mark", "interrupted": "Mei Ling"},
            {"interrupter": "Mark", "interrupted": "Aisha"},
            {"interrupter": "Daniel", "interrupted": "Mei Ling"},
            {"interrupter": "Mark", "interrupted": "Aisha", "note": "brushes off her credit claim"},
        ],
        "non_interruptions": [
            {"speaker": "Daniel", "label": "backchannel"},
            {"speaker": "Aisha", "label": "supportive", "note": "'Yes, and…' building on Priya"},
        ],
        "credit": [{"outcome": "credit_drift", "originator": "Aisha", "echoed_by": "Mark"}],
    },
    "demo_study_group.txt": {
        "interruptions": [{"interrupter": "Wei Jie", "interrupted": "Nurul"}],
        "credit": [
            {"outcome": "credit_drift", "originator": "Nurul", "echoed_by": "Wei Jie"},
            {"outcome": "credited_build", "originator": "Jason", "echoed_by": "Kavitha"},
        ],
    },
    "demo_balanced_standup.txt": {"interruptions": [], "credit": [{"outcome": "credited_build", "originator": "Grace", "echoed_by": "Ravi"}]},
}


def main():
    launch = _schedule(LAUNCH, start=6.0)
    vtt = ["WEBVTT", "", "NOTE Synthetic demo meeting written for TakeTheFloor. All people are fictional.", ""]
    for n, r in enumerate(launch, 1):
        vtt += [str(n), f"{_ts(r['start'])} --> {_ts(r['end'])}", f"<v {r['speaker']}>{r['text']}</v>", ""]
    (HERE / "demo_product_launch.vtt").write_text("\n".join(vtt), encoding="utf-8")

    study = _schedule(STUDY, start=3.0)
    lines = ["# Synthetic demo meeting written for TakeTheFloor. All people are fictional."]
    lines += [f"[{_ts(r['start'], vtt=False)}] {r['speaker']}: {r['text']}" for r in study]
    (HERE / "demo_study_group.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = ["# Synthetic demo stand-up (no timestamps) written for TakeTheFloor. All people are fictional."]
    lines += [f"{s}: {t}" for s, t in STANDUP]
    (HERE / "demo_balanced_standup.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (HERE / "demo_labels.json").write_text(json.dumps(LABELS, indent=2), encoding="utf-8")
    print("wrote", [p.name for p in HERE.glob("demo_*")])


if __name__ == "__main__":
    main()
