"""assemble — render the chapter video from beats + timing (+ script shot directives).

Pipeline: one segment per script entry (silent, camera move) → concat → mux
narration audio (concatenated) → optional music bed (audio/music.mp3, low volume).

Camera rules (v2):
- Single-beat entry → that panel as a composed 16:9 card (blurred darkened copy of
  the panel fills the frame, sharp panel centered) with the entry's camera move.
- Multi-beat entry (the writer merged beats) → the panels are joined SIDE BY SIDE
  into one collage card shown for the whole entry duration — the narration always
  describes what is on screen (no time-splitting, no wrong-panel moments).
- There is NO full-width scroll: pan-down renders the panel as a 60%-width
  centered column over the static blurred background and scrolls THAT — mild
  zoom, whole panel width always in frame (full-width scrolling was retired: it
  was dizzying and illegible). Panels whose column wouldn't be taller than the
  frame just get `fit`.

Usage:
  python tools/assemble.py --slug a-wimps-strategy-guide --chapter ch001 \
      [--test N]   # render only the first N entries (smoke test)
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

FPS = 30
W, H = 1920, 1080
SS_W = 3840  # supersample width for zoompan quality
GUTTER = 24  # px between panels in a collage
PAN_W = 0.6  # pan-down column width as a fraction of frame width (full-width scroll retired)
COLLAGE_MAX_RATIO = 1.6  # taller/shortest height ratio allowed in one collage card


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")
    return r


def root_script_default(chapter: str) -> Path:
    p = Path(f"scripts/{chapter}_script.md")
    if not p.exists():
        alt = Path(f"scripts/{chapter.replace('ch00', 'ch0')}_script.md")
        if alt.exists():
            return alt
        # fall back: any script mentioning this chapter slug order
        for cand in sorted(Path("scripts").glob("*_script.md")):
            return cand
    return p


def parse_shot_directives(script_path: Path):
    """entry signature (tuple of covered beats) -> SHOT directive"""
    text = script_path.read_text(encoding="utf-8")
    out = {}
    for block in re.split(r"\n(?=### )", text):
        if not block.startswith("### "):
            continue
        m_shot = re.search(r"SHOT:\s*(\S+)", block)
        if not m_shot:
            continue
        directive = m_shot.group(1).strip().lower()
        beats = []
        m_beat = re.search(r"BEAT (\d+)", block)
        if m_beat:
            first = int(m_beat.group(1))
            m_cov = re.search(r"covers (\d+)[–-](\d+)", block)
            beats = list(range(int(m_cov.group(1)), int(m_cov.group(2)) + 1)) if m_cov else [first]
        m_cold = re.search(r"from beat (\d+)", block)
        if not beats and m_cold:
            beats = [int(m_cold.group(1))]
        if beats:
            out[tuple(beats)] = directive
    return out


def default_move(composition: str, h: int) -> str:
    if composition in ("closeup",):
        return "punch-in"
    if composition in ("wide-action", "establishing-character") and h > 1300:
        return "pan-down"  # reduced-width scroll (see segment_filter)
    if composition in ("transition-black",):
        return "hold"
    return "hold"


def segment_filter(move: str, dur: float, fp) -> str:
    """All moves operate on a COMPOSED 16:9 card: blurred darkened panel as
    background filling the frame, sharp panel centered on top — then the camera
    moves on that card (no aspect distortion). pan-down scrolls the panel as a
    60%-width centered column over the static blurred bg: the whole panel width
    stays in view at a mild zoom, so the scroll stays readable and calm."""
    frames = max(2, round(dur * FPS))
    fx, fy = (fp or [0.5, 0.5])[:2]
    if move == "pan-down":
        cw = int(W * PAN_W)
        return (
            f"[0:v]split[bgs][fgs];"
            f"[bgs]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=luma_radius=16:luma_power=2,eq=brightness=-0.12[bg];"
            f"[fgs]scale={cw}:-2[fg];"
            f"[bg][fg]overlay=x=(W-w)/2:y='-(h-{H})*clip(t/{dur:.3f},0,1)',"
            f"fps={FPS},setsar=1,format=yuv420p")
    if move in ("punch-in",):
        z = f"min(1+0.12*on/{frames},1.12)"
    elif move == "quick-zoom":
        z = f"min(1+0.16*on/{frames},1.16)"
    elif move == "slow-zoom-out":
        z = f"max(1.12-0.12*on/{frames},1.0)"
    elif move == "fit":  # whole panel visible as centered column — barely breathing
        z = f"min(1+0.035*on/{frames},1.035)"
    else:  # hold — gentle creep
        z = f"min(1+0.05*on/{frames},1.05)"
    # zoom window biased slightly toward the beat's focal point
    bx = max(0.2, min(0.8, 0.5 + 0.4 * (fx - 0.5)))
    by = max(0.2, min(0.8, 0.5 + 0.4 * (fy - 0.5)))
    return (
        f"[0:v]split[bgs][fgs];"
        f"[bgs]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"boxblur=luma_radius=16:luma_power=2,eq=brightness=-0.12[bg];"
        f"[fgs]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,scale={SS_W}:-2,"
        f"zoompan=z='{z}':x='(iw-iw/zoom)*{bx}':y='(ih-ih/zoom)*{by}':"
        f"d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")


def render_segment(img: Path, dur: float, move: str, fp, out: Path):
    vf = segment_filter(move, dur, fp)
    sh(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}",
        "-i", str(img), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-an", str(out)])


def build_collage(imgs: list[Path], out: Path) -> Path:
    """Join panels side by side (tops aligned, dark gutter) into one collage card.
    Two tall webtoon panels side by side approximate 16:9, so the collage scales
    up nicely on the composed card."""
    if out.exists():
        return out
    ims = [Image.open(p).convert("RGB") for p in imgs]
    h = max(im.height for im in ims)
    w = sum(im.width for im in ims) + GUTTER * (len(ims) - 1)
    canvas = Image.new("RGB", (w, h), (12, 12, 14))
    x = 0
    for im in ims:
        canvas.paste(im, (x, 0))
        x += im.width + GUTTER
    canvas.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="a-wimps-strategy-guide")
    ap.add_argument("--chapter", default="ch001")
    ap.add_argument("--test", type=int, default=0, help="render only first N entries")
    ap.add_argument("--script", default=None, help="narration script path (default: scripts/<chapter>_script.md)")
    args = ap.parse_args()
    script_path = Path(args.script) if args.script else root_script_default(args.chapter)

    root = Path(".")
    beats_idx = {b["beat"]: b for b in json.loads(
        (root / f"assets/{args.slug}/{args.chapter}/beats/beats.json").read_text(encoding="utf-8"))}
    timing = json.loads((root / f"audio/{args.chapter}/timing.json").read_text(encoding="utf-8"))
    directives = parse_shot_directives(script_path)

    work = root / f"videos/{args.chapter}"
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)

    # build segment list: ONE segment per script entry. Multi-beat entries render
    # as a side-by-side collage for the whole duration (narration always matches
    # what is on screen); no per-beat time-splitting, no full-width scrolling.
    segments = []
    for ei, e in enumerate(timing["entries"]):
        if args.test and ei >= args.test:
            break
        cov = e["beats"]
        bs = [beats_idx[b] for b in cov if b in beats_idx]
        if not bs:
            print(f"SKIP entry {ei}: no beat images for {cov}", file=sys.stderr)
            continue
        move = directives.get(tuple(cov), "hold")
        if len(bs) > 1:
            hs = [b["h"] for b in bs]
            if max(hs) / max(1, min(hs)) > COLLAGE_MAX_RATIO:
                # mismatched sizes would render the short panel unreadably tiny:
                # fall back to sequential per-beat cards (old time-split behavior)
                print(f"entry {ei}: beats {cov} heights {hs} exceed collage ratio "
                      f"{COLLAGE_MAX_RATIO} — rendering sequentially", file=sys.stderr)
                total_h = sum(hs)
                acc = 0.0
                for b in bs:
                    share = e["duration_s"] * (b["h"] / total_h)
                    seg_move = move
                    if seg_move == "pan-down" and (b["h"] / max(1, b["w"])) <= 1.67:
                        seg_move = "fit"
                    segments.append({"img": root / f"assets/{args.slug}/{args.chapter}/beats/{b['file']}",
                                     "dur": share, "move": seg_move,
                                     "fp": b.get("focal_point"), "entry": ei, "idx": len(segments)})
                    acc += share
                drift = e["duration_s"] - acc
                if abs(drift) > 0.05 and segments:
                    segments[-1]["dur"] += drift
                continue
            cimg = build_collage(
                [root / f"assets/{args.slug}/{args.chapter}/beats/{b['file']}" for b in bs],
                work / f"collage_entry_{ei:03d}.png")
            segments.append({"img": cimg, "dur": e["duration_s"], "move": "hold",
                             "fp": [0.5, 0.5], "entry": ei, "idx": len(segments)})
        else:
            b = bs[0]
            # pan-down eligibility: the 60%-width column must actually be taller
            # than the frame, otherwise the whole panel fits anyway
            if move == "pan-down":
                col_h = b["h"] * (W * PAN_W) / max(1, b["w"])
                if col_h <= H * 1.15:
                    move = "fit"
            segments.append({"img": root / f"assets/{args.slug}/{args.chapter}/beats/{b['file']}",
                             "dur": e["duration_s"], "move": move,
                             "fp": b.get("focal_point"), "entry": ei, "idx": len(segments)})

    print(f"{len(segments)} segments to render")
    for s in segments:
        out = clips / f"seg_{s['idx']:04d}.mp4"
        if not out.exists():
            render_segment(s["img"], s["dur"], s["move"], s["fp"], out)

    # concat silent segments (concat demuxer resolves relative paths against the
    # LIST FILE's directory — use absolute paths to avoid surprises)
    lst = work / "segments.txt"
    lst.write_text("".join(
        f"file '{(root / clips / ('seg_%04d.mp4' % s['idx'])).resolve().as_posix()}'\n" for s in segments),
        encoding="utf-8")
    silent = work / "silent.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])

    # concat narration audio (same entries that were rendered)
    n_audio = args.test if args.test else len(timing["entries"])
    alst = work / "audio_list.txt"
    alst.write_text("".join(
        f"file '{(root / e['file']).resolve().as_posix()}'\n" for e in timing["entries"][:n_audio]),
        encoding="utf-8")
    narr = work / "narration.m4a"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst),
        "-c:a", "aac", "-b:a", "160k", str(narr)])

    # mux + optional music
    music = root / "audio/music.mp3"
    final = work / f"{args.chapter}.mp4"
    if music.exists():
        sh(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(music),
            "-i", str(silent), "-i", str(narr),
            "-filter_complex",
            "[0:a]volume=0.14,afade=t=in:d=3[m];"
            "[2:a][m]amix=inputs=2:duration=first:normalize=0[aout]",
            "-map", "1:v", "-map", "[aout]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    else:
        sh(["ffmpeg", "-y", "-i", str(silent), "-i", str(narr),
            "-map", "0:v", "-map", "1:a", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)])
    print(json.dumps({"final": str(final), "segments": len(segments)}))


if __name__ == "__main__":
    main()
