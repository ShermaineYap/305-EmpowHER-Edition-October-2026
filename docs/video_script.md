# Video scripts

Record both as MP4 (OBS Studio, Windows Game Bar `Win+Alt+R`, or macOS `Cmd+Shift+5`). Browser full-screen on https://takethefloor.streamlit.app, zoom 110–125% so text is readable. Upload as **Unlisted** on YouTube and paste the links into the README, slides and Devpost.

---

## A. 10-minute feature demo (`TakeTheFloor_feature_demo.mp4`)

| Time | On screen | Say (roughly) |
|---|---|---|
| 0:00–0:45 | Slide 1 → 2 | "Hi, I'm Shermaine from APU in Malaysia. This is TakeTheFloor, for the Analytics path of 305 EmpowHER. Leadership is visible in meetings — but airtime is uneven, interruptions aren't random, and ideas lose their author. None of that shows up in meeting notes." |
| 0:45–1:15 | Slide 3 | "Here's the moment I built this for. Aisha proposes a student tier and gets cut off. Two minutes later Mark pitches the same idea, and the room says 'great idea, Mark.'" |
| 1:15–2:30 | App → Overview, Product launch demo | Point at **Floor Health 38**, airtime balance, **4 interruptions**, **1 idea credited to the wrong person**. Read the credit-drift card: the three quotes with timestamps. Scroll to the airtime chart: "Mark held 47% — 2.3× a fair share." Open **Table view**. Read one facilitator tip. |
| 2:30–3:30 | Floor timeline tab | "Every bar is a turn. Triangles are interruptions, the diamond is where Aisha raised the idea, the star is where Mark repeated it." Hover a bar to show the quote. |
| 3:30–4:45 | Interruptions tab | Heatmap: "Mark interrupted Aisha twice and Mei Ling once." Scroll the cards: "Notice this one is a **backchannel** — Daniel just said 'Yeah' — and this one is **supportive**: Aisha says 'Yes, and…' to build on Priya. Gemma labels each moment in context, so friendly energy isn't punished." |
| 4:45–5:30 | Idea credit tab | "Gemma titled the idea. Shared terms and similarity are shown so it's explainable." |
| 5:30–6:15 | Language tab | Priya's hedges: "'This might be a dumb idea, but I think maybe we could sort of…' becomes 'I recommend we shorten the onboarding to three screens.'" |
| 6:15–7:30 | Leadership coach → Aisha, then Priya | Read Aisha's headline, one strength, one move, one script. Switch to Priya: show Gemma's rewrites of her own sentences. "Notes are private — download them for that person only." |
| 7:30–8:15 | Accessible recap + Captions | "Plain-language recap for Deaf or hard-of-hearing, neurodivergent or second-language teammates: decisions, who does what, open questions." Show the Captions tab with events written in words. |
| 8:15–8:50 | Sidebar | Toggle **dyslexia-friendly font**, **larger text**, **high contrast**, **anonymise names**. |
| 8:50–9:20 | Switch demo to **Healthy stand-up** | "Control meeting: Floor Health 86, no interruptions, and a credited build — 'Building on Grace's audit'. It doesn't just flag everything." |
| 9:20–10:00 | Slide 7 (evidence) → Slide 10 | "In my Kaggle notebook I validated the detectors on labelled meetings: 5 of 5 interruptions, 4 of 4 credit events, zero false alarms, and Gemma agreed with all six interruption labels. It's honest scope — synthetic data — and next I'll validate on the AMI corpus. TakeTheFloor makes the invisible visible. Thank you." |

## B. 5-minute backup demo (`TakeTheFloor_backup_demo.mp4`)

| Time | On screen | Say |
|---|---|---|
| 0:00–0:30 | Slide 1–3 | Problem + the Aisha/Mark moment in two sentences. |
| 0:30–1:30 | Overview | Floor Health, airtime, credit-drift card. |
| 1:30–2:30 | Interruptions | Matrix + one interruption vs. the backchannel and supportive overlap. |
| 2:30–3:30 | Leadership coach (Aisha) + Language (Priya rewrite) | Private coaching and rewrites. |
| 3:30–4:15 | Accessible recap + sidebar toggles | Accessibility. |
| 4:15–5:00 | Slide 7 | Validation results, Gemma agreement, honest scope, close. |

## Live demo checklist

* Open the app 5 minutes before your slot so it's awake (Streamlit Cloud apps sleep when idle).
* Demo meetings load instantly (recorded Gemma runs). Only paste/upload a new transcript live if you have ~1–2 minutes for Gemma.
* Backup: the 5-minute MP4, and `streamlit run app.py` locally.
