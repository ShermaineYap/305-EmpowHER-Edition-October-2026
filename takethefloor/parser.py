"""Transcript parsing.

Accepts the formats people actually have on hand:

* WebVTT exports from Zoom / Teams / Google Meet (``<v Name>text`` or ``Name: text`` cues)
* ``[00:01:12] Name: text``  /  ``00:01:12 Name: text``  /  ``(01:12) Name: text``
* ``Name (00:01:12): text``  /  ``Name  00:01:12`` on its own line followed by text (Otter style)
* Plain ``Name: text`` lines with no timestamps (times are estimated from word count)

Everything is normalised into a list of :class:`Turn` objects sorted by start time,
with consecutive cues from the same speaker merged into a single turn.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

WORDS_PER_SECOND = 2.5  # ~150 wpm conversational speech


@dataclass
class Turn:
    idx: int
    speaker: str
    start: float  # seconds
    end: float  # seconds
    text: str
    flags: list[str] = field(default_factory=list)

    @property
    def words(self) -> int:
        return len(self.text.split())

    @property
    def duration(self) -> float:
        return max(self.end - self.start, 0.0)

    @property
    def stamp(self) -> str:
        return fmt_time(self.start)


def fmt_time(seconds: float) -> str:
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _to_seconds(stamp: str) -> float:
    stamp = stamp.strip().replace(",", ".")
    parts = stamp.split(":")
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return 0.0
    total = 0.0
    for n in nums:
        total = total * 60 + n
    return total


_TS = r"(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)"
_NAME = r"([A-Za-zÀ-ɏ][\w .'\-À-ɏ]{0,40}?)"

_VTT_CUE = re.compile(rf"^{_TS}\s*-->\s*{_TS}")
_VTT_VOICE = re.compile(r"^<v\s+([^>]+)>(.*?)(?:</v>)?$")
_BRACKET_LINE = re.compile(rf"^[\[(]?{_TS}[\])]?\s*[-–]?\s*{_NAME}\s*:\s*(.+)$")
_NAME_TS_LINE = re.compile(rf"^{_NAME}\s*[\[(]{_TS}[\])]\s*:?\s*(.*)$")
_OTTER_HEADER = re.compile(rf"^{_NAME}\s+{_TS}\s*$")
_PLAIN_LINE = re.compile(rf"^{_NAME}\s*:\s*(.+)$")
_NAME_IN_TEXT = re.compile(rf"^{_NAME}\s*:\s*(.+)$")


def _clean_speaker(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip(" -:")
    return name.title() if name.isupper() or name.islower() else name


def _parse_vtt(text: str) -> list[dict]:
    rows: list[dict] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = _VTT_CUE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        start, end = _to_seconds(m.group(1)), _to_seconds(m.group(2))
        i += 1
        body: list[str] = []
        while i < len(lines) and lines[i].strip():
            body.append(lines[i].strip())
            i += 1
        joined = " ".join(body)
        speaker = "Unknown"
        vm = _VTT_VOICE.match(joined)
        if vm:
            speaker, joined = vm.group(1), vm.group(2)
        else:
            nm = _NAME_IN_TEXT.match(joined)
            if nm and len(nm.group(1).split()) <= 4:
                speaker, joined = nm.group(1), nm.group(2)
        joined = re.sub(r"</?v[^>]*>", "", joined).strip()
        if joined:
            rows.append({"speaker": _clean_speaker(speaker), "start": start, "end": end, "text": joined})
    return rows


def _parse_lines(text: str) -> list[dict]:
    rows: list[dict] = []
    pending_header: tuple[str, float] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _BRACKET_LINE.match(line)
        if m:
            rows.append({"speaker": _clean_speaker(m.group(2)), "start": _to_seconds(m.group(1)), "end": None, "text": m.group(3).strip()})
            pending_header = None
            continue
        m = _NAME_TS_LINE.match(line)
        if m:
            if m.group(3).strip():
                rows.append({"speaker": _clean_speaker(m.group(1)), "start": _to_seconds(m.group(2)), "end": None, "text": m.group(3).strip()})
                pending_header = None
            else:
                pending_header = (_clean_speaker(m.group(1)), _to_seconds(m.group(2)))
            continue
        m = _OTTER_HEADER.match(line)
        if m:
            pending_header = (_clean_speaker(m.group(1)), _to_seconds(m.group(2)))
            continue
        if pending_header:
            rows.append({"speaker": pending_header[0], "start": pending_header[1], "end": None, "text": line})
            pending_header = None
            continue
        m = _PLAIN_LINE.match(line)
        if m and len(m.group(1).split()) <= 4:
            rows.append({"speaker": _clean_speaker(m.group(1)), "start": None, "end": None, "text": m.group(2).strip()})
            continue
        if rows:  # continuation line
            rows[-1]["text"] += " " + line
    return rows


def _fill_times(rows: list[dict]) -> None:
    clock = 0.0
    for r in rows:
        if r["start"] is None:
            r["start"] = clock
        clock = max(clock, r["start"]) + len(r["text"].split()) / WORDS_PER_SECOND
    for i, r in enumerate(rows):
        if r["end"] is None:
            est = r["start"] + max(len(r["text"].split()) / WORDS_PER_SECOND, 0.6)
            nxt = rows[i + 1]["start"] if i + 1 < len(rows) else None
            # A speaker cannot "finish" after the next person has spoken for long; the
            # estimate is capped slightly past the next start so overlaps stay visible.
            if nxt is not None and nxt >= r["start"]:
                est = min(est, max(nxt, r["start"] + 0.6))
            r["end"] = est


def parse_transcript(text: str, merge_gap: float = 1.5) -> list[Turn]:
    """Parse a transcript string into ordered, merged speaker turns."""
    text = text.replace("﻿", "")
    rows = _parse_vtt(text) if "-->" in text else _parse_lines(text)
    if not rows:
        raise ValueError(
            "Couldn't find any speaker lines. Expected lines like 'Name: text', "
            "'[00:01:12] Name: text', or a .vtt export."
        )
    _fill_times(rows)
    rows.sort(key=lambda r: r["start"])

    merged: list[dict] = []
    for r in rows:
        if merged and merged[-1]["speaker"] == r["speaker"] and r["start"] - merged[-1]["end"] <= merge_gap:
            merged[-1]["text"] += " " + r["text"]
            merged[-1]["end"] = max(merged[-1]["end"], r["end"])
        else:
            merged.append(dict(r))
    return [Turn(i, r["speaker"], float(r["start"]), float(r["end"]), r["text"]) for i, r in enumerate(merged)]
