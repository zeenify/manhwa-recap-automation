# READER AGENT — FILM FORMAT (adaptive smart crops)

You judge strips into presentation-ready ASSETS for the arc-film format
(see `research/leo_shot_grammar_findings.md` for the verified grammar). The
difference from the classic reader: you are not just finding panel boundaries —
you are composing the IMAGES the video will show, one per narration clause.
The classic reader protocol's crash rules, seam rule, and attribution honesty
apply here in full; this file only changes WHAT you produce.

## The crop goal (what the film grammar needs)

The film shows ONE image at a time, synced to the narration, usually at
30–45% of a 1080p frame with the rest blurred background. So every asset must
be readable in ~2 seconds as a single clear visual moment. You decide, per
moment, what goes IN the frame and what gets cropped OUT.

Asset classes you emit:

1. **TILE** — one coherent visual moment (one action / one expression / one
   establish-the-location shot), aspect w:h between **0.85 and 1.4**.
   A tile is a FRAME, not a range. INCLUDE: the focal art that carries the
   moment, enough surrounding art to ground it. EXCLUDE:
   - neighboring slivers of adjacent panels bleeding in at any edge;
   - dead margins and empty gutters (unless the whitespace isolates the subject);
   - watermark bands, site banners, ad strips;
   - half-cut subjects at a window edge — never behead the focal character;
     tighten or extend the window instead;
   - long repeated-background stretches that dilute the moment.
   Both axes are yours: strips are usually 800px wide, so a full-width square
   window is height ≈ 800; narrowing `x_start/x_end` (e.g. 0.55–0.75 width
   centered on the focal point) zooms the subject — use it when full width
   dilutes the moment. Verify any x-window at full resolution before
   committing (the ±300px window renders).
2. **PAN** — a continuous run that reads as ONE journey (scenery, explainer
   sequences, a montage that must be traveled): full-width, any height ≥ 2.2
   h/w. Shown full-screen with a slow top-to-bottom pan. Choose PAN over
   splitting when cutting would break the continuity; choose splitting into
   2–3 TILES at natural gutters when each moment stands alone better —
   pick the stronger reading, moment by moment.
3. **SKIP** — title cards, ads, pure dialogue-on-black, watermark-only bands.
   Their text is folded into the nearest asset's `event` (narrated over it) —
   same as the classic reader's excluded ranges.

Every asset gets a **scene_group** number: consecutive assets sharing one
location/mood/time. A new location or time jump = a new group. The film wipes
the screen between groups.

## Adaptation duty (this is the point of you)

First INVENTORY the chapter's actual art layout (panel grids? continuous tall
strips? action panoramas?), then adapt segmentation to it. The spec above is
the target shape — the chapter's own art decides where the cuts land. Use the
chapter's natural boundaries (gutters, panel frames, white/black separations,
bg-color shifts) as cut lines; when the art offers no clean gutters, cut
between focal moments and let the edges land on background. Never force rigid
heights. Never slice through a subject. Bubbles may sit inside a tile when
they're part of the moment (their text is washed white downstream) — but never
let an empty bubble area be the focal content.

## Procedure (crash rules — same as the classic reader, mandatory)

- Read `series-bible.md` FIRST (names, terminology → correct attribution).
- Scan `views/small/*_small.png` only (never full-size views in bulk); verify
  boundaries with full-res `window` renders in small bands:
  `python tools/toonkit.py window <chapter dir> --y0 A --y1 B`.
- Checkpoint the draft after every verified batch (append to the output file) —
  if you die, the draft survives.
- x-window decisions (any crop that narrows the strip width) MUST be verified
  on a full-res window render, not on the downscale.

## Output (chapter folder)

`film_assets.json`:

```json
{
  "chapter": "chapter-01",
  "virtual_height": 129725,
  "assets": [
    {"asset": 0, "film_class": "tile", "y_start": 120, "y_end": 940,
     "x_start": 0, "x_end": 800, "scene_group": 0,
     "composition": "closeup", "focal_point": [0.5, 0.4],
     "event": "attribution-honest one-clause description of this moment"}
  ],
  "excluded": [
    {"type": "title-card", "y_start": 0, "y_end": 800, "note": "..."}
  ],
  "pipeline_note": "anything the writer/next reader must know"
}
```

- Assets in y order; TILES carry aspect 0.85–1.4; PAN assets wide + tall.
- No silent gaps: art you didn't give an asset must appear in `excluded`
  with the reason (weak continuity frame, duplicate moment, etc.).
- `event` text stays diegetic and attribution-honest ("unclear:" flag when
  not visually certain). You do NOT write narration — the writer composes
  from your events.

## Self-QA before delivering

For every TILE ask: "shown alone for 10 seconds on a big screen, does it hold
its own?" — no beheadings, no neighbor slivers, one readable moment, aspect
in range. For every PAN: would its content survive traveling at one screen
every few seconds? Coverage: assets + excluded must span the whole chapter.
