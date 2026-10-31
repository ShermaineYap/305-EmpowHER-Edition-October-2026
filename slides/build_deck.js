const pptxgen = require("pptxgenjs");
const React = require("react");
const RDS = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("/root/.claude/skills/synced/c2376827-4f59-44b7-8fbd-9e2d5139f606_f9ab012d-464b-4481-a356-1169579ae404/pptx/scripts/apply_theme.js");
const REPO = "/home/claude/305-empowher-edition-october-2026";
const SHOTS = REPO + "/docs/screenshots/";

const THEME = {
  name: "TakeTheFloor",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1530", lt1: "FFFFFF", dk2: "3A2B6E", lt2: "F3F1F8",
    accent1: "6250D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "EDA100", accent5: "9E1C1B", accent6: "2A78D6",
    hlink: "6250D6", folHlink: "3A2B6E",
  },
};
const HEX = THEME.colors;

async function icon(Comp, color, size = 256) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.title = "TakeTheFloor — 305 EmpowHER Edition October 2026";
  pres.author = "Shermaine Yap Shi Min";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "Dark title",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.55, w: 8.8, h: 1.1, fontFace: THEME.headFontFace, fontSize: 48, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 2.75, w: 8.4, h: 1.0, fontSize: 20, color: C.background2, valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "Light content",
    background: { color: C.background1 },
    margin: [0.5, 0.5, 0.5, 0.5],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontFace: THEME.headFontFace, fontSize: 30, bold: true, color: C.text2, valign: "middle", margin: 0 }, text: "" } },
      { text: { text: "TakeTheFloor · 305 EmpowHER Oct 2026 · Analytics Competition", options: { x: 0.5, y: 5.2, w: 6.5, h: 0.3, fontSize: 10, color: "6B6880", margin: 0 } } },
    ],
    slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: "6B6880", align: "right" },
  });

  const I = {
    mic: await icon(fa.FaMicrophoneAlt, "FFFFFF"),
    cut: await icon(fa.FaCut, "FFFFFF"),
    bulb: await icon(fa.FaLightbulb, "FFFFFF"),
    file: await icon(fa.FaFileAlt, "FFFFFF"),
    search: await icon(fa.FaSearch, "FFFFFF"),
    robot: await icon(fa.FaBrain, "FFFFFF"),
    user: await icon(fa.FaUserGraduate, "FFFFFF"),
    ear: await icon(fa.FaDeaf, "FFFFFF"),
    font: await icon(fa.FaFont, "FFFFFF"),
    adjust: await icon(fa.FaAdjust, "FFFFFF"),
    mask: await icon(fa.FaUserSecret, "FFFFFF"),
    lock: await icon(fa.FaLock, "FFFFFF"),
    scale: await icon(fa.FaBalanceScale, "FFFFFF"),
    flask: await icon(fa.FaFlask, "FFFFFF"),
    users: await icon(fa.FaUsers, "FFFFFF"),
  };
  const circleIcon = (s, data, x, y, d, fill, name) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + " circle" });
    s.addImage({ data, x: x + d * 0.24, y: y + d * 0.24, w: d * 0.52, h: d * 0.52, objectName: name + " icon", altText: name });
  };

  // 1 — Title
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "Dark title", sectionTitle: "Opening" });
  s.addText("TakeTheFloor", { placeholder: "title" });
  s.addText("See who held the floor, who got cut off, and whose ideas got credited to someone else — then coach the next sentence.", { placeholder: "body" });
  circleIcon(s, I.mic, 0.6, 0.55, 0.8, HEX.accent2, "Microphone");
  s.addText("Shermaine Yap Shi Min · Asia Pacific University (APU), Malaysia\n305 EmpowHER Edition October 2026 · Analytics Competition · Built with Gemma", { x: 0.6, y: 4.35, w: 8.8, h: 0.7, fontSize: 13, color: "CADCFC", margin: 0, isTextBox: true });
  s.addNotes("Hi, I'm Shermaine. TakeTheFloor makes the invisible dynamics of a meeting visible — airtime, interruptions and idea credit — and then gives each person private, practical leadership coaching. I'm competing in the Analytics path.");

  // 2 — Problem
  pres.addSection({ title: "Problem" });
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Problem" });
  s.addText("Leadership is won or lost in meetings", { placeholder: "title" });
  const probs = [
    [I.mic, HEX.accent1, "Uneven airtime", "In mixed groups, women's share of speaking time often falls below their share of seats unless group rules change.", "Karpowitz, Mendelberg & Shaker, APSR 2012"],
    [I.cut, HEX.accent2, "Who gets cut off", "Experimental work found people interrupted women more often than men.", "Hancock & Rubin, JLSP 2015"],
    [I.bulb, HEX.accent5, "Credit goes missing", "Someone repeats your idea and gets the credit. White House staffers fought back with “amplification”.", "Washington Post, 2016"],
  ];
  probs.forEach(([ic, col, h, b, cite], k) => {
    const x = 0.5 + k * 3.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.3, w: 2.85, h: 3.55, rectRadius: 0.12, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `Problem card ${k + 1}` });
    circleIcon(s, ic, x + 0.25, 1.55, 0.7, col, h);
    s.addText(h, { x: x + 0.25, y: 2.4, w: 2.4, h: 0.55, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(b, { x: x + 0.25, y: 3.0, w: 2.4, h: 1.25, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
    s.addText(cite, { x: x + 0.25, y: 4.35, w: 2.4, h: 0.35, fontSize: 10, italic: true, color: "6B6880", margin: 0, isTextBox: true });
  });
  s.addNotes("Three well-documented patterns decide who looks like a leader. Uneven airtime, interruptions that land more on women, and ideas that lose their author. None of these show up in meeting notes. TakeTheFloor measures all three.");

  // 3 — The moment
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Problem" });
  s.addText("The moment TakeTheFloor catches", { placeholder: "title" });
  const beats = [
    ["01:29", "Aisha", "“What if we launch a student tier at half the price of the pro plan, verified with a student email…”", HEX.accent1, "Mark cuts her off: “Let's not overcomplicate it.”"],
    ["03:29", "Mark", "“What if we did a discounted tier for students, verified with a student email, priced at half the pro plan?”", HEX.accent6, "Same idea, two minutes later."],
    ["03:40", "Daniel", "“Great idea, Mark.” … “Let's go with Mark's pricing plan.”", HEX.accent5, "Credit goes to the wrong person."],
  ];
  beats.forEach(([t, who, q, col, note], k) => {
    const y = 1.25 + k * 1.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 1.25, h: 1.0, rectRadius: 0.1, fill: { color: col }, line: { color: col }, objectName: `Beat ${k + 1} time` });
    s.addText([{ text: t, options: { fontSize: 22, bold: true, breakLine: true } }, { text: who, options: { fontSize: 13 } }], { x: 0.5, y, w: 1.25, h: 1.0, align: "center", valign: "middle", color: C.background1, margin: 0, isTextBox: true });
    s.addText(q, { x: 1.95, y, w: 5.0, h: 1.0, fontSize: 14, italic: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    s.addText(note, { x: 7.15, y, w: 2.35, h: 1.0, fontSize: 13, bold: true, color: col === HEX.accent5 ? C.accent5 : C.text2, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText("Synthetic demo meeting — all people are fictional.", { x: 0.5, y: 4.95, w: 6, h: 0.25, fontSize: 10, italic: true, color: "6B6880", margin: 0, isTextBox: true });
  s.addNotes("Here's the pattern in one demo meeting. Aisha proposes a student tier and gets cut off. Two minutes later Mark pitches the same idea almost word for word, and Daniel says 'Great idea, Mark — let's go with Mark's pricing plan.' TakeTheFloor flags this automatically with the exact quotes and timestamps.");

  // 4 — Solution flow
  pres.addSection({ title: "Solution" });
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Solution" });
  s.addText("From transcript to coaching in seconds", { placeholder: "title" });
  const steps = [
    [I.file, HEX.accent6, "1  Drop in a transcript", "Zoom/Teams/Meet .vtt, Otter, or plain “Name: text”."],
    [I.search, HEX.accent1, "2  Transparent detectors", "Airtime, cut-offs & overlaps, Hedge Index, idea-credit tracking — every flag shows the quotes."],
    [I.robot, HEX.accent2, "3  Gemma judges context", "Tells interruptions from “mm-hmm” and “yes, and…”, titles ideas, writes the recap."],
    [I.user, HEX.accent3, "4  Private coaching", "Strengths, next moves, word-for-word scripts and rewrites of your own hedged sentences."],
  ];
  steps.forEach(([ic, col, h, b], k) => {
    const x = 0.5 + k * 2.3;
    circleIcon(s, ic, x + 0.65, 1.35, 0.8, col, h);
    s.addText(h, { x, y: 2.35, w: 2.1, h: 0.6, fontSize: 16, bold: true, color: C.text1, align: "center", valign: "top", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(b, { x, y: 3.0, w: 2.1, h: 1.5, fontSize: 14, color: C.text1, align: "center", valign: "top", margin: 0, isTextBox: true });
    if (k < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 1.65, y: 1.6, w: 0.5, h: 0.3, fill: { color: "C9C5DA" }, line: { color: "C9C5DA" }, objectName: `Arrow ${k + 1}` });
  });
  s.addNotes("The flow is simple. Upload a transcript. Deterministic detectors find candidates and every flag carries its evidence. Gemma then adds judgement — it separates real interruptions from backchannels and supportive overlap, names each idea and writes the recap. Finally every person gets private coaching built from their own words.");

  // 5 — Demo screenshot
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Solution" });
  s.addText("Live demo: the dashboard", { placeholder: "title" });
  s.addImage({ path: SHOTS + "crop_overview.png", x: 0.5, y: 1.15, w: 4.6, h: 3.92, objectName: "Dashboard screenshot", altText: "TakeTheFloor overview: Floor Health 38/100, 4 interruptions, 1 idea credited to the wrong person, and the credit-drift card with quotes." });
  const callouts = [
    ["38/100", "Floor Health for the product-launch meeting (healthy stand-up scores 86)"],
    ["47%", "of airtime held by one person — 2.3× a fair share"],
    ["4", "real interruptions — the “mm-hmm” and the “yes, and…” are not counted"],
  ];
  callouts.forEach(([big, small], k) => {
    const y = 1.2 + k * 1.3;
    s.addText(big, { x: 5.45, y, w: 4.05, h: 0.6, fontSize: 36, bold: true, color: C.accent1, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(small, { x: 5.45, y: y + 0.6, w: 4.05, h: 0.6, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("Switch to the live app now. Show: Overview metrics and the credit-drift card; Floor timeline with interruption markers; Interruptions tab showing a backchannel kept separate; Idea credit; Leadership coach for Aisha; Accessible recap; then toggle the dyslexia-friendly font and high contrast.");

  // 6 — Coach screenshot
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Solution" });
  s.addText("Coaching that turns data into leadership", { placeholder: "title" });
  s.addImage({ path: SHOTS + "crop_coach.png", x: 4.9, y: 1.15, w: 4.6, h: 3.92, objectName: "Coach screenshot", altText: "Private leadership coach for Aisha: talk time 13%, cut off twice, one idea credited away, with strengths, moves and scripts." });
  s.addText([
    { text: "Private by design", options: { bold: true, breakLine: true } },
    { text: "Each person gets their own notes — never a public ranking.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Grounded in evidence", options: { bold: true, breakLine: true } },
    { text: "Every strength and move cites what happened in this meeting.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Words you can use tomorrow", options: { bold: true, breakLine: true } },
    { text: "“I'd like to finish my point, then I'd love to hear yours.”", options: { italic: true, breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 6 } },
    { text: "Facilitator tips too", options: { bold: true, breakLine: true } },
    { text: "Round-robins, a “let them land” norm, naming idea owners in notes.", options: {} },
  ], { x: 0.5, y: 1.2, w: 4.1, h: 3.85, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  s.addNotes("Data alone doesn't change behaviour, so the coach turns it into moves. Notes are private to each person, grounded in this meeting, and include word-for-word scripts. Facilitators get structural fixes, because the goal is to change the meeting, not blame individuals.");

  // 7 — Analytics evidence
  pres.addSection({ title: "Evidence" });
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Evidence" });
  s.addText("Validated against labelled meetings", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [{ name: "Floor Health", labels: ["Product launch", "Project group", "Stand-up (control)"], values: [38, 64, 86] }], {
    x: 0.5, y: 1.15, w: 4.9, h: 3.0, barDir: "bar", chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1,
    showTitle: true, title: "Floor Health (0–100, higher is healthier)", titleFontSize: 13, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", catAxisLabelColor: "52514E", valAxisLabelColor: "52514E", catAxisLabelFontSize: 12, valAxisLabelFontSize: 10,
    valAxisMaxVal: 100, valAxisMinVal: 0, valGridLine: { color: "E4E3DF", size: 0.75 }, catGridLine: { style: "none" }, showLegend: false, catAxisOrientation: "maxMin",
    objectName: "Floor Health chart", altText: "Floor Health: product launch 38, project group 64, healthy stand-up 86.",
  });
  const ev = [["5 / 5", "planted interruptions found"], ["4 / 4", "idea-credit events found"], ["0", "false alarms, incl. the healthy control"], ["0.20–0.70", "stable similarity range (sensitivity sweep)"]];
  ev.forEach(([big, small], k) => {
    const x = 5.75 + (k % 2) * 1.9, y = 1.2 + Math.floor(k / 2) * 1.5;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.75, h: 1.3, rectRadius: 0.1, fill: { color: C.background2 }, line: { color: C.background2 }, objectName: `Stat ${k + 1}` });
    s.addText(big, { x: x + 0.1, y: y + 0.1, w: 1.55, h: 0.55, fontSize: k === 3 ? 18 : 24, bold: true, color: C.accent1, align: "center", valign: "middle", margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(small, { x: x + 0.1, y: y + 0.65, w: 1.55, h: 0.6, fontSize: 11, color: C.text1, align: "center", valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("Honest scope: three synthetic, hand-labelled meetings test that the detectors behave as designed — not real-world accuracy. Full method, sensitivity analysis and limitations are in the Kaggle notebook.", { x: 0.5, y: 4.3, w: 9.0, h: 0.75, fontSize: 12, italic: true, color: "52514E", margin: 0, isTextBox: true });
  s.addNotes("This is the analytics core. I wrote three meetings with hand labels, including a healthy control. The detectors find every planted interruption and credit event with zero false alarms, and the healthy stand-up scores highest. A sensitivity sweep shows results are stable across a wide threshold range. I'm explicit that this proves the method behaves as designed, not real-world accuracy — that's the next step.");

  // 8 — Accessibility
  pres.addSection({ title: "Impact" });
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Impact" });
  s.addText("Accessible by design, not by checkbox", { placeholder: "title" });
  const acc = [
    [I.ear, HEX.accent6, "Plain-language recap", "Decisions, owners and open questions for Deaf/HoH, neurodivergent and second-language teammates."],
    [I.font, HEX.accent1, "Readable everywhere", "Atkinson Hyperlegible font, larger text and high-contrast modes."],
    [I.adjust, HEX.accent3, "Never colour-alone", "Colour-blind-safe palette, names on every chart, text summaries and table views."],
    [I.mask, HEX.accent2, "Safe to share", "One-click anonymised names; captions tab writes every event out in words."],
  ];
  acc.forEach(([ic, col, h, b], k) => {
    const x = 0.5 + (k % 2) * 4.6, y = 1.25 + Math.floor(k / 2) * 1.85;
    circleIcon(s, ic, x, y + 0.05, 0.7, col, h);
    s.addText(h, { x: x + 0.9, y, w: 3.5, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    s.addText(b, { x: x + 0.9, y: y + 0.5, w: 3.5, h: 1.05, fontSize: 14, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("The EmpowHER theme is accessibility and leadership development. Accessibility here is a feature: a plain-language recap for people who couldn't follow the meeting live, readable font and contrast modes, charts that never rely on colour, and anonymised sharing.");

  // 9 — Ethics + roadmap
  s = pres.addSlide({ masterName: "Light content", sectionTitle: "Impact" });
  s.addText("Responsible by default, ready to grow", { placeholder: "title" });
  const cols = [
    ["Ethics & privacy", [[I.lock, "Rules-only or local Gemma (Ollama): transcripts stay on-device"], [I.scale, "Describes one meeting, never grades a person"], [I.users, "Overlap norms differ by culture — every flag shows evidence"]]],
    ["What's next", [[I.flask, "Validate on the AMI Meeting Corpus and real team meetings"], [I.mic, "Live mode: nudge the facilitator during the call"], [I.bulb, "“Amplify” button: credit a colleague's idea in one tap"]]],
  ];
  cols.forEach(([h, items], c) => {
    const x = 0.5 + c * 4.6;
    s.addText(h, { x, y: 1.2, w: 4.3, h: 0.45, fontSize: 20, bold: true, color: C.text2, margin: 0, isTextBox: true, fontFace: THEME.headFontFace });
    items.forEach(([ic, t], k) => {
      const y = 1.85 + k * 1.05;
      circleIcon(s, ic, x, y, 0.6, c === 0 ? HEX.dk2 : HEX.accent2, t.slice(0, 20));
      s.addText(t, { x: x + 0.8, y: y - 0.05, w: 3.5, h: 0.75, fontSize: 14, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    });
  });
  s.addNotes("Two commitments: privacy and fairness. You can run it fully offline or with a local Gemma. It describes a meeting, not a person, and always shows evidence. Next I want to validate on the AMI corpus, add a live facilitator nudge, and an Amplify button to credit colleagues in one tap.");

  // 10 — Close
  pres.addSection({ title: "Close" });
  s = pres.addSlide({ masterName: "Dark title", sectionTitle: "Close" });
  s.addText("Make the invisible visible", { placeholder: "title" });
  s.addText("TakeTheFloor helps every voice get heard — and get the credit.", { placeholder: "body" });
  s.addText([
    { text: "Code & README: github.com/ShermaineYap/305-EmpowHER-Edition-October-2026", options: { breakLine: true } },
    { text: "Analysis: notebooks/takethefloor_meeting_equity.ipynb (Kaggle)", options: { breakLine: true } },
    { text: "AI used: Gemma (in-app analysis); Claude (coding assistant) — cited in README", options: {} },
  ], { x: 0.6, y: 3.95, w: 8.8, h: 1.1, fontSize: 13, color: "CADCFC", margin: 0, isTextBox: true });
  s.addNotes("Thank you. Everything is open source on GitHub with the Kaggle notebook. Happy to take questions.");

  const out = REPO + "/slides/TakeTheFloor_pitch_deck.pptx";
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
