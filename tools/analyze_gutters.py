"""Quick analysis: can gutter detection find panel boundaries in scraped strips?

Runs on one strip, reports candidate cut bands (near-uniform horizontal runs),
and saves downscaled previews for visual inspection.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

def gutter_bands(img, min_band=10, std_thresh=14.0):
    g = np.asarray(img.convert("L"), dtype=np.float32)
    row_std = g.std(axis=1)
    uniform = row_std < std_thresh
    bands = []
    start = None
    for y, u in enumerate(uniform):
        if u and start is None:
            start = y
        elif not u and start is not None:
            if y - start >= min_band:
                bands.append((start, y, float(g[start:y].mean())))
            start = None
    if start is not None and len(uniform) - start >= min_band:
        bands.append((start, len(uniform), float(g[start:].mean())))
    return bands

def main(path, preview_pieces=4):
    img = Image.open(path)
    w, h = img.size
    bands = gutter_bands(img)
    print(f"{path}  {w}x{h}")
    print(f"uniform bands >= {10}px: {len(bands)}")
    for s, e, m in bands[:40]:
        print(f"  y {s:>6}-{e:>6}  h={e-s:>4}  brightness={m:.0f}")
    # preview: downscale and slice for viewing
    pw = 220
    prev = img.resize((pw, int(h * pw / w)), Image.LANCZOS)
    ph = prev.size[1]
    piece_h = ph // preview_pieces
    out_dir = Path("tmp/preview")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(path).stem
    for i in range(preview_pieces):
        top, bot = i * piece_h, min(ph, (i + 1) * piece_h)
        prev.crop((0, top, pw, bot)).save(out_dir / f"{stem}_p{i}.png")
    print(f"previews saved to tmp/preview/{stem}_p*.png")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "toonverse/a-wimps-strategy-guide/chapter-01/001.jpg")
