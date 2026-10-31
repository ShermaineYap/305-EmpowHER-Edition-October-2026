"""Gemma integration.

Backends (chosen automatically, in this order):

* ``google`` – Gemma on the Gemini API / Google AI Studio (``GEMINI_API_KEY`` or ``GOOGLE_API_KEY``).
  Tries the fast mixture-of-experts ``gemma-4-26b-a4b-it`` first, then falls back to ``gemma-4-31b-it``.
* ``ollama`` – a local Gemma via Ollama (``OLLAMA_HOST``, default model ``gemma3:4b``) so a meeting
  transcript never has to leave the laptop.
* ``offline`` – deterministic rules only. The app still works end to end; results are labelled as rule-based.

Every Gemma call returns JSON that is validated and merged over the rule-based result, so a slow,
rate-limited or malformed model response degrades gracefully instead of breaking a live demo.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time

DEFAULT_GOOGLE_MODELS = ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]
DEFAULT_OLLAMA_MODEL = "gemma3:4b"
MAX_TRANSCRIPT_CHARS = 14000
SYSTEM = "You are a fast, careful JSON API for meeting analysis. Do not deliberate at length. Output only the requested JSON."
CACHE_FILE = os.path.join(os.path.dirname(__file__), "gemma_cache.json")
_DISK_CACHE: dict | None = None


def _disk_cache() -> dict:
    global _DISK_CACHE
    if _DISK_CACHE is None:
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                _DISK_CACHE = json.load(f)
        except (OSError, json.JSONDecodeError):
            _DISK_CACHE = {}
    return _DISK_CACHE


class GemmaClient:
    def __init__(self, api_key: str | None = None, backend: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.ollama_host = os.getenv("OLLAMA_HOST")
        # Demo-cache replay is allowed unless the user explicitly chose rules-only (backend="offline").
        self.allow_cache = backend != "offline"
        self.backend = backend or ("google" if self.api_key else "ollama" if self.ollama_host else "offline")
        self.models = [model] if model else (DEFAULT_GOOGLE_MODELS if self.backend == "google" else [os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)])
        self.active_model: str | None = None
        self.cache_hits = 0
        self.live_calls = 0
        self.last_error: str | None = None
        self._client = None
        if self.backend == "google":
            try:
                from google import genai

                from google.genai import types

                self._client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=150_000))
            except Exception as exc:  # pragma: no cover - import/env failure
                self.last_error = f"google-genai unavailable: {exc}"
                self.backend = "offline"

    @property
    def live(self) -> bool:
        return self.backend != "offline"

    @property
    def enabled(self) -> bool:
        return self.live or (self.allow_cache and bool(_disk_cache()))

    @property
    def label(self) -> str:
        if self.cache_hits and not self.live_calls:
            return f"Gemma · {self.active_model or 'gemma-4'} · replayed from a recorded live run (demo meeting)"
        if not self.live:
            return "Rules only (offline)"
        return f"Gemma · {self.active_model or self.models[0]} · {'Google AI Studio' if self.backend == 'google' else 'local Ollama'}"

    # ------------------------------------------------------------------ transport
    def generate(self, prompt: str, temperature: float = 0.2) -> str | None:
        if not self.enabled:
            return None
        return _cached_generate(self, _hash(prompt), prompt, temperature)

    def _raw_generate(self, prompt: str, temperature: float) -> str | None:
        models = [self.active_model] + [m for m in self.models if m != self.active_model] if self.active_model else self.models
        for model in models:
            for attempt in range(2):
                try:
                    if self.backend == "google":
                        from google.genai import types

                        resp = self._client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(temperature=temperature, max_output_tokens=8192, system_instruction=SYSTEM),
                        )
                        text = resp.text
                    else:
                        import urllib.request

                        body = json.dumps({"model": model, "system": SYSTEM, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}).encode()
                        req = urllib.request.Request(self.ollama_host.rstrip("/") + "/api/generate", body, {"Content-Type": "application/json"})
                        with urllib.request.urlopen(req, timeout=120) as r:
                            text = json.loads(r.read())["response"]
                    if text:
                        self.active_model = model
                        self.last_error = None
                        return text
                except Exception as exc:
                    self.last_error = f"{model}: {exc}"
                    msg = str(exc).lower()
                    if any(k in msg for k in ("not found", "404", "not supported", "500", "internal", "invalid")):
                        break  # try the next model straight away
                    time.sleep(1.5 * (attempt + 1))
        return None

    def generate_json(self, prompt: str):
        text = self.generate(prompt)
        return extract_json(text) if text else None


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _cached_generate(client: GemmaClient, key: str, prompt: str, temperature: float):
    """In-memory cache, then the committed disk cache of real Gemma runs (demo meetings), then a live call."""
    cache = client.__dict__.setdefault("_cache", {})
    if key in cache:
        return cache[key]
    disk = _disk_cache()
    if key in disk and os.getenv("TTF_NO_CACHE") != "1":
        client.cache_hits += 1
        cache[key] = disk[key]["text"]
        client.active_model = client.active_model or disk[key].get("model")
        return cache[key]
    if not client.live:
        return None
    out = client._raw_generate(prompt, temperature)
    if out is None:
        return None
    client.live_calls += 1
    cache[key] = out
    if os.getenv("TTF_WRITE_CACHE") == "1":
        disk[key] = {"model": client.active_model, "text": out}
    return out


def save_disk_cache() -> int:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(_disk_cache(), f, indent=1, ensure_ascii=False)
    return len(_disk_cache())


def extract_json(text: str):
    """Pull the first JSON object/array out of a model response (handles ```json fences and chatter)."""
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1)
    pairs = sorted((("{", "}"), ("[", "]")), key=lambda p: (text.find(p[0]) == -1, text.find(p[0])))
    for opener, closer in pairs:
        start = text.find(opener)
        if start == -1:
            continue
        depth, in_str, esc = 0, False, False
        for k in range(start, len(text)):
            ch = text[k]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : k + 1])
                    except json.JSONDecodeError:
                        cleaned = re.sub(r",\s*([}\]])", r"\1", text[start : k + 1])
                        try:
                            return json.loads(cleaned)
                        except json.JSONDecodeError:
                            break
    return None


def transcript_for_prompt(turns, limit: int = MAX_TRANSCRIPT_CHARS) -> str:
    lines = [f"[{t.stamp}] {t.speaker}: {t.text}" for t in turns]
    out = "\n".join(lines)
    if len(out) <= limit:
        return out
    head, tail = out[: limit // 2], out[-limit // 2 :]
    return head + "\n[... middle of meeting omitted for length ...]\n" + tail


# ---------------------------------------------------------------------- prompts
INTERRUPTION_PROMPT = """You are a careful conversation analyst. For each numbered moment below, a speaker change happened while the previous speaker may still have been talking.
Classify each moment as exactly one of:
- "interruption": the new speaker took the floor away or changed direction before the previous speaker finished.
- "supportive": a cooperative overlap that agrees with and builds on the previous speaker's point.
- "backchannel": a short acknowledgement ("mm-hmm", "right") that does not take the floor.
Be fair: do not call it an interruption if the previous speaker had clearly finished.

{items}

Reply with ONLY a JSON array, one object per moment, like:
[{{"id": 1, "label": "interruption", "reason": "one short sentence"}}]"""

RECAP_PROMPT = """You write accessible meeting recaps for people who are Deaf or hard of hearing, neurodivergent, reading in a second language, or who missed the meeting.
Use plain language (short sentences, everyday words, about a Grade 7 reading level). Name who said what. Do not invent facts that are not in the transcript.

TRANSCRIPT:
{transcript}

IDEAS TO SUMMARISE (give each a short 4-10 word title):
{ideas}

Reply with ONLY JSON in this exact shape:
{{"summary": ["3-5 short plain-language sentences"],
  "decisions": ["each decision made, with who proposed it"],
  "action_items": [{{"owner": "name", "task": "what", "due": "when or empty"}}],
  "open_questions": ["anything left unresolved"],
  "idea_titles": {{"1": "short title"}}}}"""

COACH_PROMPT = """You are a warm, direct leadership coach who helps people (especially women and people from under-represented groups) claim space in meetings without becoming aggressive.
Coach {name} using ONLY the evidence below from one meeting. Be specific, kind and practical. Quote their own words when useful.

EVIDENCE FOR {name}:
- Share of speaking time: {share:.0%} (fair share in this meeting would be {fair:.0%})
- Turns taken: {turns}; average turn length: {avg_words:.0f} words
- Hedge Index: {hedge:.1f} hedges per 100 words (team median {hedge_median:.1f})
- Times interrupted by others: {interrupted}; times they interrupted others: {interrupter}
- Ideas of theirs later credited to someone else: {drifted}
- Ideas of others they restated without naming the originator: {echoed}
- Hedged sentences they said:
{hedged}

Reply with ONLY JSON:
{{"headline": "one encouraging sentence summarising their meeting presence",
  "strengths": ["3 specific strengths grounded in the evidence"],
  "moves": ["3 concrete leadership moves for the next meeting, each starting with a verb"],
  "scripts": ["2-3 short phrases they can say word-for-word in the moment"],
  "rewrites": [{{"original": "their exact hedged sentence", "rewrite": "a confident version that keeps their meaning and stays polite"}}]}}"""


def label_interruptions(client: GemmaClient, events: list[dict], turns) -> list[dict]:
    if not client.enabled or not events:
        return events
    by_idx = {t.idx: t for t in turns}
    items = []
    for n, e in enumerate(events, 1):
        prev = by_idx.get(e["turn_idx"] - 1)
        nxt = by_idx.get(e["turn_idx"] + 1)
        items.append(
            f"#{n}\n  {e['interrupted']}: \"{prev.text[-220:] if prev else e['cut_text']}\"\n"
            f"  {e['interrupter']}: \"{e['taking_text']}\"\n"
            + (f"  then {nxt.speaker}: \"{nxt.text[:120]}\"" if nxt else "")
        )
    data = client.generate_json(INTERRUPTION_PROMPT.format(items="\n".join(items)))
    if not isinstance(data, list):
        return events
    for row in data:
        try:
            k = int(row.get("id")) - 1
            label = str(row.get("label", "")).lower().strip()
        except (TypeError, ValueError, AttributeError):
            continue
        if 0 <= k < len(events) and label in {"interruption", "supportive", "backchannel"}:
            events[k]["rule_label"] = events[k]["label"]
            events[k]["label"] = label
            events[k]["reason"] = str(row.get("reason") or events[k]["reason"])[:240]
            events[k]["labeled_by"] = "gemma"
    return events


def recap(client: GemmaClient, turns, credit_events: list[dict]):
    if not client.enabled:
        return None
    ideas = "\n".join(f"{n}. {e['originator']} at {_fmt(e['original_time'])}: \"{e['original_text'][:220]}\"" for n, e in enumerate(credit_events, 1)) or "(none)"
    data = client.generate_json(RECAP_PROMPT.format(transcript=transcript_for_prompt(turns), ideas=ideas))
    if not (isinstance(data, dict) and data.get("summary")):
        return None
    for k in ("summary", "decisions", "open_questions"):
        v = data.get(k) or []
        if isinstance(v, str):
            v = [x.strip() for x in re.split(r"(?<=[.!?])\s+", v) if x.strip()]
        data[k] = [str(x) if not isinstance(x, dict) else "; ".join(str(y) for y in x.values()) for x in v]
    items = data.get("action_items") or []
    data["action_items"] = [a if isinstance(a, dict) else {"owner": "", "task": str(a), "due": ""} for a in items]
    data["idea_titles"] = {str(k): str(v) for k, v in (data.get("idea_titles") or {}).items()} if isinstance(data.get("idea_titles"), dict) else {}
    return data


def coach(client: GemmaClient, evidence: dict):
    if not client.enabled:
        return None
    hedged = "\n".join(f'  * "{s}"' for s in evidence["hedged_sentences"][:6]) or "  (none)"
    prompt = COACH_PROMPT.format(hedged=hedged, **{k: v for k, v in evidence.items() if k != "hedged_sentences"})
    data = client.generate_json(prompt)
    if not (isinstance(data, dict) and data.get("moves")):
        return None
    for k in ("strengths", "moves", "scripts"):
        v = data.get(k) or []
        data[k] = [v] if isinstance(v, str) else [str(x) for x in v]
    data["rewrites"] = [r for r in (data.get("rewrites") or []) if isinstance(r, dict) and r.get("original") and r.get("rewrite")]
    data["headline"] = str(data.get("headline") or "")
    return data


def _fmt(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"
