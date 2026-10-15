"""assemble_film — "arc film" renderer in the sample-channel visual grammar.

Measured grammar (tmp/leo_research composition sheets): the screen shows a RUN
of 10-66s (median ~30s) during which 1-3 art tiles — panels/page-frames at
varying sizes, staggered vertically — drift continuously across the blurred,
darkened background (tiles enter from the trailing edge and exit at the
leading edge; sometimes the whole frame is briefly bg). Runs are separated by
HARD CUTS. Narration audio is the clock; a run covers its entries' audio
exactly. The only structural cut rule: an out-of-order beat visit (the cold
open) closes the current run; runs otherwise group by duration.

Usage:
  export PATH="/c/ffmpeg/bin:$PATH"
  py tools/assemble_film.py --slug return-of-the-top-class-master --chapter ch001 \\
      --audio-dir audio/return-of-the-top-class-master/ch001-film [--max-seconds 122]

Idempotent per run: existing run_*.mp4 clips are skipped — delete
videos/<slug>/films/<chapter>_work*/clips/ after changing settings or beats.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

FPS = 30
W, H = 1920, 1080
RUN_TARGET_S = 30.0    # median of the measured run-length distribution
CANVAS = (14, 14, 18)
BLUR_PX = 18
TILE_W = (0.36, 0.52)  # tile display width jitter as a fraction of the frame
TILE_MAX_H = 0.85 * H
GAP_X = 40             # px between tiles along the slide axis


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")
    return r


def plan_runs(entries, target_s=RUN_TARGET_S, max_seconds=None):
    """Group narration entries into runs of ~target_s (never split a merged
    entry; close before an out-of-order beat visit)."""
    runs, cur, seen = [], {"order": [], "audio": [], "dur": 0.0}, set()

    def close():
        nonlocal cur
        if cur["order"] and cur["audio"]:
            runs.append(cur)
        cur = {"order": [], "audio": [], "dur": 0.0}

    total = 0.0
    for e in entries:
        if max_seconds is not None and total >= max_seconds:
            break
        newb = [b for b in e["beats"] if b not in seen]
        for b in newb:
            seen.add(b)
        if (newb and cur["order"] and newb[0] <= cur["order"][-1]) \
                or cur["dur"] >= target_s:
            close()
        if newb:
            cur["order"].extend(newb)
        if not cur["order"]:
            cur["order"].append(e["beats"][0])
        cur["audio"].append(e["file"])
        cur["dur"] += e["duration_s"]
        total += e["duration_s"]
    close()
    return runs


def make_bg(first_tile, out: Path):
    """Static blurred background derived from the run's own art."""
    if out.exists():
        return Image.open(out)
    s = max(W / first_tile.width, H / first_tile.height)
    big = first_tile.resize((max(W, round(first_tile.width * s)) + 1,
                             max(H, round(first_tile.height * s)) + 1), Image.LANCZOS)
    x = (big.width - W) // 2
    y = (big.height - H) // 2
    bg = big.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(BLUR_PX))
    bg = ImageEnhance.Brightness(bg).enhance(0.8)
    bg.save(out)
    return bg


def layout_tiles(beats, run_idx):
    """Pre-scaled, pre-sized tiles for a run. Vertical stagger alternates so a
    train reads as 【 short/high, tall/low, … 】 like the sample's clusters."""
    tiles = []
    y_slots = [0.05, 0.26, 0.13, 0.21]
    for i, meta in enumerate(beats):
        img = meta["img"]
        w_frac = TILE_W[0] + (hash((run_idx, i)) % 1000) / 1000.0 * (TILE_W[1] - TILE_W[0])
        if len(beats) == 1:
            w_frac = 0.74  # single-beat run reads as the "full page" moment
        w = round(W * w_frac)
        h = round(img.height * w / img.width)
        if h > TILE_MAX_H:
            h = round(TILE_MAX_H)
            w = round(img.width * h / img.height)
        tiles.append({"img": img.resize((w, h), Image.LANCZOS),
                      "w": w, "h": h,
                      "y": round(H * min(0.45, y_slots[i % len(y_slots)]
                                         + (hash((run_idx, i, 7)) % 100) / 1500.0))})
    return tiles


def render_run(run, beats, run_idx, out: Path):
    dur = run["dur"]
    frames = max(2, round(dur * FPS))
    rtl = run_idx % 2 == 0  # direction alternates per run
    tiles = layout_tiles(beats, run_idx)
    if not rtl:
        tiles = list(reversed(tiles))  # narration-first beat enters first either way
    train_x = []
    x_acc = 0
    for t in tiles:
        train_x.append(x_acc)
        x_acc += t["w"] + GAP_X
    train_w = x_acc - GAP_X
    bg = make_bg(tiles[0]["img"], out.parent / f"{out.stem}_bg.png")
    bgdump = bg.tobytes()
    travel = W + train_w  # enough for every tile to fully cross the frame

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  run_{run_idx:02d}: {len(tiles)} tiles, {dur:.1f}s, train {train_w}px,"
          f" {'RTL' if rtl else 'LTR'}", flush=True)
    for f in range(frames):
        cursor = travel * min(1.0, f / FPS / dur)
        frame = Image.frombytes("RGB", (W, H), bgdump)
        for tx, tile in zip(train_x, tiles):
            if rtl:
                x = W + tx - cursor          # enters right, exits left
            else:
                x = -tx - tile["w"] + cursor  # enters left, exits right
            if x > W or x + tile["w"] < 0:
                continue
            frame.paste(tile["img"], (round(x), tile["y"]))
        proc.stdin.write(frame.tobytes())
        if f % 1200 == 0:
            print(f"    {out.name}: {f}/{frames} frames", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg failed for {out.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--audio-dir", default=None,
                    help="override narration folder (default audio/<slug>/<chapter>; "
                         "the film voice may differ from the card voice)")
    ap.add_argument("--run-seconds", type=float, default=RUN_TARGET_S)
    ap.add_argument("--max-seconds", type=float, default=None,
                    help="render only the first N seconds of narration (samples)")
    args = ap.parse_args()

    audio_dir = Path(args.audio_dir or f"audio/{args.slug}/{args.chapter}")
    beats_idx = {b["beat"]: b for b in json.loads(
        Path(f"assets/{args.slug}/{args.chapter}/beats/beats.json").read_text(encoding="utf-8"))}
    timing = json.loads((audio_dir / "timing.json").read_text(encoding="utf-8"))
    files_dir = Path(f"assets/{args.slug}/{args.chapter}/beats")

    suffix = "_sample" if args.max_seconds else ""
    runs = plan_runs(timing["entries"], args.run_seconds, args.max_seconds)
    print(f"{len(runs)} run(s) from {len(timing['entries'])} entries")
    for i, s in enumerate(runs):
        print(f"  run_{i:02d}: beats {s['order']} {s['dur']:.1f}s")

    work = Path(f"videos/{args.slug}/films/{args.chapter}_work{suffix}")
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)

    for i, r in enumerate(runs):
        out = clips / f"run_{i:02d}.mp4"
        if out.exists():
            print(f"  run_{i:02d}: exists, skipping")
            continue
        beats = [{"img": Image.open(files_dir / beats_idx[b]["file"]).convert("RGB"),
                  "beat": b} for b in r["order"]]
        render_run(r, beats, i, out)

    lst = work / "segments.txt"
    lst.write_text("".join(
        f"file '{(clips / f'run_{i:02d}.mp4').resolve().as_posix()}'\n"
        for i in range(len(runs))), encoding="utf-8")
    silent = work / "silent.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    alst = work / "audio_list.txt"
    alst.write_text("".join(
        f"file '{Path(f).resolve().as_posix()}'\n" for r in runs for f in r["audio"]),
        encoding="utf-8")
    narr = work / "narration.m4a"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst),
        "-c:a", "aac", "-b:a", "160k", str(narr)])

    final = Path(f"videos/{args.slug}/films/{args.chapter}_film{suffix}.mp4")
    sh(["ffmpeg", "-y", "-i", str(silent), "-i", str(narr),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    print(json.dumps({"final": str(final), "runs": len(runs)}))


if __name__ == "__main__":
    main()
