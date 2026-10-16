"""assemble_film — BATCH-model renderer for the arc-film format.

Grammar (user-verified): the video is a sequence of BATCHES. Each batch is a
self-contained composition of 1, 2, or 3 images, sized and placed EXACTLY:
- 1 image: the star of the batch — shown big and centered; a tall strip pans
  top-to-bottom full-screen instead.
- 2 images: one occupies the LEFT half, one the RIGHT half — perfectly
  balanced, centered within their halves, no overlap, no imbalance.
- 3 images: left / middle / right thirds — smaller so all three fit, but
  still large (there is breathing room; triples are rarer).
Each image slides INTO its slot as the narration reaches it (~0.9s ease-out)
and holds with a gentle zoom creep. When the batch's narration ends the whole
batch disappears — NO leftovers carry into the next batch. Scene-group
changes get a white flash wipe. Narration audio is the clock; one clause =
one batch (assets tagged per clause by the film writer).

Chain: reader-agent-film -> film_assets.json -> toonkit crop (chNNN-film) ->
writer-agent-film -> chNNN_film_script.md -> TTS per-clause
(audio/<slug>/<chapter>-film, one mp3 per clause, in order) -> THIS tool.

Usage:
  py tools/assemble_film.py --slug <slug> --chapter ch001 \\
      --script scripts/<slug>/ch001_film_script.md [--tag 60s]

Idempotent per clause: existing clause_*.mp4 are skipped — delete
videos/<slug>/films/<chapter>_work<suffix>/clips/ after changing anything.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

FPS = 30
W, H = 1920, 1080
CANVAS = (14, 14, 18)
BLUR_PX = 34
BG_BRIGHT = 0.6
BG_SAT = 0.85
ENTRY_S = 0.9
CREEP_ZOOM = 0.05
PAN_W = 0.8
PAN_MAX_RATE = 170.0
WIPE_S = 0.35
LAYOUTS = {  # per count: slot centers (x frac), max width frac, max height frac
    1: {"centers": [0.5], "maxw": 0.74, "maxh": 0.88},
    2: {"centers": [0.25, 0.75], "maxw": 0.46, "maxh": 0.86},
    3: {"centers": [1 / 6, 0.5, 5 / 6], "maxw": 0.315, "maxh": 0.8},
}
SLIDE_DIRS = {  # slide-in travel-in direction per slot: (dx, dy)
    1: [(0, 1)],
    2: [(-1, 0), (1, 0)],
    3: [(-1, 0), (0, 1), (1, 0)],
}


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")
    return r


def parse_film_script(path: Path):
    clauses = []
    for block in re.split(r"\n(?=### )", path.read_text(encoding="utf-8")):
        if not block.startswith("### SCENE"):
            continue
        m_group = re.search(r"group\s+(\d+)", block)
        group = int(m_group.group(1)) if m_group else 0
        cur = {"tags": None, "buf": None}

        def flush(group=group, cur=cur):
            if cur["tags"] and cur["buf"] and " ".join(cur["buf"]).strip():
                clauses.append({"group": group,
                                "assets": [(int(n), c) for n, c in cur["tags"]],
                                "narration": " ".join(" ".join(cur["buf"]).split())})

        for ln in block.split("\n")[1:]:
            s = ln.strip()
            m_tag = re.match(r"^((?:\[\d+\s+(?:tile|pan)\]\s*)+)$", s)
            if m_tag:
                flush()
                cur["tags"] = re.findall(r"\[(\d+)\s+(tile|pan)\]", m_tag.group(1))
                cur["buf"] = None
            elif s.upper().startswith("NARRATION"):
                flush()
                cur["buf"] = []
            elif cur["buf"] is not None and s and not s.lstrip().startswith("#"):
                cur["buf"].append(s)
        flush()
    return clauses


def make_bg(img: Image.Image, out: Path):
    if out.exists():
        return Image.open(out)
    s = max(W / img.width, H / img.height)
    big = img.resize((max(W, round(img.width * s)) + 1,
                      max(H, round(img.height * s)) + 1), Image.LANCZOS)
    x, y = (big.width - W) // 2, (big.height - H) // 2
    bg = big.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(BLUR_PX))
    bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHT)
    bg = ImageEnhance.Color(bg).enhance(BG_SAT)
    bg.save(out)
    return Image.open(out)


def fit_tile(img: Image.Image, maxw: int, maxh: int):
    s = min(maxw / img.width, maxh / img.height)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))),
                      Image.LANCZOS)


def start_encoder(out: Path):
    return subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def finish(proc, out: Path):
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg failed for {out.name}")


def proc_write(proc, frame: Image.Image, f: int, frames: int, out: Path):
    proc.stdin.write(frame.tobytes())
    if f % 600 == 0:
        print(f"    {out.name}: {f}/{frames}", flush=True)


def build_batch(clause, dur, wipes: bool, out: Path):
    """One batch = one clause: n = 1..3 tiles placed by the layout table, or a
    solo full-screen pan (explicit pan tag, or a tall single promoted)."""
    frames = max(2, round(dur * FPS))
    pan_img = clause["pan_img"]
    tiles_src = clause["tile_imgs"][:3]
    is_pan = pan_img is not None or (len(tiles_src) == 1 and
                                     tiles_src[0].height / tiles_src[0].width >= 2.2)
    if is_pan:
        img = pan_img if pan_img is not None else tiles_src[0]
        dw = round(W * PAN_W)
        strip = img.resize((dw, round(img.height * dw / img.width)), Image.LANCZOS)
        bg = make_bg(img, out.parent / f"{out.stem}_bg.png")
        bgdump = bg.tobytes()
        scroll_px = strip.height - H
        proc = start_encoder(out)
        for f in range(frames):
            t = f / FPS
            scroll = scroll_px * min(1.0, t / dur) if scroll_px > 0 else 0.0
            y0 = int(scroll)
            alpha = scroll - y0
            ymax = min(strip.height, y0 + H + 1)
            band = strip.crop((0, y0, strip.width, ymax))
            if alpha > 0.01 and ymax < strip.height:
                b2 = strip.crop((0, y0 + 1, strip.width, min(strip.height, y0 + H + 2)))
                if b2.size == band.size:
                    band = Image.blend(band, b2, alpha)
            frame = Image.frombytes("RGB", (W, H), bgdump)
            frame.paste(band, ((W - strip.width) // 2, 0))
            if wipes and t < WIPE_S:
                frame = Image.blend(frame, Image.new("RGB", (W, H), (245, 245, 247)),
                                    (1 - t / WIPE_S) * 0.85)
            proc_write(proc, frame, f, frames, out)
        finish(proc, out)
        return

    n = max(1, min(3, len(tiles_src)))
    lay = LAYOUTS[n]
    bg = make_bg(tiles_src[-1], out.parent / f"{out.stem}_bg.png")
    bgdump = bg.tobytes()
    tiles = []
    for k, img in enumerate(tiles_src):
        disp = fit_tile(img, round(W * lay["maxw"]), round(H * lay["maxh"]))
        cx = round(W * lay["centers"][k])
        x = max(4, min(W - disp.width - 4, cx - disp.width // 2))
        y = max(4, min(H - disp.height - 4, (H - disp.height) // 2))
        dx, dy = SLIDE_DIRS[n][k]
        tiles.append({"img": disp, "w": disp.width, "h": disp.height,
                      "x": x, "y": y, "dir": (dx * W * 0.6, dy * H * 0.6),
                      "t0": k * min(1.2, dur * 0.3)})
    proc = start_encoder(out)
    for f in range(frames):
        t = f / FPS
        frame = Image.frombytes("RGB", (W, H), bgdump)
        for tile in tiles:
            age = t - tile["t0"]
            if age < 0:
                continue
            e = min(1.0, age / ENTRY_S)
            ease = e * e * (3 - 2 * e)
            z = 1.0 + CREEP_ZOOM * min(1.0, max(0.0, age - ENTRY_S) / max(dur, 1))
            tw, th = round(tile["w"] * z), round(tile["h"] * z)
            img_z = tile["img"] if z <= 1.004 else tile["img"].resize((tw, th), Image.BILINEAR)
            offx, offy = tile["dir"]
            x = tile["x"] - (tw - tile["w"]) // 2 + round(offx * (1 - ease))
            y = tile["y"] - (th - tile["h"]) // 2 + round(offy * (1 - ease))
            if e >= 1.0:
                x = max(4, min(W - tw - 4, x))
                y = max(4, min(H - th - 4, y))
            frame.paste(img_z, (x, y))
        if wipes and t < WIPE_S:
            frame = Image.blend(frame, Image.new("RGB", (W, H), (245, 245, 247)),
                                (1 - t / WIPE_S) * 0.85)
        proc_write(proc, frame, f, frames, out)
    finish(proc, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    assets_dir = Path(f"assets/{args.slug}/{args.chapter}-film/beats")
    beats = json.loads((assets_dir / "beats.json").read_text(encoding="utf-8"))
    timing = json.loads((Path(f"audio/{args.slug}/{args.chapter}-film") / "timing.json")
                        .read_text(encoding="utf-8"))
    clauses = parse_film_script(Path(args.script))
    if len(clauses) != len(timing["entries"]):
        raise SystemExit(f"clauses {len(clauses)} != audio entries {len(timing['entries'])}")
    imgs = {b["beat"]: Image.open(assets_dir / b["file"]).convert("RGB") for b in beats}

    tag = f"_{args.tag}" if args.tag else ""
    work = Path(f"videos/{args.slug}/films/{args.chapter}_work{tag}")
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)

    cur_group = None
    for i, cl in enumerate(clauses):
        out = clips / f"clause_{i:02d}.mp4"
        dur = timing["entries"][i]["duration_s"]
        wipes = cur_group is not None and cl["group"] != cur_group
        clause = {"group": cl["group"], "tile_imgs": [], "pan_img": None}
        for nn, klass in cl["assets"]:
            if klass == "pan":
                clause["pan_img"] = imgs[nn]
            else:
                clause["tile_imgs"].append(imgs[nn])
        print(f"clause {i:02d}: group {cl['group']}, "
              f"assets {[(n, _k) for n, _k in cl['assets']]}, {dur:.1f}s", flush=True)
        if not out.exists():
            build_batch(clause, dur, wipes, out)
        cur_group = cl["group"]

    lst = work / "segments.txt"
    lst.write_text("".join(
        f"file '{(clips / f'clause_{i:02d}.mp4').resolve().as_posix()}'\n"
        for i in range(len(clauses))), encoding="utf-8")
    silent = work / "silent.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    alst = work / "audio_list.txt"
    alst.write_text("".join(
        f"file '{Path(e['file']).resolve().as_posix()}'\n" for e in timing["entries"]),
        encoding="utf-8")
    narr = work / "narration.m4a"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst),
        "-c:a", "aac", "-b:a", "160k", str(narr)])

    final = Path(f"videos/{args.slug}/films/{args.chapter}_film{tag}.mp4")
    sh(["ffmpeg", "-y", "-i", str(silent), "-i", str(narr),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    print(json.dumps({"final": str(final), "batches": len(clauses)}))


if __name__ == "__main__":
    main()
