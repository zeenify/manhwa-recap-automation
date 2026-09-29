"""toonkit — the manhwa-to-video pipeline toolkit that subagents call via Bash.

Subcommands:
  views      Generate ruler-annotated, gutter-marked view pieces for a chapter.
             The reader agent Reads these images and reports beat boundaries
             in VIRTUAL chapter coordinates (labels on the ruler).
  gutters    Print deterministic gutter candidates for each file (the propose stage).
  continuation  Side-by-side image of file N bottom + file N+1 top, to judge
             whether a panel continues across the file boundary.
  crop       Export beat PNGs from a beats draft JSON written by the reader agent.

All coordinates are VIRTUAL: file 1 occupies [0, h1), file 2 [h1, h1+h2), etc.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RULER_W = 64
TICK_MINOR = 250
TICK_MAJOR = 1000
GUTTER_STD = 14.0
GUTTER_MIN = 10


def auto_trim(piece: Image.Image, std_thresh: float = 12.0, pad: int = 12, max_trim: int = 400):
    """Trim near-uniform margins (black/white page background) from all four edges."""
    g = np.asarray(piece.convert("L"), dtype=np.float32)
    h, w = g.shape
    top, bot, left, right = 0, h, 0, w
    def row_uniform(y): return g[y, :].std() < std_thresh
    def col_uniform(x): return g[:, x].std() < std_thresh
    t = 0
    while top < bot - pad and row_uniform(top) and t < max_trim:
        top += 1; t += 1
    t = 0
    while bot > top + pad and row_uniform(bot - 1) and t < max_trim:
        bot -= 1; t += 1
    t = 0
    while left < right - pad and col_uniform(left) and t < max_trim:
        left += 1; t += 1
    t = 0
    while right > left + pad and col_uniform(right - 1) and t < max_trim:
        right -= 1; t += 1
    top, bot = max(0, top - pad), min(h, bot + pad)
    left, right = max(0, left - pad), min(w, right + pad)
    return piece.crop((left, top, right, bot)), (left, top, right, bot)


def chapter_files(chapter_dir: Path) -> list[Path]:
    files = (sorted(chapter_dir.glob("*.jpg")) + sorted(chapter_dir.glob("*.png"))
             + sorted(chapter_dir.glob("*.webp")))
    return sorted(files, key=lambda p: p.name)


def file_sizes(files: list[Path]) -> list[tuple[int, int]]:
    out = []
    for f in files:
        with Image.open(f) as im:
            out.append(im.size)  # (w, h)
    return out


def offsets(sizes: list[tuple[int, int]]) -> list[int]:
    off, acc = [], 0
    for _, h in sizes:
        off.append(acc)
        acc += h
    return off


def gutter_lines(img: Image.Image, base_y: int):
    """Return virtual-y centers of uniform bands (candidate cut lines)."""
    g = np.asarray(img.convert("L"), dtype=np.float32)
    row_std = g.std(axis=1)
    uniform = row_std < GUTTER_STD
    bands, start = [], None
    for y, u in enumerate(uniform):
        if u and start is None:
            start = y
        elif not u and start is not None:
            if y - start >= GUTTER_MIN:
                bands.append((start + base_y, y + base_y))
            start = None
    if start is not None and len(uniform) - start >= GUTTER_MIN:
        bands.append((start + base_y, len(uniform) + base_y))
    return bands


def font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def draw_ruler(draw: ImageDraw.ImageDraw, virtual_top: int, height: int, gutter_set: set[int]):
    """Ruler on the left edge: ticks + labels in virtual coordinates."""
    y = 0
    while y < height:
        vy = virtual_top + y
        major = vy % TICK_MAJOR == 0
        minor = vy % TICK_MINOR == 0
        if major or minor:
            x_end = RULER_W if major else RULER_W - 14
            color = (255, 255, 0) if major else (120, 120, 120)
            draw.line([(RULER_W - 2, y), (x_end + 2, y)], fill=color, width=2 if major else 1)
        if major:
            draw.text((2, max(0, y - 12)), str(vy), fill=(255, 255, 0), font=font(22))
        y += 1
    for gy in gutter_set:
        if virtual_top <= gy < virtual_top + height:
            ly = gy - virtual_top
            draw.line([(RULER_W, ly), (RULER_W + 60, ly)], fill=(255, 60, 60), width=2)


def cmd_views(args):
    cdir = Path(args.chapter)
    files = chapter_files(cdir)
    sizes = file_sizes(files)
    offs = offsets(sizes)
    total_h = offs[-1] + sizes[-1][1]
    out_dir = cdir / "views"
    out_dir.mkdir(exist_ok=True)

    # propose stage: collect gutter candidate lines across all files
    all_gutters: set[int] = set()
    per_file = {}
    for f, (w, h), base in zip(files, sizes, offs):
        with Image.open(f) as im:
            bands = gutter_lines(im, base)
        per_file[f.name] = [[s, e] for s, e in bands]
        for s, e in bands:
            all_gutters.add((s + e) // 2)

    manifest = {
        "chapter": str(cdir),
        "total_virtual_height": total_h,
        "overlap": args.overlap,
        "files": [
            {"name": f.name, "virtual_start": o, "height": h, "width": w}
            for f, (w, h), o in zip(files, sizes, offs)
        ],
        "gutter_candidates": per_file,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))

    # render view pieces with ruler + gutter overlays; pieces OVERLAP so seams
    # are visible from both sides and panels straddling a boundary are never
    # judged from half their body
    step = args.piece_height - args.overlap
    tops = list(range(0, max(total_h, 1), step))
    if tops[-1] != 0 and tops[-1] + args.piece_height < total_h:
        tops.append(total_h - args.piece_height)
    for top in tops:
        bot = min(total_h, top + args.piece_height)
        canvas = Image.new("RGB", (RULER_W + args.width, bot - top), (24, 24, 24))
        draw = ImageDraw.Draw(canvas)
        y = top
        while y < bot:
            fi = max(j for j, o in enumerate(offs) if o <= y)
            f, (w, h), o = files[fi], sizes[fi], offs[fi]
            sy, sy_end = y - o, min(h, bot - o)
            if sy >= h:
                y = o + h
                continue
            with Image.open(f) as im:
                piece = im.crop((0, sy, w, sy_end))
            canvas.paste(piece, (RULER_W, y - top))
            y = o + sy_end
        in_gutters = {g for g in all_gutters if top <= g < bot}
        draw_ruler(draw, top, bot - top, in_gutters)
        name = f"v{top:06d}.png"
        canvas.save(out_dir / name)
    print(json.dumps({
        "chapter": str(cdir), "views": len(tops), "out_dir": str(out_dir),
        "total_virtual_height": total_h, "overlap": args.overlap,
        "gutter_candidate_count": len(all_gutters),
        "note": "ruler labels = VIRTUAL y coords; red lines = gutter candidates; pieces overlap by "
                + str(args.overlap) + "px so seams are judged with full context",
    }, indent=1))


def cmd_window(args):
    """Render any y-band at full resolution with ruler — the agent's zoom lens
    for judging piece-seam regions and uncertain boundaries."""
    cdir = Path(args.chapter)
    files = chapter_files(cdir)
    sizes = file_sizes(files)
    offs = offsets(sizes)
    total_h = offs[-1] + sizes[-1][1]
    y0, y1 = args.y0, min(args.y1, total_h)
    all_gutters: set[int] = set()
    for f, (w, h), base in zip(files, sizes, offs):
        with Image.open(f) as im:
            for s, e in gutter_lines(im, base):
                all_gutters.add((s + e) // 2)
    canvas = Image.new("RGB", (RULER_W + args.width, y1 - y0), (24, 24, 24))
    draw = ImageDraw.Draw(canvas)
    y = y0
    while y < y1:
        fi = max(j for j, o in enumerate(offs) if o <= y)
        f, (w, h), o = files[fi], sizes[fi], offs[fi]
        sy, sy_end = y - o, min(h, y1 - o)
        if sy >= h:
            y = o + h
            continue
        with Image.open(f) as im:
            piece = im.crop((0, sy, w, sy_end))
        canvas.paste(piece, (RULER_W, y - y0))
        y = o + sy_end
    in_gutters = {g for g in all_gutters if y0 <= g < y1}
    draw_ruler(draw, y0, y1 - y0, in_gutters)
    out_dir = cdir / "views"
    out_dir.mkdir(exist_ok=True)
    p = out_dir / f"window_{y0:06d}_{y1:06d}.png"
    canvas.save(p)
    print(json.dumps({"image": str(p), "range": [y0, y1]}))


def cmd_gutters(args):
    cdir = Path(args.chapter)
    files = chapter_files(cdir)
    sizes = file_sizes(files)
    offs = offsets(sizes)
    out = {}
    for f, (w, h), base in zip(files, sizes, offs):
        with Image.open(f) as im:
            out[f.name] = gutter_lines(im, base)
    print(json.dumps(out, indent=1))


def cmd_continuation(args):
    cdir = Path(args.chapter)
    files = chapter_files(cdir)
    a, b = files[args.file_index], files[args.file_index + 1]
    k = args.overlap
    with Image.open(a) as ia, Image.open(b) as ib:
        wa, ha = ia.size
        wb, hb = ib.size
        bottom = ia.crop((0, ha - k, wa, ha))
        top = ib.crop((0, 0, wb, min(k, hb)))
        h = max(bottom.size[1], top.size[1])
        canvas = Image.new("RGB", (wa + wb + 12, h), (40, 40, 40))
        canvas.paste(bottom, (0, 0))
        canvas.paste(top, (wa + 12, 0))
        out = cdir / "views"
        out.mkdir(exist_ok=True)
        p = out / f"continuation_{args.file_index:03d}_{a.stem}_{b.stem}.png"
        canvas.save(p)
    print(json.dumps({"image": str(p), "left": a.name, "right": b.name,
                      "question": "does the same panel/artwork continue from left edge to right edge?"}))


def cmd_crop(args):
    cdir = Path(args.chapter)
    files = chapter_files(cdir)
    sizes = file_sizes(files)
    offs = offsets(sizes)
    total_h = offs[-1] + sizes[-1][1]

    def locate(vy: int):
        fi = max(j for j, o in enumerate(offs) if o <= vy)
        return fi, vy - offs[fi]

    beats_draft = json.loads(Path(args.beats).read_text())
    beats = beats_draft["beats"] if isinstance(beats_draft, dict) else beats_draft
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    index = []
    for i, b in enumerate(sorted(beats, key=lambda x: x["y_start"])):
        y0, y1 = int(b["y_start"]), int(b["y_end"])
        if not (0 <= y0 < y1 <= total_h):
            print(f"SKIP beat {i}: bad range {y0}-{y1}", file=sys.stderr)
            continue
        fi0, fy0 = locate(y0)
        fi1, fy1 = locate(y1 - 1)
        if fi0 == fi1:
            with Image.open(files[fi0]) as im:
                piece = im.crop((0, fy0, sizes[fi0][0], fy1 + 1))
        else:
            parts = []
            for j in range(fi0, fi1 + 1):
                w, h = sizes[j]
                sy0 = fy0 if j == fi0 else 0
                sy1 = fy1 + 1 if j == fi1 else h
                with Image.open(files[j]) as im:
                    parts.append(im.crop((0, max(0, sy0), w, min(h, sy1))))
            piece = Image.new("RGB", (sizes[fi0][0], sum(p.size[1] for p in parts)))
            yy = 0
            for p in parts:
                piece.paste(p, (0, yy))
                yy += p.size[1]
        trim_box = None
        if args.trim:
            piece, trim_box = auto_trim(piece)
        name = f"beat_{i:04d}.png"
        piece.save(out_dir / name)
        index.append({
            "beat": i, "file": name, "y_start": y0, "y_end": y1,
            "w": piece.size[0], "h": piece.size[1], "trim_box": trim_box,
            "composition": b.get("composition", "unknown"),
            "focal_point": b.get("focal_point"),
            "event": b.get("event", ""),
        })
    (out_dir / "beats.json").write_text(json.dumps(index, indent=1))
    print(json.dumps({"exported": len(index), "out_dir": str(out_dir)}, indent=1))


def main():
    ap = argparse.ArgumentParser(prog="toonkit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("views")
    v.add_argument("chapter")
    v.add_argument("--piece-height", type=int, default=2000)
    v.add_argument("--width", type=int, default=720)
    v.add_argument("--overlap", type=int, default=300)
    v.set_defaults(func=cmd_views)

    w = sub.add_parser("window")
    w.add_argument("chapter")
    w.add_argument("--y0", type=int, required=True)
    w.add_argument("--y1", type=int, required=True)
    w.add_argument("--width", type=int, default=720)
    w.set_defaults(func=cmd_window)

    g = sub.add_parser("gutters")
    g.add_argument("chapter")
    g.set_defaults(func=cmd_gutters)

    c = sub.add_parser("continuation")
    c.add_argument("chapter")
    c.add_argument("file_index", type=int)
    c.add_argument("--overlap", type=int, default=800)
    c.set_defaults(func=cmd_continuation)

    p = sub.add_parser("crop")
    p.add_argument("chapter")
    p.add_argument("--beats", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--no-trim", dest="trim", action="store_false",
                   help="disable auto-trim of uniform margins (default: on)")
    p.set_defaults(func=cmd_crop, trim=True)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
