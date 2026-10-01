"""compile_video — build the YouTube-ready chapter compilation.

Generates styled transition cards (intro / per-chapter / outro) with Pillow,
renders them as short clips that match the chapter files' codec parameters
(h264 1920x1080 30fps + aac 44100 mono), then losslessly concats
[intro] + ch1 + [card] + ch2 + ... + ch20 + [outro]. Prints the
YouTube-chapters timestamp block for the upload description.

Usage:
  python tools/compile_video.py --from 1 --to 20 --out videos/compilation/ch001-020_full.mp4
"""
import argparse
import subprocess
from pathlib import Path

W, H, FPS = 1920, 1080, 30
SERIES = "A WIMP'S STRATEGY GUIDE"
SERIES_SUB = "TO CONQUER THE TOWER"
CARD_DUR = 2.5
INTRO_DUR = 3.0
OUTRO_DUR = 10.0
BG = (13, 13, 18)
GOLD = (240, 192, 64)
WHITE = (240, 240, 240)
GRAY = (150, 150, 160)

F_BIG = "C:/Windows/Fonts/ariblk.ttf"     # Arial Black
F_MID = "C:/Windows/Fonts/arialbd.ttf"    # Arial Bold


def _fmt_ts(seconds: float) -> str:
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def _draw_center(draw, text, font, y, fill, letter_pad=0):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, font=font, fill=fill)


def make_card(path: Path, big: str, small: str, sub: str) -> None:
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    size = 150
    while size > 60:  # shrink until the big line fits with side margins
        f_big = ImageFont.truetype(F_BIG, size)
        bbox = d.textbbox((0, 0), big, font=f_big)
        if bbox[2] - bbox[0] <= W - 160:
            break
        size -= 6
    f_small = ImageFont.truetype(F_MID, 44)
    f_sub = ImageFont.truetype(F_MID, 34)
    _draw_center(d, small.upper(), f_small, 330, GOLD)
    _draw_center(d, big, f_big, 440, WHITE)
    if sub:
        _draw_center(d, sub.upper(), f_sub, 680, GRAY)
    d.rectangle([W // 2 - 220, 640, W // 2 + 220, 644], fill=GOLD)
    im.save(path, "PNG")


def render_card_clip(png: Path, mp4: Path, dur: float) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-loop", "1", "-i", str(png),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", f"{dur}",
        "-vf", f"fade=t=in:st=0:d=0.4,fade=t=out:st={dur - 0.4:.2f}:d=0.4,format=yuv420p",
        "-r", str(FPS), "-s", f"{W}x{H}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "96k",
        "-shortest", str(mp4),
    ], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="first", type=int, default=1)
    ap.add_argument("--to", dest="last", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workdir", default="tmp/compile")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)

    entries = []  # (path, youtube_label or None)

    total = 0.0
    lines = []
    for n in range(args.first, args.last + 1):
        label = f"Chapter {n}"
        if n > args.first:
            png = work / f"card_ch{n:03d}.png"
            make_card(png, f"CHAPTER {n}", SERIES, SERIES_SUB)
            clip = work / f"clip_ch{n:03d}.mp4"
            render_card_clip(png, clip, CARD_DUR)
            entries.append((clip, label))
            total += CARD_DUR
        ch = Path(f"videos/ch{n:03d}/ch{n:03d}.mp4")
        if not ch.exists():
            raise SystemExit(f"missing chapter video: {ch}")
        lines.append(f"{_fmt_ts(total)} {label}")
        d = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(ch)],
            capture_output=True, text=True, check=True).stdout.strip())
        entries.append((ch, None))
        total += d

    outro_png = work / "card_outro.png"
    make_card(outro_png, "THAT'S CHAPTERS 1-20", SERIES, "NEW FLOORS EVERY WEEK - SUBSCRIBE")
    outro_clip = work / "clip_outro.mp4"
    render_card_clip(outro_png, outro_clip, OUTRO_DUR)
    entries.append((outro_clip, None))
    total += OUTRO_DUR

    listfile = work / "concat_list.txt"
    with open(listfile, "w", encoding="utf-8") as f:
        for path, _ in entries:
            if path is None:
                continue
            f.write(f"file '{path.resolve().as_posix()}'\n")

    # Stage 1: lossless concat into an intermediate (fast).
    intermediate = work / "concat_intermediate.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-f", "concat", "-safe", "0", "-i", str(listfile),
        "-c", "copy", str(intermediate),
    ], check=True)

    # Stage 2: single clean re-encode — normalizes every frame and packet so
    # mixed-encoder sources (cards vs older chapter renders) cannot glitch.
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-stats",
        "-i", str(intermediate),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-s", f"{W}x{H}",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1",
        "-movflags", "+faststart", str(out),
    ], check=True)

    print(f"final: {out}  ({_fmt_ts(total)} total)")
    print("--- YouTube chapters (paste into description) ---")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
