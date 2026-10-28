# UPDATE v1 — Film lane ("arc film" format, inspired by Leo's Manhwa)

**Date:** 2026-10-17
**Scope:** new parallel long-form lane alongside the classic per-chapter card
pipeline (classic pipeline untouched — `tools/assemble.py` and friends
unchanged).

## Research (user-verified before implementation)

- `research/leo_manhwa_format_notes.md` — study of Leo's Manhwa (4.3k subs,
  100k+-view 4–15h videos): one binge video per story, ~210 WPM third-person
  plot recitation, square-ish art tiles, blank bubbles, no captions.
- `research/leo_shot_grammar_findings.md` — frame-by-frame verified shot
  grammar: one image per narration clause, image batches, slide-ins, zoom
  creep, full-screen top-down pans for tall/scenic strips, hard cuts between
  batches. Supersedes the earlier "continuous scroll" misread.
- Crop verification against the actual source manhua ("It Turns Out That They
  Are the Protagonists", native 1080×1080 pages): their "crops" are whole
  source pages with text washed — smart cropping ≠ cropping at all for
  paginated sources; for long-strip series the reader adapts instead.

## Tools

- `tools/assemble_film.py` (new) — BATCH-model renderer. One script clause =
  one batch of 1/2/3 images:
  - 1 image: the star — big and centered; a tall strip (h/w ≥ 2.2) promotes
    to a solo full-screen top-down pan.
  - 2 images: balanced left half / right half, no overlap.
  - 3 images: left / middle / right thirds, smaller but screen-filling.
  - Images slide into their slots staggered by narration progress (tile k
    enters at k/n of the clause), gentle zoom creep holds, and the whole
    batch disappears when its clause ends — no leftovers. Scene-group changes
    get a white-flash wipe. Narration audio is the clock. Rendered frames piped
    to x264.
  - Removed during review (wrong vs batch grammar or unneeded): per-slide
    accumulation, endless drift, pop-out tile evictions, weak background
    blur, experimental text-wash (bubbles stay readable — that is the
    channel's look by owner decision).
- `tools/toonkit.py` — `crop` supports optional per-beat `x_start`/`x_end`
  x-windows (film tiles can zoom horizontally) and passes `film_class` /
  `scene_group` through to the exported beats.json.

## Agents (new stage protocols; classic reader/writer untouched)

- `agents/reader-agent-film.md` — adaptive smart-crop reader: given the crop
  GOAL (tiles aspect 0.85–1.4 with focal x-windows, pans for continuous
  strips, skips for junk/watermarks/title cards), it inventories the chapter's
  own layout and reasons out its crops per series — no native-page or
  rigid-shape assumptions. Output: `film_assets.json`.
- `agents/writer-agent-film.md` — image-first film writer: one flowing clause
  per scheduled image (25–40 words, channel voice at ~210 WPM), batch tags
  `[NN tile]` / `[NN pan]`, scene-group wipes, and a mandatory image
  SAFETY-NET: the writer Reads 3–4 pivotal asset PNGs to verify context.
  Caught two real reader mis-descriptions on its first run.

## Test production (return-of-the-top-class-master ch001)

- Film assets: 66 tiles + 5 pans + 13 scene groups, all aspects in spec, 16
  x-window crops, adaptive splits where slicing would cut a figure.
  - Draft: `toonverse/return-of-the-top-class-master/chapter-01/film_assets.json`
  - Crops: `assets/return-of-the-top-class-master/ch001-film/beats/`
- 70s proof film (full chain: reader → film-writer → per-clause TTS with the
  default voice → batch assembler):
  `videos/return-of-the-top-class-master/films/ch001_film_60s.mp4`
  (1080p30, narration sync to the frame).
