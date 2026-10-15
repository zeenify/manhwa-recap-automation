"""assemble_film — "arc film" renderer, grammar v3 (verified against the sample channel).

Shot grammar (tmp/leo_research composition sheets, user-confirmed):
- The video is a sequence of SHOTS (hard cuts between them, ~12-45s each).
- Normal beats become SQUARE-ISH art tiles (aspect 0.8-1.3, focal-point crop):
  one tile ~0.6 frame width, a PAIR side by side (~0.47W each, staggered),
  or a TRIPLE across (~0.36W each, staggered heights).
- Each tile SLIDES IN to its rest spot from its own direction (down / up /
  left / right — variety across the shot's tiles), over ~2.5s, then creeps:
  slow continued drift + gentle zoom-in for the rest of the shot.
- TALL strips (h/w >= 2.2) get the solo full-screen treatment: ~0.8W column,
  slow top-to-bottom pan.
- The narration audio is the clock; a shot covers its entries' audio exactly.
- The only structural cut rule: an out-of-order beat visit (cold open) closes
  the current shot.

Usage:
  export PATH="/c/ffmpeg/bin:$PATH"
  py tools/assemble_film.py --slug return-of-the-top-class-master --chapter ch001 \\
      --audio-dir audio/return-of-the-top-class-master/ch001-film [--max-seconds 108]

Idempotent per shot: existing shot_*.mp4 clips are skipped — delete
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
SHOT_TARGET_S = 16.0
CANVAS = (14, 14, 18)
BLUR_PX = 18
TILE_AR = (0.8, 1.3)   # square-ish tile aspect window (w/h)
PAN_W = 0.8            # full-screen strip column width for tall beats
PAN_MAX_RATE = 170.0   # px/s cap for the top-down pan
ENTRY_S = 2.5          # slide-in duration
CREEP_DRIFT = 9.0      # px/s continued drift after entry
CREEP_ZOOM = 0.09      # zoom-in over the remaining shot


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")
    return r


def plan_shots(entries, target_s=SHOT_TARGET_S, max_seconds=None):
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


def squareish_crop(img, focal):
    """Crop a square-ish window (aspect TILE_AR w/h) centered on the focal
    point; falls back to the full beat when the beat is already square-ish."""
    w, h = img.size
    if TILE_AR[0] <= w / h <= TILE_AR[1]:
        win_w, win_h = w, h
    else:
        # aim for aspect ~1.05 inside the beat's bounds
        win_h = min(h, int(w / 1.05)) if w / h > TILE_AR[1] else w
        win_w = min(w, int(win_h * 1.25)) if w / h > TILE_AR[1] else \
            min(w, int(h * 0.95))
        win_h = min(h, int(win_w / 1.25)) if win_w / win_h > TILE_AR[1] else win_h
    fx, fy = (focal or [0.5, 0.5])[:2]
    cx = int(win_w / 2 + (w - win_w) * max(0.0, min(1.0, fx)))
    cy = int(win_h / 2 + (h - win_h) * max(0.0, min(1.0, fy)))
    x0 = max(0, min(w - win_w, cx - win_w // 2))
    y0 = max(0, min(h - win_h, cy - win_h // 2))
    return img.crop((x0, y0, x0 + win_w, y0 + win_h))


def make_bg(tile_img, out: Path):
    if out.exists():
        return Image.open(out)
    s = max(W / tile_img.width, H / tile_img.height)
    big = tile_img.resize((max(W, round(tile_img.width * s)) + 1,
                           max(H, round(tile_img.height * s)) + 1), Image.LANCZOS)
    x = (big.width - W) // 2
    y = (big.height - H) // 2
    bg = big.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(BLUR_PX))
    bg = ImageEnhance.Brightness(bg).enhance(0.8)
    bg.save(out)
    return bg


# rest spots: (x_frac, y_frac of the tile's top-left within the frame) per count
SLOTS = {
    1: [(0.20, 0.09)],
    2: [(0.06, 0.09), (0.54, 0.17)],
    3: [(0.03, 0.17), (0.355, 0.05), (0.66, 0.14)],
}
ENTRY_DIRS = {  # per-slot slide-in directions (user-observed: down / up / left)
    1: [(0, 1)],
    2: [(0, 1), (0, -1)],
    3: [(0, 1), (0, -1), (-1, 0)],
}


def build_shot(shot_idx, beat_imgs, dur, out: Path):
    """Render one shot: tiles slide into their slots (per-tile direction),
    then creep; or a tall beat pans top-to-bottom full-screen."""
    frames = max(2, round(dur * FPS))
    tall = [(b.height / b.width >= 2.2, b) for b in beat_imgs]

    # tall strip(s) in a 1-beat shot → solo full-screen pan-down
    if len(tall) == 1 and tall[0][0]:
        strip = tall[0][1]
        dw = round(W * PAN_W)
        strip_d = strip.resize((dw, round(strip.height * dw / strip.width)), Image.LANCZOS)
        scroll = strip_d.height - H
        bg = make_bg(strip, out.parent / f"{out.stem}_bg.png")
        bgdump = bg.tobytes()
        dx = (W - dw) // 2
        rate = (scroll / dur) if scroll > 0 else 0.0
        if scroll > 0 and rate > PAN_MAX_RATE:  # already-settled pinned rate
            scroll = PAN_MAX_RATE * dur
        print(f"    pan-down: {strip_d.height}px tall, {rate:.0f}px/s", flush=True)
        proc = subprocess.Popen(
            ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
             "-r", str(FPS), "-i", "-",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
             str(out)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for f in range(frames):
            t = f / FPS
            y = scroll * min(1.0, t / dur) if scroll > 0 else 0.0
            y0 = int(y)
            alpha = y - y0
            ymax = min(strip_d.height, y0 + H + 1)
            band = strip_d.crop((0, y0, strip_d.width, ymax))
            if alpha > 0.01 and ymax < strip_d.height:
                b2 = strip_d.crop((0, y0 + 1, strip_d.width, min(strip_d.height, y0 + H + 2)))
                if b2.size == band.size:
                    band = Image.blend(band, b2, alpha)
            frame = Image.frombytes("RGB", (W, H), bgdump)
            frame.paste(band, (dx, 0))
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise SystemExit(f"ffmpeg failed for {out.name}")
        return

    # tile shots: 1 / 2 / 3 square-ish tiles
    tiles = []
    for i, b in enumerate(beat_imgs):
        img = squareish_crop(b, None)
        n = len(beat_imgs)
        w_frac = {1: 0.62, 2: 0.47, 3: 0.36}[n]
        img_d = img.resize((round(W * w_frac), round(img.height * W * w_frac / img.width)),
                           Image.LANCZOS)
        if img_d.height > H * 0.86:
            img_d = img_d.resize((round(img_d.width * H * 0.86 / img_d.height),
                                  round(H * 0.86)), Image.LANCZOS)
        slots = SLOTS[n]
        x = round(W * slots[i][0] + (hash((shot_idx, i)) % 60) - 30)
        y = round(H * slots[i][1] + (hash((shot_idx, i, 3)) % 50) - 25)
        y = max(0, min(H - img_d.height, y))
        dx_dir, dy_dir = ENTRY_DIRS[n][i]
        tiles.append({"img": img_d, "x": x, "y": y,
                      "dir": (dx_dir * W * 0.45, dy_dir * H * 0.45)})

    bg = make_bg(tiles[0]["img"], out.parent / f"{out.stem}_bg.png")
    bgdump = bg.tobytes()
    print("    {} tile(s): {}".format(
        len(tiles), [(t["img"].width, t["img"].height, t["x"], t["y"]) for t in tiles]),
        flush=True)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         str(out)], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in range(frames):
        t = f / FPS
        frame = Image.frombytes("RGB", (W, H), bgdump)
        for tile in tiles:
            e = min(1.0, t / ENTRY_S)
            ease = e * e * (3 - 2 * e)  # smoothstep ease-out for the slide-in
            dzx, dzy = tile["dir"]
            ex = round(dzx * (1 - ease))
            ey = round(dzy * (1 - ease))
            drift = max(0.0, t - ENTRY_S)
            z = 1.0 + CREEP_ZOOM * min(1.0, drift / max(1.0, dur - ENTRY_S))
            if z > 1.003:
                tw, th = round(tile["img"].width * z), round(tile["img"].height * z)
                img_z = tile["img"].resize((tw, th), Image.BILINEAR)
            else:
                tw, th, img_z = tile["img"].width, tile["img"].height, tile["img"]
            x = tile["x"] + ex + round(CREEP_DRIFT * drift) * (1 if dzx >= 0 else -1) * (1 if dzx else 0)
            y = tile["y"] + ey + round(CREEP_DRIFT * drift) * (1 if dzy >= 0 else -1) * (1 if dzy else 0)
            x -= (tw - tile["img"].width) // 2  # creep zoom grows around the center
            y -= (th - tile["img"].height) // 2
            frame.paste(img_z, (x, y))
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
    ap.add_argument("--audio-dir", default=None)
    ap.add_argument("--shot-seconds", type=float, default=SHOT_TARGET_S)
    ap.add_argument("--max-seconds", type=float, default=None,
                    help="render only the first N seconds of narration (samples)")
    args = ap.parse_args()

    audio_dir = Path(args.audio_dir or f"audio/{args.slug}/{args.chapter}")
    beats_idx = {b["beat"]: b for b in json.loads(
        Path(f"assets/{args.slug}/{args.chapter}/beats/beats.json").read_text(encoding="utf-8"))}
    timing = json.loads((audio_dir / "timing.json").read_text(encoding="utf-8"))
    files_dir = Path(f"assets/{args.slug}/{args.chapter}/beats")

    suffix = "_sample" if args.max_seconds else ""
    shots = plan_shots(timing["entries"], args.shot_seconds, args.max_seconds)
    print(f"{len(shots)} shot(s) from {len(timing['entries'])} entries")
    for i, s in enumerate(shots):
        print(f"  shot_{i:02d}: beats {s['order']} {s['dur']:.1f}s")

    work = Path(f"videos/{args.slug}/films/{args.chapter}_work{suffix}")
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)

    for i, s in enumerate(shots):
        out = clips / f"shot_{i:02d}.mp4"
        if out.exists():
            print(f"  shot_{i:02d}: exists, skipping")
            continue
        imgs = [Image.open(files_dir / beats_idx[b]["file"]).convert("RGB") for b in s["order"]]
        build_shot(i, imgs, s["dur"], out)

    lst = work / "segments.txt"
    lst.write_text("".join(
        f"file '{(clips / f'shot_{i:02d}.mp4').resolve().as_posix()}'\n"
        for i in range(len(shots))), encoding="utf-8")
    silent = work / "silent.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    alst = work / "audio_list.txt"
    alst.write_text("".join(
        f"file '{Path(f).resolve().as_posix()}'\n" for s in shots for f in s["audio"]),
        encoding="utf-8")
    narr = work / "narration.m4a"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst),
        "-c:a", "aac", "-b:a", "160k", str(narr)])

    final = Path(f"videos/{args.slug}/films/{args.chapter}_film{suffix}.mp4")
    sh(["ffmpeg", "-y", "-i", str(silent), "-i", str(narr),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    print(json.dumps({"final": str(final), "shots": len(shots)}))


if __name__ == "__main__":
    main()
