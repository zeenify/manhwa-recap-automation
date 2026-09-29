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
- Zero-padded sequential numbering (`001.jpg`, `002.jpg`, …) with **no gaps** —
  the tools concatenate them into one virtual coordinate space per chapter.
- One folder per chapter, two-digit (`chapter-01`), matching the `chapter=chNNN`
  argument used by the tools (`ch001` ↔ `chapter-01`).
- Watermarks/site banners inside the scans are fine — the reader agents are
  trained (in `agents/reader-agent.md`) to exclude them from the crops.

Everything else in the pipeline is derived from these images. Nothing in this
folder should be committed to git — scans are heavy and are not yours to
redistribute (see the legal note in the root README).

**How you obtain the scans is up to you** — this repository intentionally ships
no scraper. Only process content you have the rights to use.
