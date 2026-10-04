"""tts_generate — read the narration script, synthesize each entry via fish.audio,
measure durations, and write the timing file the assembler syncs to.

Usage: python tools/tts_generate.py --script scripts/a-wimps-strategy-guide/ch001_script.md --out-dir audio/a-wimps-strategy-guide/ch001
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
MODEL = os.environ.get("FISH_MODEL", "s2.1-pro-free")

# Named channel voices — swap a series' voice by passing --voice <name>
# (a raw fish.audio reference_id also works and gets no prosody preset).
# "default" respects FISH_VOICE_ID from the environment if set.
VOICES = {
    "default": os.environ.get("FISH_VOICE_ID", "ec47a6d54dbe4e1481f66e1d6a94b849"),
    "mommy": "d8cc2855171e415591c06f0c8f0b9bf9",
}
# Prosody presets per voice (applied in post-processing — the API has no knobs).
VOICE_PRESETS = {
    "default": {"speed": 1.0, "gain": "0dB"},
    "mommy": {"speed": 1.07, "gain": "5dB"},
}


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


def tts(text: str, out: Path, key: str, voice: str) -> bool:
    body = json.dumps({"text": text, "reference_id": voice, "format": "mp3"})
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


def post_process(path: Path, speed: float, gain: str, pad_s: float) -> None:
    """Manual prosody knobs the fish.audio API lacks (verified 2026-10-04: the
    s2.1 endpoint silently ignores speed/volume fields — generation randomness
    masquerades as effect). Runs immediately after synthesis and BEFORE duration
    measurement, so the timing contract always reflects the final audio — the
    tail pad makes every beat's screen time include a natural pause between
    entries (user finding: back-to-back narration with zero gap sounds wrong).
    Idempotent: only ever touches freshly synthesized files — the skip-if-exists
    check runs before this, so processed files are never processed twice."""
    af = []
    if speed != 1.0:
        af.append(f"atempo={speed}")
    if gain and gain != "0dB":
        af.append(f"volume={gain}")
        af.append("alimiter=limit=0.95:level=false")
    if pad_s > 0:
        af.append(f"apad=pad_dur={pad_s}")
    if not af:
        return
    tmp = path.with_suffix(".tmp.mp3")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(path), "-af", ",".join(af),
                        "-c:a", "libmp3lame", "-q:a", "2", str(tmp)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 1000:
        print(r.stderr[-500:], file=sys.stderr)
        raise SystemExit(f"post-process failed: {path}")
    tmp.replace(path)


def duration(path: Path) -> float:
    r = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", str(path),
    ], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="scripts/a-wimps-strategy-guide/ch001_script.md")
    ap.add_argument("--out-dir", default="audio/a-wimps-strategy-guide/ch001")
    ap.add_argument("--workers", type=int, default=4,
                    help="parallel TTS requests (1 = sequential, the old behavior)")
    ap.add_argument("--voice", default="default",
                    help="voice NAME from VOICES ('default', 'mommy', ...) or a raw fish.audio reference_id")
    ap.add_argument("--speed", type=float, default=None,
                    help="override the voice preset's tempo factor, e.g. 1.07")
    ap.add_argument("--gain", default=None,
                    help="override the voice preset's loudness lift, e.g. 5dB")
    ap.add_argument("--pad", type=float, default=0.4,
                    help="seconds of tail silence padded onto every entry (breathing room "
                         "between beats; included in the timing contract)")
    args = ap.parse_args()

    voice_id = VOICES.get(args.voice, args.voice)
    preset = VOICE_PRESETS.get(args.voice, {"speed": 1.0, "gain": "0dB"})
    args.speed = args.speed if args.speed is not None else preset["speed"]
    args.gain = args.gain if args.gain is not None else preset["gain"]
    print(f"voice={args.voice} ({voice_id}) speed={args.speed} gain={args.gain}")

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
            ok = tts(e["narration"], f, key, voice_id)
            if ok:
                post_process(f, args.speed, args.gain, args.pad)
            return i, ok
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for i, ok in pool.map(run, jobs):
                if not ok:
                    print(f"FAILED entry {i} beats {entries[i]['beats']}", file=sys.stderr)
                    sys.exit(1)
                print(f"[{i+1}/{len(entries)}] synthesized beats {entries[i]['beats']}")

    # pass 3: measure durations in order, write the timing contract
    timing = {"reference_id": voice_id, "voice_name": args.voice,
              "model": MODEL, "speed": args.speed, "gain": args.gain,
              "pad_s": args.pad, "entries": []}
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
