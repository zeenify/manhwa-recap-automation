"""assemble_film — executes a FILM SCRIPT (agents/writer-agent-film.md format).

The film grammar (research/leo_shot_grammar_findings.md, verified): one clause
= one image event. Each clause's asset slides in as the narration reaches it
(~1s ease-out), accumulated tiles hold with a slow zoom creep (drift settles —
tiles keep their slots), the screen wipes between scene groups, evicted tiles
FADE out (no pop-out), and PAN-class assets get a solo full-screen pan.
Every tile image first goes through TEXT WASHING (speech bubbles / dark
caption boxes are blanked to their box color — readable source text must
never reach the frame). Narration audio is the clock.

Chain: reader-agent-film -> film_assets.json -> toonkit crop (chNNN-film) ->
writer-agent-film -> chNNN_film_script.md -> TTS the per-clause blocks
(audio/<slug>/<chapter>-film, one mp3 per clause, in order) -> THIS tool.

Usage:
  py tools/assemble_film.py --slug <slug> --chapter ch001 \\
      --script scripts/<slug>/ch001_film_script.md [--tag 60s]

Idempotent per clause: existing clause_*.mp4 are skipped — delete
videos/<slug>/films/<chapter>_work<suffix>/clips/ and the washed/ cache
after changing anything.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

FPS = 30
W, H = 1920, 1080
CANVAS = (14, 14, 18)
BLUR_PX = 34          # background abstraction (strong: big shapes only)
BG_BRIGHT = 0.6
BG_SAT = 0.85
ENTRY_S = 1.0
CREEP_ZOOM = 0.09
CREEP_TIME = 14.0
DRIFT_RATE = 7.0      # px/s, settles: total drift <= DRIFT_RATE * SETTLE_S
SETTLE_S = 2.5
FADE_S = 0.7          # evicted tile fade-out
WIPE_S = 0.35
PAN_W = 0.8
PAN_MAX_RATE = 170.0
SLOTS = [(0.055, 0.10), (0.535, 0.18), (0.29, 0.40)]
WIDTHS = [0.58, 0.46, 0.36]
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
MAX_TILES = 3


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")
    return r


# ---------------------------------------------------------------- asset loading

def load_asset(assets_dir: Path, beat: int) -> Image.Image:
    """Film assets render as-is: bubbles/text stay readable (that is the
    channel's look and narration is the voice of the bubbles)."""
    return Image.open(assets_dir / f"beat_{beat:04d}.png").convert("RGB")


# ---------------------------------------------------------------- rendering

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


def tile_view(img: Image.Image, arrival: int):
    w = round(W * WIDTHS[min(arrival, 2)])
    h = round(img.height * w / img.width)
    if h > H * 0.86:
        h = round(H * 0.86)
        w = round(img.width * h / img.height)
    x = round(W * SLOTS[min(arrival, 2)][0]) + (arrival % 2) * 10
    y = round(H * SLOTS[min(arrival, 2)][1]) + (arrival * 17 % 34) - 17
    y = max(0, min(H - h, y))
    dx, dy = DIRS[arrival % 4]
    rgba = img.resize((w, h), Image.LANCZOS).convert("RGBA")
    return {"img": rgba, "w0": w, "h0": h, "x": x, "y": y,
            "dir": (dx * W * 0.55, dy * H * 0.55)}


def render_clause(spec, work_assets: Path, out: Path):
    """Render one clause segment from the global schedule (pass 1 computed
    everything: visible tiles with enter/evict times, pan, bg source)."""
    dur, t0 = spec["dur"], spec["t0"]
    frames = max(2, round(dur * FPS))
    pan = spec.get("pan")
    if pan:
        dw = round(W * PAN_W)
        strip = pan["img"].resize((dw, round(pan["img"].height * dw / pan["img"].width)),
                                     Image.LANCZOS)
        bg = make_bg(pan["img"], out.parent / f"bg_{spec['scene_id']}_pan{pan['beat']}.png")
    else:
        bg = (make_bg(spec["bg_img"], out.parent / f"bg_{spec['scene_id']}.png")
              if spec.get("bg_img") is not None else Image.new("RGB", (W, H), CANVAS))
    bgdump = bg.tobytes()
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in range(frames):
        t = f / FPS
        t_global = t0 + t
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
            for tile in spec["tiles"]:
                age = t_global - tile["enter_t"]
                if age < 0:
                    continue
                alpha = 255
                if tile.get("evict_t") is not None:
                    alpha = round(255 * max(0.0, 1.0 - (t_global - tile["evict_t"]) / FADE_S))
                    if alpha <= 0:
                        continue
                e = min(1.0, age / ENTRY_S)
                ease = e * e * (3 - 2 * e)
                z = 1.0 + CREEP_ZOOM * min(1.0, max(0.0, age - ENTRY_S) / CREEP_TIME)
                tw, th = round(tile["w0"] * z), round(tile["h0"] * z)
                img_z = (tile["img"] if z <= 1.004
                         else tile["img"].resize((tw, th), Image.BILINEAR))
                if alpha < 250:
                    img_z = img_z.copy()
                    img_z.putalpha(alpha)
                drift = min(max(0.0, age - ENTRY_S), SETTLE_S)
                offx, offy = tile["dir"]
                x = tile["x"] - (tw - tile["w0"]) // 2 + round(offx * (1 - ease)) \
                    + round(DRIFT_RATE * drift) * (1 if offx >= 0 else -1) * (1 if offx else 0)
                y = tile["y"] - (th - tile["h0"]) // 2 + round(offy * (1 - ease)) \
                    + round(DRIFT_RATE * drift) * (1 if offy >= 0 else -1) * (1 if offy else 0)
                if e >= 1.0:  # settled: never let creep/drift push a tile off-frame
                    x = max(4, min(W - tw - 4, x))
                    y = max(4, min(H - th - 4, y))
                frame.paste(img_z, (x, y), img_z)
        if spec["wipe"] and t < WIPE_S:
            a = 1.0 - t / WIPE_S
            frame = Image.blend(frame, Image.new("RGB", (W, H), (245, 245, 247)), a * 0.85)
        proc.stdin.write(frame.tobytes())
        if f % 600 == 0:
            print(f"    {out.name}: {f}/{frames}", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit(f"ffmpeg failed for {out.name}")


def parse_film_script(path: Path):
    """Per-CLAUSE parse: inside each ### SCENE block, a clause = its [NN tile|pan]
    tag line(s) followed by the NARRATION text, ending at the next tag line."""
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

    tag = f"_{args.tag}" if args.tag else ""
    work = Path(f"videos/{args.slug}/films/{args.chapter}_work{tag}")
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)

    # pass 1: deterministic global schedule (enter/evict times, wipes, pans)
    schedule, t0 = [], 0.0
    scene_tiles, cur_group, scene_id, scene_bg_img = [], None, -1, None
    for i, cl in enumerate(clauses):
        dur = timing["entries"][i]["duration_s"]
        wipe = cur_group is None or cl["group"] != cur_group
        if wipe:
            scene_id += 1
            scene_tiles, scene_bg_img = [], None
        spec = {"t0": t0, "dur": dur, "group": cl["group"], "scene_id": scene_id,
                "wipe": wipe, "pan": None, "tiles": [], "bg_img": scene_bg_img}
        if cl["assets"] and cl["assets"][0][1] == "pan":
            nn = cl["assets"][0][0]
            img = load_asset(assets_dir, nn)
            spec["pan"] = {"beat": nn, "img": img}
            scene_tiles = []
        else:
            tiled = [a[0] for a in cl["assets"] if a[1] == "tile"][:2]
            for k, nn in enumerate(tiled):
                if any(t["beat"] == nn for t in scene_tiles):
                    continue
                arrival = len(scene_tiles)
                img = load_asset(assets_dir, nn)
                if scene_bg_img is None:
                    scene_bg_img = img
                    spec["bg_img"] = img
                enter_t = t0 + (0.0 if k == 0 else dur * 0.55)
                if arrival >= MAX_TILES:  # evict the oldest with a fade
                    scene_tiles[0]["evict_t"] = enter_t
                    scene_tiles = scene_tiles[1:]
                scene_tiles.append({"enter_t": enter_t, "beat": nn,
                                    "view": tile_view(img, arrival)})
        spec["tiles"] = [dict(t["view"], beat=t["beat"], enter_t=t["enter_t"],
                              evict_t=t.get("evict_t")) for t in scene_tiles]
        schedule.append(spec)
        t0 += dur
        cur_group = cl["group"]

    for i, spec in enumerate(schedule):
        out = clips / f"clause_{i:02d}.mp4"
        if out.exists():
            print(f"  clause_{i:02d}: exists, skipping")
            continue
        kind = f"pan {spec['pan']['beat']}" if spec["pan"] else \
            "tiles " + ",".join(str(t["beat"]) for t in spec["tiles"])
        print(f"clause {i:02d}: group {spec['group']}, {kind}, {spec['dur']:.1f}s", flush=True)
        render_clause(spec, assets_dir, out)

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
