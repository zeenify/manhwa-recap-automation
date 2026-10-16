# PIPELINE UPDATES — track record

Newest first. One entry per shipped change to the pipeline (tools, agents,
research, formats). Dated.

---

## 2026-10-17 — Film lane v1 ("arc film" format, inspired by Leo's Manhwa)

New parallel long-form lane alongside the classic per-chapter card pipeline
(classic pipeline untouched — `tools/assemble.py` and friends unchanged).

**Research** (findings committed before implementation, user-verified):
- `research/leo_manhwa_format_notes.md` — study of Leo's Manhwa (4.3k subs,
  100k+-view 4–15h videos): one binge video per story, ~210 WPM third-person
  plot recitation, square-ish art tiles, blank bubbles, no captions.
- `research/leo_shot_grammar_findings.md` — frame-by-frame verified shot
  grammar: one image per narration clause, images accumulate to 1–3 per
  screen, slide-ins, zoom creep, full-set swaps, full-screen top-down pans
  for tall/scenic strips, hard cuts between batches. Supersedes the earlier
  "continuous scroll" misread.
- Crop verification against the actual source manhua: their "crops" are whole
  1080×1080 native pages with text washed — smart cropping ≠ cropping at all
  for paginated sources.

**Tools**:
- `tools/assemble_film.py` (new) — BATCH-model renderer. One script clause =
  one batch of 1/2/3 images: singles big & centered (tall strips auto-promote
  to full-screen top-down pans), pairs balanced left/right halves, triples in
  thirds; images slide in staggered by narration progress (tile k enters at
  k/n of the clause), zoom creep holds, whole batch replaced when its clause
  ends (no leftovers), white-flash wipe on scene-group changes, narration
  audio is the clock. Pulled-frames → x264 via stdin.
  - Removed during review: per-slide accumulation (wrong vs batch grammar),
    endless drift, pop-out tile evictions, weak background blur, an
    experimental text-wash (deemed unnecessary — bubbles stay readable;
    that is the channel's look).
- `tools/toonkit.py` — `crop` now supports optional per-beat `x_start`/`x_end`
  x-windows (film tiles can zoom horizontally) and passes through
  `film_class` / `scene_group` into the exported beats.json.

**Agents** (new stage protocols, classic reader/writer untouched):
- `agents/reader-agent-film.md` — adaptive smart-crop reader: given the crop
  GOAL (tiles aspect 0.85–1.4 with focal x-windows, pans for continuous
  strips, skips for junk), it inventories the chapter's own layout and
  reasons out the crops per series — no native-page or rigid-shape
  assumptions. Output: `film_assets.json`.
- `agents/writer-agent-film.md` — image-first film writer: one flowing clause
  per scheduled image (25–40 words, ~210 WPM of the channel voice), batch
  tags `[NN tile]` / `[NN pan]`, scene-group wipes, and a mandatory image
  SAFETY-NET: the writer Reads 3–4 pivotal asset PNGs to verify context —
  caught two real reader mis-descriptions on its first run.
- Also updated: `agents/writer-agent-film.md` batch semantics documented.

**Test production** (return-of-the-top-class-master ch001):
- Film assets: 66 tiles + 5 pans + 13 scene groups, all aspects in spec, 16
  x-window crops, adaptive splits where slicing would cut a figure
  (`toonverse/return-of-the-top-class-master/chapter-01/film_assets.json`,
  crops at `assets/return-of-the-top-class-master/ch001-film/beats/`).
- 70s proof film: `videos/return-of-the-top-class-master/films/ch001_film_60s.mp4`
  (1080p30, default voice) — full chain run end-to-end: reader → film-writer
  → per-clause TTS (`audio/.../ch001-film/`) → batch assembler.

## 2026-10-15 — prior session notes
- Format study began (Leo's Manhwa metadata + transcript pull,
  `tmp/leo_research/`); earlier scroll/consumption interpretations corrected
  in the findings doc above.
