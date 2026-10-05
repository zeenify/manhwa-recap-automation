# STITCHER AGENT — chapter-range compilation builder

Trigger: the user says "stitch chapters X-Y of <series>" (e.g. "stitch chapter
1-10 of return-of-the-top-class-master"). This file is the complete runbook.

What it produces: ONE YouTube-ready compilation mp4 — chapter videos joined in
order with styled transition cards between them, an outro card, a printed
YouTube-chapters timestamp block, a `youtube_timestamps.json` companion, and
an upload-prep doc with the timestamps embedded in a ready-to-paste
description.

## Rules you cannot change

- **The first chapter of the range gets NO transition card** — it starts cold
  (the tool does this itself: cards only go before chapters 2..N of the range,
  so "stitch 11-20" opens directly on chapter 11). Never add one manually.
- Never mention the chapter range or total runtime in a future YouTube TITLE
  (user rule from the wimp upload prep). The chapters block belongs in the
  DESCRIPTION, not the title.
- Chapter sources are `videos/<slug>/chNNN/chNNN.mp4` — the tool aborts if any
  is missing. Do not improvise sources.

## Inputs to collect

1. **slug** — e.g. `return-of-the-top-class-master`, `a-wimps-strategy-guide`.
2. **range** — first..last chapter numbers.
3. **series display name** (for the outro card + card top line, rendered in
   caps) and an optional **sub-line** (tagline; empty string omits it).
   Known series:
   - `a-wimps-strategy-guide` → "A WIMP'S STRATEGY GUIDE" / "TO CONQUER THE TOWER"
   - `return-of-the-top-class-master` → "RETURN OF THE TOP CLASS MASTER" / ""
   If a series is unknown, take the name from `story-so-far.md` or ask the user.

## Command

```bash
export PATH="/c/ffmpeg/bin:$PATH"   # session PATH can lose ffmpeg
python tools/compile_video.py \
  --from <first> --to <last> \
  --slug <slug> \
  --series "<SERIES DISPLAY NAME>" \
  --sub "<TAGLINE OR EMPTY>" \
  --out videos/<slug>/compilation/ch<first03>-ch<last03>_full.mp4
```

Defaults exist for the wimp series (all three series args) — other series MUST
pass `--slug` at minimum. Workdir defaults to `tmp/compile/<slug>`; card PNGs +
intermediates land there.

**Run it in the background** — the final re-encode pass takes roughly as long
as the compilation's own runtime ÷ encode speed (a 1-2 hour compilation is a
30-90 min wait). Do not block on it; report that it's running.

## What the tool does (so you can explain/verify)

1. Renders a 2.5s card per following chapter: dark bg, gold series name, big
   white "CHAPTER N", gold divider, gray tagline. 0.4s fade in/out.
2. ffprobe-measures every chapter, builds the YouTube chapters timestamps.
3. Lossless concat ([ch_first] [card] [ch] ... [card] [ch] [outro 10s]) →
   one clean re-encode (h264 1920x1080 30fps crf18, aac 44.1k mono) with
   +faststart.
4. Prints the chapters block and writes `youtube_timestamps.json` next to the
   output (per-chapter start times + how_to_apply for the YouTube upload).

## Verification (after the background job finishes)

1. `ffprobe` the output: duration ≈ sum(chapter durations) + 2.5s × (N−1)
   cards + 10s outro; resolution 1920×1080; h264 + aac.
2. Confirm `youtube_timestamps.json` exists next to it and its first chapter
   starts at "0:00".
3. Optional spot-check: extract a frame at a card boundary
   (`ffmpeg -ss <t> -i out.mp4 -frames:v 1 tmp/check.png`) and eyeball one
   transition card.

## Timestamps + upload prep (mandatory final step — the tool alone is not enough)

The tool writes `youtube_timestamps.json` and prints the chapters block, but
the AGENT must turn that into an upload-ready document. Write
`channel/<slug>/upload-prep-compilation-chXXX-chYYY.md` (template:
`channel/a-wimps-strategy-guide/upload-prep-merged-video.md`) containing:

1. **Files** — compilation path + duration, thumbnail status (build one via
   `agents/thumbnail-agent.md` if none exists for this compilation).
2. **Title options** (2–3) — power-word hook pattern, user rule: NEVER the
   chapter range or runtime in the title.
3. **Description** — the chapters block MUST be the very first lines (first
   line `0:00 Chapter N`, ascending, ≥3 entries — that is what makes YouTube
   auto-chapters work), THEN the standard description template: "Manhwa
   Summary:" hook, fully-edited/commentary line, 📖 Series block (+ official
   link if one exists), rating question, subscribe line with cadence, fair-use
   line. Copy the chapters block verbatim from the tool output or
   `youtube_timestamps.json.chapters_block` — never re-type timestamps by
   hand.
4. **Tags** line.
5. **Upload-day checklist** — Studio upload, metadata from this doc,
   thumbnail, playlist, audience not-made-for-kids, HD check, pinned comment.

Report both the chapters block and the prep-doc path to the user.

## Notes

- The old wimp compilation file (ch001-020, 5h43m) was removed from the laptop
  on 2026-10-05 to free 13GB (user has a flashdrive copy) — it is fully
  regenerable with this tool: `--from 1 --to 20` with the wimp defaults.
- Card look is defined in `tools/compile_video.py` (`make_card`): edit only in
  the main session, never from subagents.
