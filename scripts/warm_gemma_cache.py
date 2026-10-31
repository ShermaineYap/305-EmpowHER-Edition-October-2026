"""Runs real Gemma over the three demo meetings (analysis + every person's coaching) and stores
the raw responses in takethefloor/gemma_cache.json, so the live demo shows genuine Gemma output
instantly. Uploaded transcripts are never served from this cache (their prompts differ).

    GEMINI_API_KEY=... TTF_WRITE_CACHE=1 python scripts/warm_gemma_cache.py
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["TTF_WRITE_CACHE"] = "1"

from takethefloor import analyze, parse_transcript  # noqa: E402
from takethefloor.analysis import coach  # noqa: E402
from takethefloor.gemma import GemmaClient, save_disk_cache  # noqa: E402

DEMOS = ["demo_product_launch.vtt", "demo_study_group.txt", "demo_balanced_standup.txt"]


def warm(name: str) -> str:
    text = (ROOT / "data" / name).read_text(encoding="utf-8")
    client = GemmaClient()
    t0 = time.time()
    r = analyze(parse_transcript(text), client=client, timestamps_real="standup" not in name)
    with ThreadPoolExecutor(3) as pool:
        srcs = list(pool.map(lambda s: coach(r, s, client)[1], r["speakers"]))
    labelled = sum(e["labeled_by"] == "gemma" for e in r["interruptions"])
    return f"{name}: recap={r['recap_source']} interruptions_gemma={labelled}/{len(r['interruptions'])} coach={srcs} ({time.time() - t0:.0f}s, {client.last_error})"


if __name__ == "__main__":
    with ThreadPoolExecutor(3) as pool:
        for line in pool.map(warm, DEMOS):
            print(line)
    print("cached responses:", save_disk_cache())
