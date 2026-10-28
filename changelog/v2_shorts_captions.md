# UPDATE v2 — Shorts captions rebuild (one-line center blocks, Akiel-Runes style)

**Date:** 2026-10-28
**Scope:** `tools/assemble_shorts.py` caption engine only — scripts, TTS,
beat assets, and the long-form pipeline untouched. Went through three
iterations in one day (v2 block captions → v3 style copy → v4 motion+sync),
final state recorded here.

## Research (Akiel Runes studied frame by frame)

- Channel: **Akiel Runes @AkielRunes** (98.1k subs, manhwa recommendation
  shorts — the "weird things" source the user pointed at).
- Downloaded 2 of his shorts with yt-dlp (`tmp/reference/`, one at 4K/60fps)
  and watched caption transitions at 60fps magnified 2–2.5×.
- Findings that drove the implementation:
  - Captions are ONE line (2 centered lines when long) **dead-center**, all
    caps, white, **thin** ~3px black stroke (not the fat 7px Hormozi border),
    soft dark drop shadow, rounded-corner chunky bold sans (closest installed
    match: **Rubik Bold**). Settled line letter-gap is wide/open.
  - The signature move: text **never moves position** — each block is born
    CLUMPED (letters near-touching, ~90% of settled width) and its letter
    gaps EXPAND outward to the settled width over ~8 frames (~130ms), then
    the block holds dead still. A long careful zoom revealed the settle is
    eased (decelerating, not an abrupt stop).
  - His blocks pop in at near-full opacity from the first frame — no dim ramp.

## Tools (`tools/assemble_shorts.py` rewrite)

- **Captions are per-frame ASS events** (~1 line per frame; ~1.2k events for
  a 44s short — trivial for libass). Every block emits one event per video
  frame at a fixed dead-center `\pos` anchor, so Python owns all motion.
- **Blockification** (`blockify`) — narration (uppercased) split into blocks
  by PIL-measured Rubik widths at settled tracking; budget = frame width minus
  2×40px margins; prefers sentence ends, then commas, then greedy splits;
  safety pass guarantees a block can never wrap (build prints a loud warning
  if one ever would).
- **Birth pop** (`pop_gap_frac`) — per-frame `\fsp` letter-spacing curve:
  clumped → fast ease-out rise → **~12% overshoot** → sine settle back over
  ~290ms total (user: "it doesn't just stop when it's expanded").
- **Vibration** (`jitter_xy`) — continuous ~1px sine wobble per axis at
  8–13Hz on the `\pos` anchor; mean position never drifts (user: "it's
  vibrating a little, very subtly"). Deterministic per block → re-renders
  are identical.
- **Perfect TTS↔caption sync** (user: "as soon as the TTS says it") — two
  layers:
  - faster-whisper is BACK, but only for **block-boundary anchoring** (no
    word karaoke): when whisper's token count matches the script, each
    block's birth = the real spoken onset of its first word; on token
    mismatch, blocks spread proportionally across the REAL speech window.
  - **Frame-exact segment allocation** (`split_frames`): an entry's video
    length now always equals its mp3 duration (Bresenham split across its
    beats, `-frames:v` pinned per segment) — kills the old cumulative A/V
    rounding drift that made captions late ~0.1–0.2s by the end of a short.
- Font: Rubik Bold 96px (same 67px cap height as before), Arial Black
  fallback for machines without Rubik. Thin outline 3px (was 7), soft blurred
  shadow, SNAP-in (frame-0 alpha 62%, then full opacity — matches the
  reference's instant pop; no more 60ms dim ramp).
- Sample re-render verified end to end: pop curve measured from ASS
  (-6.1 → 7.64 peak → 6.17 settled), `\pos` oscillates ±1px around center,
  and the first caption birth lands at 0.00s exactly where silencedetect
  hears the voice start.

## House style (v4, recorded in the law docs)

`research/shorts_style_notes.md` caption spec + `AGENTS.md` updated so the
style (and the "never restore" list: per-word karaoke, multi-line cards,
bottom/top anchors, thick borders) survives future edits. Knobs if tuning is
wanted: `CAP_FSP_TWEEN` (clump depth), `CAP_POP_MS`, `CAP_POP_OVERSHOOT`,
`CAP_JITTER`. Reference strips live in `tmp/caption_sample/` (ours) and
`tmp/reference/` (Akiel runs) for side-by-side eyeballing.
