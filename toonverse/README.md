# toonverse/ — your source scans go here

This folder holds the RAW INPUT to the pipeline: one sub-folder per series, one
sub-folder per chapter, containing the chapter's images as read top-to-bottom.

## Input contract (what the pipeline expects)

```
toonverse/<your-series-slug>/
  chapter-01/
    001.jpg
    002.jpg
    ...
  chapter-02/
    001.jpg
    ...
```

- Each image is a TALL vertical slice of the chapter (webtoon-style strips),
  roughly **720 px wide**; height can vary (5k–12k px is normal).
- `.jpg`, `.png` and `.webp` are all accepted (one format per chapter folder is
  cleanest — the tools sort by filename).
- Zero-padded sequential numbering (`001.jpg`, `002.jpg`, …) with **no gaps** —
  the tools concatenate them into one virtual coordinate space per chapter.
- One folder per chapter, two-digit (`chapter-01`), matching the `chapter=chNNN`
  argument used by the tools (`ch001` ↔ `chapter-01`).
- Watermarks/site banners inside the scans are fine — the reader agents are
  trained (in `agents/reader-agent.md`) to exclude them from the crops.

Everything else in the pipeline is derived from these images. Nothing in this
folder should be committed to git — scans are heavy and are not yours to
redistribute (see the legal note in the root README).

**How you obtain the scans is up to you.** A reference scraper
(`download_chapters.py`, written for the author's own workflow) sits in this
folder — expect it to break as sites change, and remember you are responsible
for what you fetch: only download content you have the rights to use.

Using the reference scraper: open it and edit the constants at the top
(`SERIES` = the site's series slug, `FIRST`/`LAST` = chapter numbers,
`WORKERS`), then run `python toonverse/download_chapters.py` from the repo
root. Two things it does NOT do for you:

1. it writes `toonverse/chapter-NN/` straight into `toonverse/` — **move each
   chapter folder under your series slug** (`toonverse/<slug>/chapter-NN/`),
   which is where the pipeline looks;
2. it keeps the site's page filenames — the pipeline expects zero-padded
   `001.jpg, 002.jpg, …` with no gaps, so rename if your source names differ.
