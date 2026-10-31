"""TakeTheFloor — meeting equity & leadership coach (Streamlit app).

Run locally:   streamlit run app.py
Gemma:         set GEMINI_API_KEY (Google AI Studio) in .streamlit/secrets.toml or the environment,
               or OLLAMA_HOST for a local Gemma. Without either, the app runs in rules-only mode.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from takethefloor import analyze, parse_transcript
from takethefloor.analysis import coach as run_coach
from takethefloor.gemma import GemmaClient
from takethefloor.parser import Turn, fmt_time
from takethefloor.report import OUTCOME_TEXT, coach_markdown, markdown_report

ROOT = Path(__file__).parent
DEMOS = {
    "Product launch sync (Zoom .vtt)": ROOT / "data" / "demo_product_launch.vtt",
    "University project group": ROOT / "data" / "demo_study_group.txt",
    "Healthy stand-up (control)": ROOT / "data" / "demo_balanced_standup.txt",
}
# Validated categorical order (dataviz reference palette) — identity is never colour-alone: names are always printed.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SERIES_HC = ["#0b4a9e", "#a8380b", "#0a6b49", "#7a5200", "#9c2a58", "#005500", "#3a2b9e", "#9e1c1b"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

st.set_page_config(page_title="TakeTheFloor", page_icon="🎙️", layout="wide", initial_sidebar_state="expanded")


# ---------------------------------------------------------------------------- accessibility settings
with st.sidebar:
    st.markdown("### Accessibility")
    a11y_font = st.toggle("Dyslexia-friendly font (Atkinson Hyperlegible)", value=False)
    a11y_large = st.toggle("Larger text", value=False)
    a11y_contrast = st.toggle("High contrast", value=False)
    a11y_anon = st.toggle("Anonymise names (Speaker A, B…)", value=False, help="Use before sharing results with the whole team.")
    st.divider()
    st.markdown("### AI engine")
    secret_key = None
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        pass
    typed_key = st.text_input(
        "Gemini API key (optional)",
        type="password",
        help="Free key from aistudio.google.com. Used only for this session to call Gemma. Leave empty to use the deployed key or rules-only mode.",
    )
    use_gemma = st.toggle("Use Gemma", value=True, help="Off = deterministic rules only (fast, fully private).")

palette = SERIES_HC if a11y_contrast else SERIES
css = []
if a11y_font:
    css.append(
        "@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');"
        "html, body, [class*='css'], .stMarkdown, p, li, label, h1, h2, h3, button {font-family:'Atkinson Hyperlegible', sans-serif !important; letter-spacing:.01em;}"
    )
if a11y_large:
    css.append(".stMarkdown p, .stMarkdown li, label, .stDataFrame {font-size:1.18rem !important; line-height:1.6 !important;}")
if a11y_contrast:
    css.append(
        ".stApp {background:#ffffff !important; color:#000 !important;} .stMarkdown p, li {color:#000 !important;}"
        " .ttf-card {border:2px solid #000 !important; background:#fff !important;} a {text-decoration:underline !important;}"
    )
css.append(
    """
    .ttf-card {border:1px solid #d9d7d0; border-radius:12px; padding:14px 16px; margin:6px 0 12px; background:#ffffff;}
    .ttf-card h4 {margin:0 0 6px; font-size:1.02rem;}
    .ttf-tag {display:inline-block; padding:2px 8px; border-radius:999px; font-size:.78rem; font-weight:700; margin-right:6px; border:1px solid currentColor;}
    .ttf-drift {color:#9e1c1b;} .ttf-unattr {color:#7a5200;} .ttf-build {color:#0a6b49;}
    .ttf-quote {border-left:4px solid #b9b6ad; padding:4px 10px; margin:6px 0; color:#2b2a27;}
    .ttf-big {font-size:2.4rem; font-weight:800; line-height:1.05;}
    .ttf-sub {color:#52514e; font-size:.9rem;}
    :focus-visible {outline:3px solid #6250d6 !important; outline-offset:2px;}
    """
)
st.markdown(f"<style>{''.join(css)}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------- helpers
@st.cache_resource(show_spinner=False)
def get_client(key: str | None, enabled: bool) -> GemmaClient:
    if not enabled:
        return GemmaClient(backend="offline")
    if key:
        return GemmaClient(api_key=key)
    return GemmaClient()


@st.cache_data(show_spinner=False)
def run_analysis(text: str, key: str | None, enabled: bool, anon: bool) -> dict:
    turns = parse_transcript(text)
    if anon:
        turns = anonymise(turns)
    real_ts = bool(re.search(r"\d{1,2}:\d{2}", text))
    return analyze(turns, client=get_client(key, enabled), timestamps_real=real_ts)


def anonymise(turns: list[Turn]) -> list[Turn]:
    names = list(dict.fromkeys(t.speaker for t in turns))
    mapping = {n: f"Speaker {chr(65 + i)}" for i, n in enumerate(names)}
    out = []
    for t in turns:
        text = t.text
        for n, a in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
            text = re.sub(rf"\b{re.escape(n)}\b", a, text)
            text = re.sub(rf"\b{re.escape(n.split()[0])}\b", a, text)
        out.append(Turn(t.idx, mapping[t.speaker], t.start, t.end, text))
    return out


def colour_map(speakers: list[str]) -> dict[str, str]:
    return {s: palette[i % len(palette)] for i, s in enumerate(speakers)}


def style_fig(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=15 if a11y_large else 13, color=INK),
        hoverlabel=dict(font_size=14),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", zeroline=False)
    return fig


def esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(html: str):
    st.markdown(f'<div class="ttf-card" role="group">{html}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------- header + input
st.title("TakeTheFloor")
st.markdown(
    "**See who held the floor, who got cut off, and whose ideas got credited to someone else — "
    "then get private, Gemma-powered coaching to lead the next meeting.**"
)

col_in, col_demo = st.columns([3, 2], gap="large")
with col_demo:
    st.markdown("##### Try a demo meeting")
    demo_choice = st.radio("Demo transcript", list(DEMOS), index=0, label_visibility="collapsed")
    st.caption("All demo meetings are synthetic, written for this project. People are fictional.")
with col_in:
    st.markdown("##### Bring your own transcript")
    up = st.file_uploader("Upload a .vtt or .txt transcript (Zoom, Teams, Meet, Otter)", type=["vtt", "txt", "srt"], help="Nothing is stored. With Gemma off, nothing leaves this server.")
    pasted = st.text_area("Or paste it here", height=110, placeholder="[00:00:05] Aisha: What if we launched a student tier…\n[00:00:12] Mark: Let's not overcomplicate it…")

if up is not None:
    source_text, source_name = up.getvalue().decode("utf-8", errors="ignore"), up.name
elif pasted.strip():
    source_text, source_name = pasted, "Pasted transcript"
else:
    source_text, source_name = DEMOS[demo_choice].read_text(encoding="utf-8"), demo_choice

api_key = typed_key or secret_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
try:
    with st.spinner("Reading the room…"):
        R = run_analysis(source_text, api_key, use_gemma, a11y_anon)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

speakers = R["speakers"]
COL = colour_map(speakers)
client = get_client(api_key, use_gemma)

engine_note = R["engine"]
if use_gemma and not client.enabled:
    engine_note += " — add a Gemini API key in the sidebar to switch on Gemma."
elif R.get("engine_error") and R["recap_source"] == "rules":
    engine_note += " — Gemma didn't respond, so rule-based results are shown."
st.caption(f"Analysing: **{esc(source_name)}** · {len(R['turns'])} turns · {fmt_time(R['duration'])} · Engine: {engine_note}")

tabs = st.tabs(["Overview", "Floor timeline", "Interruptions", "Idea credit", "Language", "Leadership coach", "Accessible recap", "Captions"])

# ---------------------------------------------------------------------------- overview
with tabs[0]:
    c = R["counts"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Floor Health", f"{R['floor_health']}/100", help="Airtime balance, minus interruptions and mis-credited ideas, plus credited builds.")
    m2.metric("Airtime balance", f"{R['equity_index']}/100", help="1 − Gini coefficient of talk-time share. 100 = everyone spoke equally.")
    m3.metric("Interruptions", c["interruptions"], help="Backchannels ('mm-hmm') and supportive 'yes, and…' overlaps are not counted.")
    m4.metric("Ideas credited to the wrong person", c["credit_drift"])

    drift = [x for x in R["credit_events"] if x["outcome"] == "credit_drift"]
    if drift:
        d = drift[0]
        card(
            f'<span class="ttf-tag ttf-drift">Idea credit drift</span><h4>{esc(d["summary"])}</h4>'
            f'<div class="ttf-quote"><b>{fmt_time(d["original_time"])} · {esc(d["originator"])} said first:</b> “{esc(d["original_text"][:240])}”</div>'
            f'<div class="ttf-quote"><b>{fmt_time(d["echo_time"])} · {esc(d["echoed_by"])} repeated it:</b> “{esc(d["echo_text"][:240])}”</div>'
            + (f'<div class="ttf-quote"><b>Credit went to {esc(d["credited_to"])}:</b> {esc(d["credit_evidence"])}</div>' if d["credit_evidence"] else "")
        )

    st.markdown("#### Who held the floor")
    df = pd.DataFrame(
        [
            {
                "Person": s,
                "Share of talk time": R["stats"][s]["talk_share"],
                "Fair share": R["stats"][s]["fair_share"],
                "Turns": R["stats"][s]["turns"],
                "Interrupted by others": R["stats"][s]["interrupted_by_others"],
                "Interrupted others": R["stats"][s]["interrupted_others"],
                "Hedges / 100 words": R["stats"][s]["hedge_index"],
            }
            for s in speakers
        ]
    )
    fair = 1 / max(len(speakers), 1)
    fig = go.Figure(
        go.Bar(
            x=df["Share of talk time"],
            y=df["Person"],
            orientation="h",
            marker=dict(color=[COL[s] for s in df["Person"]], cornerradius=4),
            text=[f"{v:.0%}" for v in df["Share of talk time"]],
            textposition="outside",
            textfont=dict(color=INK),
            hovertemplate="%{y}: %{x:.0%} of talk time<extra></extra>",
        )
    )
    fig.add_vline(x=fair, line=dict(color=MUTED, dash="dash", width=2))
    fig.add_annotation(x=fair, y=1.02, yref="paper", text=f"fair share {fair:.0%}", showarrow=False, font=dict(color=MUTED, size=12), xanchor="left")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(tickformat=".0%", range=[0, max(df["Share of talk time"].max() * 1.25, fair * 1.4)])
    st.plotly_chart(style_fig(fig, 60 + 46 * len(speakers)), width="stretch", config={"displayModeBar": False})
    top, low = df.iloc[0], df.iloc[-1]
    st.markdown(
        f"<p class='ttf-sub'>Text summary: {esc(top['Person'])} spoke {top['Share of talk time']:.0%} of the time "
        f"({top['Share of talk time'] / fair:.1f}× a fair share); {esc(low['Person'])} spoke {low['Share of talk time']:.0%}.</p>",
        unsafe_allow_html=True,
    )
    with st.expander("Table view"):
        st.dataframe(df.style.format({"Share of talk time": "{:.0%}", "Fair share": "{:.0%}", "Hedges / 100 words": "{:.1f}"}), hide_index=True, width="stretch")

    st.markdown("#### What the facilitator can change next time")
    for tip in R["facilitator_tips"]:
        st.markdown(f"- {tip}")
    st.download_button("Download full report (Markdown)", markdown_report(R, source_name), file_name="takethefloor_report.md", mime="text/markdown")

# ---------------------------------------------------------------------------- timeline
with tabs[1]:
    st.markdown("#### Floor timeline")
    st.caption("Each bar is one turn. ▼ marks a true interruption; ◆ marks where an idea was first raised; ★ marks where it was repeated.")
    fig = go.Figure()
    for s in speakers:
        ts = [t for t in R["turns"] if t.speaker == s]
        fig.add_trace(
            go.Bar(
                base=[t.start for t in ts],
                x=[max(t.duration, 0.6) for t in ts],
                y=[s] * len(ts),
                orientation="h",
                marker=dict(color=COL[s], line=dict(color="#fcfcfb", width=2)),
                customdata=[[fmt_time(t.start), t.text[:140]] for t in ts],
                hovertemplate=f"<b>{esc(s)}</b> %{{customdata[0]}}<br>%{{customdata[1]}}<extra></extra>",
                name=s,
            )
        )
    real = [e for e in R["interruptions"] if e["label"] == "interruption"]
    if real:
        fig.add_trace(
            go.Scatter(
                x=[e["time"] for e in real],
                y=[e["interrupted"] for e in real],
                mode="markers",
                marker=dict(symbol="triangle-down", size=16, color=INK, line=dict(color="#fff", width=2)),
                customdata=[[e["interrupter"], fmt_time(e["time"])] for e in real],
                hovertemplate="Interrupted by %{customdata[0]} at %{customdata[1]}<extra></extra>",
            )
        )
    for ce in R["credit_events"]:
        fig.add_trace(
            go.Scatter(
                x=[ce["original_time"], ce["echo_time"]],
                y=[ce["originator"], ce["echoed_by"]],
                mode="markers+lines",
                line=dict(color="#9e1c1b" if ce["outcome"] == "credit_drift" else MUTED, dash="dot", width=2),
                marker=dict(symbol=["diamond", "star"], size=16, color="#9e1c1b" if ce["outcome"] == "credit_drift" else "#0a6b49", line=dict(color="#fff", width=2)),
                hovertemplate=f"{esc(ce['summary'])}<br>{OUTCOME_TEXT[ce['outcome']]}<extra></extra>",
            )
        )
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Minutes into meeting", tickvals=list(range(0, int(R["duration"]) + 60, 60)), ticktext=[f"{m}:00" for m in range(0, int(R["duration"]) // 60 + 2)])
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style_fig(fig, 90 + 52 * len(speakers)), width="stretch", config={"displayModeBar": False})
    st.markdown(
        f"<p class='ttf-sub'>Text summary: {len(real)} interruption(s) and {len(R['credit_events'])} repeated idea(s) are marked. "
        "The Captions tab lists every turn in order with the same markers in words.</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------- interruptions
with tabs[2]:
    st.markdown("#### Interruptions — told apart from healthy overlap")
    st.caption("Speaker changes where someone was cut off or talked over are checked, then classified. Backchannels and 'yes, and…' overlaps are kept separate so friendly energy isn't punished.")
    ev = R["interruptions"]
    if not ev:
        st.success("No cut-offs or overlaps detected in this meeting.")
    else:
        mat = R["interruption_matrix"]
        if any(any(row) for row in mat):
            hm = go.Figure(
                go.Heatmap(
                    z=mat,
                    x=speakers,
                    y=speakers,
                    colorscale=[[0, "#f4f3ef"], [0.001, "#cde2fb"], [0.5, "#3987e5"], [1, "#104281"]],
                    showscale=False,
                    xgap=2,
                    ygap=2,
                    text=[[str(v) if v else "" for v in row] for row in mat],
                    texttemplate="%{text}",
                    textfont=dict(size=16),
                    hovertemplate="%{y} interrupted %{x}: %{z} time(s)<extra></extra>",
                )
            )
            hm.update_xaxes(title="…interrupted this person", side="top")
            hm.update_yaxes(title="This person…", autorange="reversed")
            st.plotly_chart(style_fig(hm, 120 + 48 * len(speakers)), width="stretch", config={"displayModeBar": False})
        label_names = {"interruption": "Interruption", "supportive": "Supportive overlap", "backchannel": "Backchannel"}
        for e in ev:
            by = "Gemma" if e["labeled_by"] == "gemma" else "rules"
            regain = " They got the floor back afterwards." if e["regained_floor"] else ""
            card(
                f'<span class="ttf-tag {"ttf-drift" if e["label"] == "interruption" else "ttf-build"}">{label_names[e["label"]]}</span>'
                f'<span class="ttf-sub">{fmt_time(e["time"])} · labelled by {by}</span>'
                f'<div class="ttf-quote"><b>{esc(e["interrupted"])}:</b> “…{esc(e["cut_text"][-150:])}”</div>'
                f'<div class="ttf-quote"><b>{esc(e["interrupter"])}:</b> “{esc(e["taking_text"][:180])}”</div>'
                f'<div class="ttf-sub">{esc(e["reason"])}{regain}</div>'
            )

# ---------------------------------------------------------------------------- idea credit
with tabs[3]:
    st.markdown("#### Idea credit tracker")
    st.caption("Finds ideas that were raised by one person and repeated by another, then checks who the room credited.")
    if not R["credit_events"]:
        st.info("No repeated ideas found in this meeting.")
    for ce in R["credit_events"]:
        cls = {"credit_drift": "ttf-drift", "unattributed": "ttf-unattr", "credited_build": "ttf-build"}[ce["outcome"]]
        card(
            f'<span class="ttf-tag {cls}">{OUTCOME_TEXT[ce["outcome"]]}</span><h4>{esc(ce["summary"])}</h4>'
            f'<div class="ttf-quote"><b>{fmt_time(ce["original_time"])} · {esc(ce["originator"])}:</b> “{esc(ce["original_text"][:260])}”</div>'
            f'<div class="ttf-quote"><b>{fmt_time(ce["echo_time"])} · {esc(ce["echoed_by"])}:</b> “{esc(ce["echo_text"][:260])}”</div>'
            + (f'<div class="ttf-quote"><b>Credit:</b> {esc(ce["credit_evidence"])}</div>' if ce["credit_evidence"] else "")
            + f'<div class="ttf-sub">Shared key terms: {esc(", ".join(ce["shared_terms"]))} · similarity {ce["similarity"]:.2f}</div>'
        )

# ---------------------------------------------------------------------------- language
with tabs[4]:
    st.markdown("#### Hedge Index — language that gives away authority")
    st.caption("Hedges per 100 words. Hedging isn't wrong, but habitual pre-apologies and self-discounting make strong ideas sound optional.")
    hdf = pd.DataFrame([{"Person": s, "Hedges / 100 words": R["stats"][s]["hedge_index"]} for s in speakers]).sort_values("Hedges / 100 words", ascending=False)
    fig = go.Figure(
        go.Bar(
            x=hdf["Hedges / 100 words"],
            y=hdf["Person"],
            orientation="h",
            marker=dict(color=[COL[s] for s in hdf["Person"]], cornerradius=4),
            text=[f"{v:.1f}" for v in hdf["Hedges / 100 words"]],
            textposition="outside",
            hovertemplate="%{y}: %{x:.1f} hedges per 100 words<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style_fig(fig, 60 + 46 * len(speakers)), width="stretch", config={"displayModeBar": False})
    if not R["hedge_hits"]:
        st.success("No strong hedges found.")
    for h in R["hedge_hits"]:
        kinds = ", ".join(sorted({x["category"] for x in h["hedges"]}))
        why = " ".join(sorted({x["why"] for x in h["hedges"]}))
        card(
            f'<span class="ttf-tag ttf-unattr">{esc(kinds)}</span><span class="ttf-sub">{fmt_time(h["time"])} · {esc(h["speaker"])}</span>'
            f'<div class="ttf-quote"><b>Said:</b> “{esc(h["sentence"])}”</div>'
            f'<div class="ttf-quote"><b>Try:</b> “{esc(h["rewrite"])}”</div><div class="ttf-sub">{esc(why)}</div>'
        )

# ---------------------------------------------------------------------------- coach
with tabs[5]:
    st.markdown("#### Private leadership coach")
    st.caption("Each person gets their own notes, grounded only in what happened in this meeting. Share it with them — not the whole team.")
    who = st.selectbox("Coach for", speakers, index=next((i for i, s in enumerate(speakers) if R["stats"][s]["ideas_credited_away"]), len(speakers) - 1))
    with st.spinner(f"Gemma is preparing notes for {who}…" if client.enabled else "Preparing notes…"):
        cdata, csrc = run_coach(R, who, client)
    s = R["stats"][who]
    a, b, c3, d = st.columns(4)
    a.metric("Talk time", f"{s['talk_share']:.0%}", f"{s['talk_share'] - s['fair_share']:+.0%} vs fair share")
    b.metric("Times cut off", s["interrupted_by_others"])
    c3.metric("Ideas credited away", s["ideas_credited_away"])
    d.metric("Hedges / 100 words", f"{s['hedge_index']:.1f}")
    st.markdown(f"**{esc(cdata.get('headline', ''))}**")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("##### Strengths")
        for x in cdata.get("strengths", []):
            st.markdown(f"- {x}")
        st.markdown("##### Moves for next meeting")
        for x in cdata.get("moves", []):
            st.markdown(f"- {x}")
    with right:
        st.markdown("##### Say it word for word")
        for x in cdata.get("scripts", []):
            st.markdown(f"> {x}")
        if cdata.get("rewrites"):
            st.markdown("##### Assertive rewrites of your own words")
            for rw in cdata["rewrites"]:
                card(f'<div class="ttf-quote"><b>You said:</b> “{esc(rw.get("original", ""))}”</div><div class="ttf-quote"><b>Try:</b> “{esc(rw.get("rewrite", ""))}”</div>')
    st.caption(f"Written by {'Gemma' if csrc == 'gemma' else 'rule-based coach (turn on Gemma for personalised wording)'}.")
    st.download_button(f"Download {who}'s private notes", coach_markdown(who, cdata), file_name=f"coach_{who.replace(' ', '_')}.md", mime="text/markdown")

# ---------------------------------------------------------------------------- recap
with tabs[6]:
    st.markdown("#### Accessible recap")
    st.caption("Plain language for teammates who are Deaf or hard of hearing, neurodivergent, reading in a second language, or who missed the meeting.")
    rc = R["recap"]
    st.markdown("##### What happened")
    for x in rc.get("summary", []):
        st.markdown(f"- {x}")
    if rc.get("decisions"):
        st.markdown("##### Decisions")
        for x in rc["decisions"]:
            st.markdown(f"- {x}")
    if rc.get("action_items"):
        st.markdown("##### Who does what")
        st.dataframe(pd.DataFrame(rc["action_items"]).rename(columns=str.title), hide_index=True, width="stretch")
    if rc.get("open_questions"):
        st.markdown("##### Still open")
        for x in rc["open_questions"]:
            st.markdown(f"- {x}")
    st.caption(f"Recap written by {'Gemma' if R['recap_source'] == 'gemma' else 'rule-based extractor'}.")

# ---------------------------------------------------------------------------- captions
with tabs[7]:
    st.markdown("#### Captions with speaker labels")
    st.caption("Every turn in order, with events written out in words (no colour needed).")
    int_at = {e["turn_idx"]: e for e in R["interruptions"] if e["label"] == "interruption"}
    orig_at = {}
    echo_at = {}
    for ce in R["credit_events"]:
        orig_at.setdefault(ce["original_time"], ce)
        echo_at.setdefault(ce["echo_time"], ce)
    lines = []
    for t in R["turns"]:
        notes = []
        if t.idx in int_at:
            notes.append(f"[interrupts {int_at[t.idx]['interrupted']}]")
        if t.start in orig_at:
            notes.append("[raises an idea]")
        if t.start in echo_at:
            notes.append(f"[repeats {echo_at[t.start]['originator']}'s idea]")
        lines.append(f"**{fmt_time(t.start)} · {esc(t.speaker)}** {' '.join(notes)}  \n{esc(t.text)}")
    st.markdown("\n\n".join(lines))

st.divider()
st.caption("TakeTheFloor · 305 EmpowHER Edition October 2026 · Analytics Competition · Built with Gemma. Insights describe one meeting, not a person's worth — use them to start conversations, not to grade people.")
