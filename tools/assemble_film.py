"""assemble_film — executes a FILM SCRIPT (agents/writer-agent-film.md format).

The film grammar (research/leo_shot_grammar_findings.md, verified): one clause
= one image event. Each clause's asset slides in as the narration reaches it
(~1s ease-out), accumulated tiles hold with a slow zoom creep, the screen
wipes between scene groups, and PAN-class assets get a solo full-screen
top-down pan for their whole clause. Narration audio is the clock.

Chain: reader-agent-film -> film_assets.json -> toonkit crop (chNNN-film) ->
writer-agent-film -> chNNN_film_script.md -> TTS the per-clause blocks
(audio/<slug>/<chapter>-film, one mp3 per clause, in order) -> THIS tool.

Usage:
  py tools/assemble_film.py --slug <slug> --chapter ch001 \
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
BLUR_PX = 18
ENTRY_S = 1.0
CREEP_ZOOM = 0.09
CREEP_TIME = 12.0
DRIFT = 8.0
WIPE_S = 0.35
PAN_W = 0.8
PAN_MAX_RATE = 170.0
SLOTS = [(0.055, 0.10), (0.535, 0.18), (0.29, 0.40)]
WIDTHS = [0.58, 0.46, 0.36]
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # enter-from directions


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")
    return r


def parse_film_script(path: Path):
    """Per-CLAUSE parse: inside each ### SCENE block, a clause = its [NN tile|pan]
    tag line(s) followed by the NARRATION text, ending at the next tag line."""
    clauses = []
    for block in re.split(r"\n(?=### )", path.read_text(encoding="utf-8")):
        if not block.startswith("### SCENE"):
            continue
        m_group = re.search(r"group\s+(\d+)", block)
        group = int(m_group.group(1)) if m_group else 0
        cur_tags, buf = None, None

        def flush(group=group):
            if cur_tags and buf and " ".join(buf).strip():
                clauses.append({"group": group,
                                "assets": [(int(n), c) for n, c in cur_tags],
                                "narration": " ".join(" ".join(buf).split())})

        for ln in block.split("\n")[1:]:
            s = ln.strip()
            m_tag = re.match(r"^((?:\[\d+\s+(?:tile|pan)\]\s*)+)$", s)
            if m_tag:
                flush()
                cur_tags = re.findall(r"\[(\d+)\s+(tile|pan)\]", m_tag.group(1))
                buf = None
            elif s.upper().startswith("NARRATION"):
                flush()
                buf = []
                cur_tags = cur_tags  # keep tags of the clause being collected
            elif buf is not None and s:
                if not s.lstrip().startswith("#"):
                    buf.append(s)
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
    ImageEnhance.Brightness(bg).enhance(0.8).save(out)
    return Image.open(out)


def tile_view(img, ordinal, arrival_k):
    """Fixed slot + width + direction by arrival order within the scene."""
    w = round(W * WIDTHS[min(arrival_k, 2)])
    h = round(img.height * w / img.width)
    if h > H * 0.86:
        h = round(H * 0.86)
        w = round(img.width * h / img.height)
    x = round(W * SLOTS[min(arrival_k, 2)][0]) + (arrival_k % 2) * 12
    y = round(H * SLOTS[min(arrival_k, 2)][1]) + (arrival_k * 23 % 40) - 20
    y = max(0, min(H - h, y))
    dx, dy = DIRS[arrival_k % 4]
    return {"img": img.resize((w, h), Image.LANCZOS), "w0": w, "h0": h, "x": x, "y": y,
            "dir": (dx * W * 0.55, dy * H * 0.55)}


def render_clause(spec, tiles_visible, dur, assets_dir: Path, out: Path):
    """tiles_visible: [(enter_t_global, ordinal, beat, img)] — everything on
    screen during this clause, including this clause's own new arrivals."""
    frames = max(2, round(dur * FPS))
    pan = spec.get("pan")
    bg_img = tiles_visible[-1][1]["img"] if tiles_visible else pan["img"] if pan else None
    if bg_img is None:
        frame0 = Image.new("RGB", (W, H), CANVAS)
        bg = frame0
        bgdump = frame0.tobytes()
        bg_ref = None
    else:
        bg = make_bg(bg_img, out.parent / f"bg_{spec['scene_id']}.png")
        bgdump = bg.tobytes()
    strip = None
    if pan:
        dw = round(W * PAN_W)
        strip = pan["img"].resize((dw, round(pan["img"].height * dw / pan["img"].width)),
                                  Image.LANCZOS)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in range(frames):
        t = f / FPS
        t_global = spec["t0"] + t
        if pan:
            scroll = (strip.height - H) * min(1.0, t / dur) if strip.height > H else 0.0
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
        else:
            frame = Image.frombytes("RGB", (W, H), bgdump)
            for enter_t, tile in tiles_visible:
                age = t_global - enter_t
                if age < 0:
                    continue
                e = min(1.0, age / ENTRY_S)
                ease = e * e * (3 - 2 * e)
                z = 1.0 + CREEP_ZOOM * min(1.0, max(0.0, age - ENTRY_S) / CREEP_TIME)
                tw, th = round(tile["w0"] * z), round(tile["h0"] * z)
                img_z = tile["img"] if z <= 1.004 else tile["img"].resize((tw, th), Image.BILINEAR)
                drift = max(0.0, age - ENTRY_S)
                offx, offy = tile["dir"]
                x = tile["x"] - (tw - tile["w0"]) // 2 + round(offx * (1 - ease)) \
                    + round(DRIFT * drift * (1 if offx >= 0 else -1) if offx else 0)
                y = tile["y"] - (th - tile["h0"]) // 2 + round(offy * (1 - ease)) \
                    + round(DRIFT * drift * (1 if offy >= 0 else -1) if offy else 0)
                frame.paste(img_z, (x, y))
        if spec["wipe"] and t < WIPE_S:
            a = 1.0 - t / WIPE_S
            frame = Image.blend(frame, Image.new("RGB", (W, H), (245, 245, 247)), a * 0.85)
        proc.stdin.write(frame.tobytes())
        if f % 600 == 0:
            print(f"    {out.name}: {f}/{frames}", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg failed for {out.name}")


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

    # pass 1: build the deterministic global schedule
    schedule, t0 = [], 0.0
    scene_tiles, cur_group, scene_id = [], None, -1
    for i, cl in enumerate(clauses):
        dur = timing["entries"][i]["duration_s"]
        wipe = cur_group is None or cl["group"] != cur_group
        if wipe:
            scene_id += 1
            scene_tiles = []
        spec = {"t0": t0, "dur": dur, "group": cl["group"], "scene_id": scene_id,
                "wipe": wipe, "pan": None}
        if cl["assets"] and cl["assets"][0][1] == "pan":
            nn = cl["assets"][0][0]
            spec["pan"] = {"img": imgs[nn], "beat": nn}
            scene_tiles = []  # a pan is a solo moment; reset after it
        else:
            for k, (nn, klass) in enumerate([a for a in cl["assets"] if a[1] == "tile"][:2]):
                arrival = len(scene_tiles)
                enter_t = t0 + (0.0 if k == 0 else dur * 0.55)
                scene_tiles.append({"enter_t": enter_t, "ordinal": scene_id,
                                    "arrival": arrival, "beat": nn,
                                    "view": tile_view(imgs[nn], arrival, arrival)})
                if len(scene_tiles) > 3:
                    scene_tiles = scene_tiles[-3:]
        spec["tiles"] = [(t["enter_t"], t["view"]) for t in scene_tiles]
        schedule.append(spec)
        t0 += dur
        cur_group = cl["group"]

    for i, spec in enumerate(schedule):
        out = clips / f"clause_{i:02d}.mp4"
        if out.exists():
            print(f"  clause_{i:02d}: exists, skipping")
            continue
        print(f"clause {i:02d}: group {spec['group']}, "
              f"{'pan '+str(spec['pan']['beat']) if spec['pan'] else 'tiles'}, "
              f"{spec['dur']:.1f}s", flush=True)
        render_clause(spec, spec["tiles"], spec["dur"], assets_dir, out)

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
    print(json.dumps({"final": str(final), "clauses": len(clauses)}))


if __name__ == "__main__":
    main()
