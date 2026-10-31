# Devpost submission text (copy-paste)

**Project name:** TakeTheFloor

**Tagline (≤ 200 chars):** See who held the floor, who got cut off, and whose ideas got credited to someone else — then get private, Gemma-powered coaching to lead the next meeting.

**Competition type:** Analytics Competition
**Track / challenges:** Track #1 — Hackathon Competition (General Build) · LLM Gemma Challenge · Kaggle Challenge
**GenAI tools used:** Gemma (in-app) · Anthropic Claude (coding assistant)

**Built with:** python, streamlit, gemma, google-ai-studio, gemini-api, pandas, plotly, matplotlib, jupyter, kaggle, pytest

**Links**
- Live app: https://takethefloor.streamlit.app
- GitHub: https://github.com/ShermaineYap/305-EmpowHER-Edition-October-2026
- Kaggle notebook: KAGGLE_LINK_HERE
- Google Slides: GOOGLE_SLIDES_LINK_HERE
- 10-min feature demo: FEATURE_VIDEO_LINK_HERE
- 5-min backup demo: BACKUP_VIDEO_LINK_HERE

---

## Inspiration
Leadership is visible in meetings — and quietly lost there. Research shows airtime is uneven in mixed groups, interruptions land more often on women, and ideas lose their author when someone else repeats them. Women staffers in the Obama White House invented "amplification" to fight that last one. None of it shows up in meeting notes, so nobody can fix it. I wanted a tool that makes those dynamics visible — and turns them into coaching instead of blame.

## What it does
Upload a meeting transcript (Zoom/Teams/Meet .vtt, Otter, or plain "Name: text") and TakeTheFloor shows:
- **Floor Health** — one score for the facilitator.
- **Airtime** — each person's share vs. a fair share.
- **Interruptions** — cut-offs and overlaps, told apart from "mm-hmm" backchannels and supportive "yes, and…" overlap, with a who-interrupted-whom matrix.
- **Idea credit tracker** — catches an idea raised by one person, repeated by another, and credited to the repeater, with exact quotes and timestamps.
- **Hedge Index** — pre-apologies and self-discounting, each with a confident rewrite.
- **Private leadership coach (Gemma)** — strengths, next moves, word-for-word scripts and rewrites of your own sentences.
- **Accessible recap (Gemma)** — plain-language decisions, owners and open questions for Deaf/HoH, neurodivergent and second-language teammates.
- Dyslexia-friendly font, large text, high contrast, colour-blind-safe charts with table views, captions, and one-click anonymisation.

## How I built it
A Python engine (`takethefloor/`) parses transcripts into speaker turns, then runs transparent detectors: Gini-based airtime balance, cut-off/overlap interruption candidates, 13 hedge pattern families, and an idea-credit tracker using content-word cosine similarity plus attribution and praise patterns. **Gemma 4** (via Google AI Studio, `gemma-4-26b-a4b-it` with `gemma-4-31b-it` fallback, or local Gemma via Ollama) re-labels each interruption in context, titles ideas, writes the accessible recap and the private coaching. Every Gemma response is parsed defensively and merged over the rule-based result. The dashboard is Streamlit + Plotly, deployed on Streamlit Community Cloud. A Kaggle notebook evaluates the detectors against hand-labelled meetings with a sensitivity analysis. 20 pytest tests cover parser formats, detectors vs. labels, and the Gemma merge path.

## Challenges I ran into
- **Not punishing friendly conversation.** Overlap isn't always rude, so I separated backchannels and supportive overlap from real interruptions — rules first, Gemma in context second.
- **Gemma 4 reasons before it answers**, so calls took about a minute and sometimes ran out of tokens. I added a system instruction that roughly halved the thinking, raised the token budget, hardened JSON parsing, added model fallback, and recorded real Gemma runs for the demo meetings so the live demo is instant (clearly labelled), while uploaded transcripts still call Gemma live.
- **Honest evaluation.** It's easy to "prove" a detector on data you wrote yourself, so I added a healthy control meeting to test for false alarms, a threshold sensitivity sweep, and stated the scope plainly.

## Accomplishments that I'm proud of
- On three hand-labelled meetings: **5/5 interruptions and 4/4 idea-credit events found, zero false alarms**, and the healthy stand-up scores highest (86 vs. 38).
- Gemma's interruption labels agreed with my hand labels on **6/6** candidates, including the tricky backchannel and "yes, and…" cases.
- Accessibility is a feature, not a checkbox: the recap and captions serve people who couldn't follow the meeting live.

## What I learned
Explainability matters as much as accuracy when a tool talks about people: every flag has to show its evidence. Combining transparent rules with an LLM gives the best of both — testable baselines plus contextual judgement.

## What's next for TakeTheFloor
- Validate on the AMI Meeting Corpus and real, consented team meetings.
- Live mode that nudges the facilitator during the call.
- An "Amplify" button to credit a colleague's idea in one tap.
- Zoom/Teams integration so the recap and private notes arrive automatically.
