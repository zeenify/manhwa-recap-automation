"""tts_generate — read the narration script, synthesize each entry via fish.audio,
measure durations, and write the timing file the assembler syncs to.

Usage: python tools/tts_generate.py --script scripts/ch01_script.md --out-dir audio/ch001
Idempotent: skips entries whose mp3 already exists (safe to re-run).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KEY_FILE = Path(os.environ.get("FISH_API_KEY_FILE", "tmp/fish_api_key.txt"))
API_URL = os.environ.get("FISH_API_URL", "https://api.fish.audio/v1/tts")
REFERENCE_ID = os.environ.get("FISH_VOICE_ID", "ec47a6d54dbe4e1481f66e1d6a94b849")
MODEL = os.environ.get("FISH_MODEL", "s2.1-pro-free")


def parse_script(path: Path):
    text = path.read_text(encoding="utf-8")
    blocks = re.split(r"\n(?=### )", text)
    entries = []
    for b in blocks:
        if not b.startswith("### "):
            continue
        header = b.split("\n", 1)[0]
        # narration ends at a --- rule, any ##/### section header, or the block end —
        # a bare "## MAIN SCRIPT"/"## OUTRO" header after an entry must never leak
        # into the TTS text (it was literally spoken as "hash hash main script")
        m_narr = re.search(r"NARRATION:\n(.*?)(?=\n---|\n## |\n### |\Z)", b, re.S)
        if not m_narr:
            continue
        raw = m_narr.group(1).strip()
        stripped = [ln.strip()[:60] for ln in raw.splitlines()
                    if ln.lstrip().startswith("#") or "SHOT:" in ln or "NARRATION:" in ln]
        if stripped or "*" in raw:
            print(f"STRIPPED leak markers from {header}: {stripped or ['asterisk(s)']}",
                  file=sys.stderr)
        kept = [ln for ln in raw.splitlines() if not ln.lstrip().startswith("#")]
        narration = " ".join(" ".join(kept).split()).replace("*", "")
        if "#" in narration or "SHOT:" in narration or "NARRATION:" in narration:
            print(f"DIRTY narration after cleanup, refusing to synthesize: {header}",
                  file=sys.stderr)
            sys.exit(1)
        beats = []
        m_beat = re.search(r"BEAT (\d+)", header)
        if m_beat:
            first = int(m_beat.group(1))
            m_cov = re.search(r"covers (\d+)[–-](\d+)", header)
            if m_cov:
                beats = list(range(int(m_cov.group(1)), int(m_cov.group(2)) + 1))
            else:
                beats = [first]
        m_cold = re.search(r"from beat (\d+)", header)
        if not beats and m_cold:
            beats = [int(m_cold.group(1))]
        if not beats:
            print(f"SKIP (no beat ref): {header}", file=sys.stderr)
            continue
        title = re.sub(r"^### (BEAT \d+|COLD OPEN)[^—]*—?\s*", "", header).strip() or header
        entries.append({"beats": beats, "title": title, "narration": narration})
    return entries


def tts(text: str, out: Path, key: str) -> bool:
    body = json.dumps({"text": text, "reference_id": REFERENCE_ID, "format": "mp3"})
    for attempt in range(4):
        r = subprocess.run([
            "curl", "-sS", "-X", "POST", API_URL,
            "-H", f"Authorization: Bearer {key}",
            "-H", "Content-Type: application/json",
            "-H", f"model: {MODEL}",
            "-d", body, "--output", str(out),
            "-w", "%{http_code}",
        ], capture_output=True, text=True)
        code = r.stdout.strip()
        if code == "200" and out.exists() and out.stat().st_size > 1000:
            return True
        wait = 5 * (attempt + 1)
        print(f"  retry in {wait}s (HTTP {code}, size {out.stat().st_size if out.exists() else 0})", file=sys.stderr)
        time.sleep(wait)
    return False


def duration(path: Path) -> float:
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path),
    ], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="scripts/ch01_script.md")
    ap.add_argument("--out-dir", default="audio/ch001")
    ap.add_argument("--workers", type=int, default=4,
                    help="parallel TTS requests (1 = sequential, the old behavior)")
    args = ap.parse_args()

    key = KEY_FILE.read_text(encoding="utf-8").strip()
    entries = parse_script(Path(args.script))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"{len(entries)} entries to synthesize (workers={args.workers})")

    # pass 1: figure out what still needs synthesizing (idempotent skip)
    jobs, files = [], []
    for i, e in enumerate(entries):
        f = out_dir / f"entry_{i:03d}_{e['beats'][0]:04d}.mp3"
        files.append(f)
        if not (f.exists() and f.stat().st_size > 1000):
            jobs.append((i, e, f))

    # pass 2: synthesize missing clips, up to --workers at a time
    if jobs:
        def run(job):
            i, e, f = job
            ok = tts(e["narration"], f, key)
            return i, ok
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for i, ok in pool.map(run, jobs):
                if not ok:
                    print(f"FAILED entry {i} beats {entries[i]['beats']}", file=sys.stderr)
                    sys.exit(1)
                print(f"[{i+1}/{len(entries)}] synthesized beats {entries[i]['beats']}")

    # pass 3: measure durations in order, write the timing contract
    timing = {"reference_id": REFERENCE_ID, "model": MODEL, "entries": []}
    for i, e in enumerate(entries):
        f = files[i]
        dur = duration(f)
        timing["entries"].append({
            "beats": e["beats"], "file": str(f).replace("\\", "/"),
            "duration_s": round(dur, 3), "words": len(e["narration"].split()),
            "title": e["title"],
        })
        print(f"[{i+1}/{len(entries)}] beats {e['beats']} -> {dur:.1f}s")

    timing["total_duration_s"] = round(sum(t["duration_s"] for t in timing["entries"]), 2)
    (out_dir / "timing.json").write_text(json.dumps(timing, indent=1), encoding="utf-8")
    print(json.dumps({"total_duration_s": timing["total_duration_s"],
                      "entries": len(timing["entries"])}))


if __name__ == "__main__":
    main()
