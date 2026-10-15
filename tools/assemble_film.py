"""assemble_film — Leo-style continuous-scroll render of one chapter ("arc film" format).

The film format (research/leo_manhwa_format_notes.md): the chapter's beat crops
are stacked into ONE tall column that scrolls continuously over a blurred
darkened self-background for the whole chapter's narration. No per-entry cards,
no per-sentence cuts — hard cuts happen ONLY where the narration visits beats
out of order (e.g. the cold open consumes a later beat before the chapter
starts; a beat shown there is not shown again). The narration audio is the
clock (same sync law as assemble.py).

Usage:
  export PATH="/c/ffmpeg/bin:$PATH"
  py tools/assemble_film.py --slug return-of-the-top-class-master --chapter ch001 \\
      --audio-dir audio/return-of-the-top-class-master/ch001-film

Idempotent per segment: existing seg_*.mp4 clips are skipped — delete
videos/<slug>/films/<chapter>_work/clips/ after changing settings or beats.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

FPS = 30
W, H = 1920, 1080
GUTTER = 24            # px between beats in the column
CANVAS = (14, 14, 18)  # column canvas (reads as the dark blurred bg at scroll extremes)
WIDTH_FRAC = 0.62      # display width as a fraction of the frame (Leo's tile scale)
RATE_CAP = 130.0       # max scroll speed in display px/s (~one screen height per 8.3s)
MIN_WIDTH_FRAC = 0.45  # never display the column narrower than this


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")
    return r


def build_column(beats, files_dir: Path, out: Path) -> Image.Image:
    """Stack beat crops top-to-bottom (narration order is handled by segments;
    the column itself is chronological)."""
    if out.exists():
        return Image.open(out)
    cw = max(b["w"] for b in beats)
    total_h = sum(b["h"] for b in beats) + GUTTER * (len(beats) - 1)
    print(f"column: {len(beats)} beats, {cw}x{total_h}px")
    col = Image.new("RGB", (cw, total_h), CANVAS)
    y = 0
    for b in beats:
        im = Image.open(files_dir / b["file"]).convert("RGB")
        col.paste(im, ((cw - im.width) // 2, y))
        y += im.height + GUTTER
    col.save(out)
    return col


def plan_segments(entries):
    """Group narration entries into scroll segments. A segment continues while
    the visited beats keep moving forward through the column; an out-of-order
    visit (cold open, or a beat already consumed earlier) closes the segment."""
    segs, cur, seen = [], {"order": [], "audio": [], "dur": 0.0}, set()

    def close():
        nonlocal cur
        if cur["order"] and cur["audio"]:
            segs.append(cur)
        cur = {"order": [], "audio": [], "dur": 0.0}

    for e in entries:
        newb = [b for b in e["beats"] if b not in seen]
        for b in newb:
            seen.add(b)
        if newb and cur["order"] and newb[0] <= cur["order"][-1]:
            close()
        if newb:
            cur["order"].extend(newb)
        if not cur["order"]:  # fully-revisited entry: lean on its first beat's image
            cur["order"].append(e["beats"][0])
        cur["audio"].extend([e["file"]] * 1)
        cur["dur"] += e["duration_s"]
    close()
    return segs


def make_bg(seg_col: Image.Image, out: Path) -> Image.Image:
    """Static blurred background derived from the segment's own art (the
    self-fill look from assemble.py, pre-rendered once)."""
    if out.exists():
        return Image.open(out)
    s = max(W / seg_col.width, H / seg_col.height)
    band = seg_col.resize((max(W, round(seg_col.width * s)) + 1,
                           max(H, round(seg_col.height * s)) + 1), Image.LANCZOS)
    x = (band.width - W) // 2
    y = (band.height - H) // 2
    band = band.crop((x, y, x + W, y + H))
    bg = band.filter(ImageFilter.GaussianBlur(BLUR_PX))
    bg = ImageEnhance.Brightness(bg).enhance(0.8)
    bg.save(out)
    return bg


BLUR_PX = 18


def render_segment(seg, seg_col, out: Path):
    dur = seg["dur"]
    scale = (W * WIDTH_FRAC) / seg_col.width
    rate = scale * seg_col.height / dur
    if rate > RATE_CAP:
        scale = RATE_CAP * dur / seg_col.height
        rate = RATE_CAP
    dw = round(seg_col.width * scale)
    if dw < W * MIN_WIDTH_FRAC:
        dw = round(W * MIN_WIDTH_FRAC)
        scale = dw / seg_col.width
        rate = scale * seg_col.height / dur
    view_h = H / scale  # native pixels visible per frame
    fits = seg_col.height <= view_h * 1.15
    print(f"  display {dw}px wide, rate {rate:.0f}px/s, dur {dur:.1f}s"
          f"{' [hold]' if fits else ''}", flush=True)

    bg = make_bg(seg_col, out.parent / (out.stem + "_bg.png"))
    dx = (W - dw) // 2
    held = None
    if fits:  # whole segment visible: contain-fit and center it on the frame
        s2 = min(dw / seg_col.width, H / seg_col.height)
        held = seg_col.resize((max(1, round(seg_col.width * s2)),
                               max(1, round(seg_col.height * s2))), Image.LANCZOS)
    cmd = ["ffmpeg", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    top = seg_col.height - view_h  # max scroll offset (native px)
    bgdump = bg.tobytes()
    frames = max(2, round(dur * FPS))
    for f in range(frames):
        t = f / FPS
        if fits or top <= 0:
            y0, alpha = 0.0, 0.0
        else:
            yf = top * min(1.0, t / dur)
            y0 = float(int(yf))
            alpha = yf - y0
        vh = min(seg_col.height - y0, view_h)
        b1 = seg_col.crop((0, int(y0), seg_col.width, int(y0 + vh) + 1))
        if alpha > 0.01 and int(y0 + vh) + 2 < seg_col.height:
            b2 = seg_col.crop((0, int(y0) + 1, seg_col.width, int(y0 + vh) + 2))
            if b2.size == b1.size:
                b1 = Image.blend(b1, b2, alpha)
        disp = b1.resize((dw, max(1, round(b1.height * scale))), Image.LANCZOS)
        frame = Image.frombytes("RGB", (W, H), bgdump)
        if held is not None:
            frame.paste(held, ((W - held.width) // 2, (H - held.height) // 2))
        else:
            frame.paste(disp, (dx, 0))
        proc.stdin.write(frame.tobytes())
        if f % 900 == 0:
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
    ap.add_argument("--width-frac", type=float, default=WIDTH_FRAC)
    ap.add_argument("--rate-cap", type=float, default=RATE_CAP)
    args = ap.parse_args()

    audio_dir = Path(args.audio_dir or f"audio/{args.slug}/{args.chapter}")
    beats_idx = {b["beat"]: b for b in json.loads(
        Path(f"assets/{args.slug}/{args.chapter}/beats/beats.json").read_text(encoding="utf-8"))}
    timing = json.loads((audio_dir / "timing.json").read_text(encoding="utf-8"))
    files_dir = Path(f"assets/{args.slug}/{args.chapter}/beats")

    segs = plan_segments(timing["entries"])
    print(f"{len(segs)} scroll segment(s) from {len(timing['entries'])} entries")
    for i, s in enumerate(segs):
        print(f"  seg_{i:02d}: beats {s['order'][0]}..{s['order'][-1]} "
              f"({len(s['order'])} beats, {s['dur']:.1f}s)")

    work = Path(f"videos/{args.slug}/films/{args.chapter}_work")
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)

    # one chronological column; each segment scrolls its own sub-range of it
    chrono = sorted({b for s in segs for b in s["order"]})
    col_beats = [beats_idx[b] for b in chrono]
    col = build_column(col_beats, files_dir, work / "column.png")
    ypos, y = {}, 0
    for b in col_beats:
        ypos[b["beat"]] = (y, y + b["h"])
        y += b["h"] + GUTTER

    for i, s in enumerate(segs):
        out = clips / f"seg_{i:02d}.mp4"
        if out.exists():
            print(f"  seg_{i:02d}: exists, skipping")
            continue
        ys = min(ypos[b][0] for b in s["order"])
        ye = max(ypos[b][1] for b in s["order"])
        sub = col.crop((0, max(0, ys - GUTTER), col.width, min(col.height, ye + GUTTER)))
        render_segment(s, sub, out)

    lst = work / "segments.txt"
    lst.write_text("".join(
        f"file '{(clips / f'seg_{i:02d}.mp4').resolve().as_posix()}'\n"
        for i in range(len(segs))), encoding="utf-8")
    silent = work / "silent.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    # narration in narration order, exactly as the entries were voiced
    alst = work / "audio_list.txt"
    alst.write_text("".join(
        f"file '{Path(f).resolve().as_posix()}'\n" for s in segs for f in s["audio"]),
        encoding="utf-8")
    narr = work / "narration.m4a"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst),
        "-c:a", "aac", "-b:a", "160k", str(narr)])

    final = Path(f"videos/{args.slug}/films/{args.chapter}_film.mp4")
    sh(["ffmpeg", "-y", "-i", str(silent), "-i", str(narr),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    print(json.dumps({"final": str(final), "segments": len(segs)}))


if __name__ == "__main__":
    main()
