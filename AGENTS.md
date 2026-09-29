# AGENTS.md — manhwa-recap pipeline

Manhwa/webtoon chapters → narrated YouTube-style recap videos. Scanned chapters
in `toonverse/` are judged into panel "beats" by AI reader agents, narrated by a
writer agent in a fixed persona, voiced via fish.audio TTS, and rendered to MP4
by an ffmpeg assembler.

**You (the agent) are the reader and the writer; the tools only execute your
decisions.** `README.md` is the human onboarding guide; this file is YOUR brain:
the stage-by-stage runbook, the non-negotiable quality conventions, and the
gotchas. `tone.md` is the narration persona — law for all writing.
`examples/` holds real artifacts from the author's production run; when any
output format is unclear, match those files.

**Starting a new series:** create `toonverse/<slug>/chapter-01/` with the scans
(see `toonverse/README.md` for the input contract), reset `story-so-far.md` to a
one-line memo, then follow the NEW CHAPTER RUNBOOK at the bottom of this file.
Commit after every successful stage.

## Layout

- `toonverse/<slug>/chapter-NN/NNN.jpg` — scraped source strips (720px wide, ~10k px tall each; one chapter = 8–26 files).
- `tools/toonkit.py` — the only image tooling. Subcommands: `views` (overlapping ruler-annotated reading pieces), `window` (full-res y-band render — the boundary-verification zoom lens), `continuation` (file-seam checker), `gutters` (candidate cut lines), `crop` (export beat PNGs from a beats draft, with auto-trim of uniform margins).
- `tools/merge_drafts.py` — fuses reader-part drafts into one chapter draft. Handles both spawn layouts: sequential adjacent parts (fuses `continues`/`continues_from_previous` seams) and parallel overlapping parts (fuses the beat that completes a range-cut panel, drops duplicate overlap beats; prints coverage warnings).
- `tools/writer_brief.py` — pre-digests beats.json (with aspect ratios) + all handoff synopses + story-so-far into ONE briefing file for the writer agent, so the writer reads 3 files total instead of 7.
- `tools/tts_generate.py` — synthesizes one mp3 per script entry via the fish.audio API (model `s2.1-pro-free`; voice reference_id and API constants live in the script; API key in `tmp/fish_api_key.txt` — treat as secret, never echo or publish). Idempotent (skips existing mp3s), retries on failure, 4 parallel workers by default (`--workers`).
- `tools/assemble.py` — the renderer. Reads beats.json + timing.json + shot directives from the script → renders ONE clip per script entry (a merged entry becomes a side-by-side collage shown for the whole entry's audio; `pan-down` scrolls a 60%-width centered column over the blurred bg — full-width scrolling is gone) → concats → muxes narration → optional music. Outputs `videos/<chapter>/<chapter>.mp4` at 1920×1080/30fps. Idempotent per segment (skips existing clips — **delete `videos/<chapter>/clips/*.mp4` AND the cached `collage_entry_*.png` whenever render settings or beats change**, or stale data gets reused).
- `agents/reader-agent.md`, `agents/writer-agent.md` — permanent agent protocols. **Read the relevant one before doing agent work**; spawn subagents with "follow this file + spawn parameters".
- `tone.md` — channel persona ("Roasting Best Friend") + the **pacing law** (words per beat by screen time). Law for all narration.
- `research/narration_style_notes.md` — verbatim style analysis from a real 636K-sub recap channel's transcript. Style bible for writers.
- `story-so-far.md` — rolling continuity memo, refreshed after every approved chapter script (cap ~1,500 words). Next chapter's agents get this + previous script, nothing older.
- `scripts/` — narration scripts. `assets/<slug>/<chapter>/beats/` — exported beat PNGs + `beats.json` (the contract between all stages).
- `audio/<chapter>/` — per-entry mp3s + `timing.json`: entry → mp3 file, measured `duration_s`, covered beats. **This is the sync contract: an entry's screen time = its narration mp3's duration (audio is the clock).** `videos/`, `tmp/` — outputs and scratch.

## Commands

```bash
python tools/toonkit.py views   toonverse/<slug>/chapter-NN --overlap 300   # regenerate reading pieces
python tools/toonkit.py window  toonverse/<slug>/chapter-NN --y0 A --y1 B  # full-res band render
python tools/toonkit.py crop    toonverse/<slug>/chapter-NN --beats <draft.json> --out assets/<slug>/<chapter>/beats
python tools/merge_drafts.py    --out <merged.json> <part1.json> [<part2.json> <part3.json>]
python tools/writer_brief.py    --slug <slug> --chapter <chapter> --out tmp/writer_brief_<chapter>.md
python tools/tts_generate.py    --script scripts/<chapter>_script.md --out-dir audio/<chapter>
python tools/assemble.py        --slug <slug> --chapter <chapter> --script scripts/<chapter>_script.md
```

Deps: Python 3.11 + Pillow + numpy (already installed). No git repo, no linter, no test suite — verification is visual QA of exported beats and grep checks on scripts.

## Non-negotiable conventions

1. **Virtual coordinates**: pieces/files concatenate into one continuous y-space per chapter; all beat boundaries are virtual y-values. Views are reading windows only — never crop from them, crop reassembles from source files.
2. **Every boundary must be window-verified.** Coordinates eyeballed from tall pieces are wrong by 300–400px (downscaled renders). Rough-locate from pieces, decide only from `window` renders.
3. **Art-only beats.** Dialogue bubbles on black and narration captions are narrated over the nearest art beat (`excluded` ranges), never cropped as beats. Bubbles spilling from art into whitespace are clipped at the art's edge (the beat ends where the art ends; the spillover is excluded and its text spoken over the beat) — bubble-chasing tall crops are a defect. Site junk (THUNDERSCANS banners/promos) is excluded.
4. **Attribution strictness.** Event text states only what is visually certain; ambiguity gets an "unclear:" flag. The writer's harmonization pass fixes attributions with later-chapter context.
5. **Flow rule + diegetic narration** (tone.md): every narration entry is flowing, complete sentences a TTS voice reads naturally — no fragments, colon lead-ins, one-word punchline paragraphs, or "— sigh —" stage directions. Banned words in narration: panel, sound effect, narrator, montage, caption, "all chapter". Grep scripts before delivering. Pacing: typical entry 15–45 words (lore up to ~80); total runtime = sum of audio durations, never padded.
6. **Reader agents split the chapter into 2–3 near-equal ranges (~60–100k virtual
   px each) with 2000px overlaps at the seams.** Run them in PARALLEL when the
   platform allows concurrent subagents (`merge_drafts.py` fuses flagged seams and
   dedups overlap beats); fall back to sequential if spawning is rejected. Each
   agent writes a handoff file the writer later uses as story context.
7. **Camera rules (assembler):** every panel becomes a composed 16:9 card — blurred, darkened copy fills the frame as background, sharp panel centered on top (kills aspect stretching). **No full-width scrolling** (the old full-width pan-down was illegible and dizzying): `pan-down` now scrolls the panel as a **60%-width centered column** over the static blurred background — mild zoom, whole panel width always in frame; panels whose column wouldn't clear the frame height just get `fit`. **A merged entry (writer covered 2 beats) renders as ONE side-by-side collage card for the whole entry's audio** — but only when the panels' heights are comparable (ratio ≤ 1.6, enforced by the assembler; the writer's rule is ~1.5): mismatched sets render as sequential cards instead, because a short panel beside a tall one becomes unreadably tiny. A beat's screen time = its entry's narration mp3 duration.
8. **No background music** unless the user explicitly asks (in the author's
   tests it sat too quietly under constant narration to be worth it).

## Gotchas

- Windows + Git Bash; workspace path contains spaces — always quote.
- Session PATH can silently lose `python` and `ffmpeg` (happened once): use `py`
  for Python (the Windows launcher, always present) and prepend
  `export PATH="/c/ffmpeg/bin:/c/WINDOWS/System32:$PATH"` for ffmpeg/curl runs.
  Tools that shell out (tts_generate→curl, assemble→ffmpeg) inherit the fixed PATH.
- Cross-file beats were the source of a real crop bug (fixed); if crop throws `lower < upper`, check a beat's y_end sitting exactly on a file offset.
- `views/` regenerates with different piece names after changing `--overlap`; old pieces must be deleted first.
- Never edit `tools/*.py` from subagents; only the main session does.
- `story-so-far.md` and `beats.json` are the memory of the project — do not overwrite casually.
- TTS entry filenames must be unique per entry index: two entries can share the same first covered beat (the cold open once collided with a merged beat and its audio was silently overwritten — fixed with index-prefixed names, but older audio folders may not have them).
- fish.audio can return HTTP 200 with an EMPTY body on auth/param failures — verify the output file exists and is >1KB, never trust the status code alone.
- Writer agents' self-reported QA can be wrong (ch10's claimed "all under the cap" shipped 81- and 87-word entries) — the MAIN SESSION always re-verifies coverage, word caps, banned words, and shot directives with the production parsers before spending TTS credits; over-cap entries get edited by hand and their clips re-generated.
- Stale `ffmpeg.exe` processes lock clip files and break cleanup — `taskkill //F //IM ffmpeg.exe` before deleting/re-rendering.
- The concat demuxer resolves relative paths against the LIST FILE's directory — always write absolute forward-slash paths into `segments.txt` / `audio_list.txt`.
- Change a render setting (resolution, filters) without deleting old clips = the idempotent skip silently reuses the stale clips. Purge `videos/<chapter>/clips/` first.

## NEW CHAPTER RUNBOOK (do these in order, per chapter — e.g. chapter 2)

0. **Verify the scrape first**: `toonverse/<slug>/chapter-NN/` must exist with
   zero-padded sequential images and no numbering gaps. If images are missing or
   tiny, STOP and report — do not invent content. Aggregators sometimes stitch
   TWO scan sources together, duplicating a whole sequence with reworded
   captions — if a reader agent flags a suspicious repeat, window-compare the
   regions and dedupe at the beats level before cropping.

0.5 **PREFLIGHT — verify you can see before reading.** Before spawning any reader
   agent: generate views (`python tools/toonkit.py views ...`), then Read ONE view
   image and describe it (panels, bubble text). If images do not come through or
   you cannot describe them, STOP — the model/provider lacks working vision; do
   not run the reader stage blind. Report and wait.

**Version control discipline (overnight safety net):** this is a git repo. Commit
after each successful stage: `git add -A && git commit -m "<stage> done"`.
Everything destructive should be a commit away from recovery. If something looks
demolished: `git checkout -- .` restores tracked files; `git log --oneline` lists
checkpoints. NOTE: images/media/*.mp3/*.mp4 are gitignored (heavy, regenerable).
Never `git clean -fdx` or `git reset --hard` without checking what the previous
commit contains. Do NOT make Desktop backups — the user said they're not needed.

**Speed conventions (agent stages dominate runtime):** subagents run on the
session's model, so keep the session on the fast model when producing a chapter
(DeepSeek-via-NVIDIA ran ~3× slower per turn than GLM). Readers and writers follow
the batching rules in their protocols; TTS runs 4 parallel workers by default.
The window-verification quality rule is NOT relaxed for speed — it is what keeps
crops correct.
1. `python tools/toonkit.py views toonverse/<slug>/chapter-NN --overlap 300`
2. Spawn READER AGENTS — prefer PARALLEL (2–3× faster than sequential; the
   platform rejected 6 concurrent subagents once, so try 3, fall back to 2, then
   to sequential):
   - Split total virtual height into near-equal ranges with 2000px OVERLAP:
     3 agents → A `[0, m1+2000)`, B `[m1−2000, m2+2000)`, C `[m2−2000, END)`;
     2 agents → A `[0, MID+2000)`, B `[MID−2000, END)`.
   - Prompt per agent: "Execute the READER AGENT protocol in
     agents/reader-agent.md exactly. Mode: PARALLEL (ranges overlap your
     neighbors; judge from what you see). Range: [START, END). Output:
     beats_draft_X.json + handoff_X.json (exact paths in the chapter folder)."
   - If concurrent spawning is rejected, run the same agents SEQUENTIALLY (first
     agent's handoff feeds the next).
   - `tools/merge_drafts.py` handles both layouts (fuses flagged seams, drops
     duplicate overlap beats). After merging, window-verify each seam region once.
   Midpoints ≈ equal splits of total_virtual_height.
3. `python tools/merge_drafts.py --out toonverse/<slug>/chapter-NN/beats_full_chNN.json <part1.json> [<part2.json> <part3.json>]`
4. `python tools/toonkit.py crop toonverse/<slug>/chapter-NN --beats <merged.json> --out assets/<slug>/<chapter>/beats`
5. Build the writer brief (ONE file for the writer instead of six reads):
   `python tools/writer_brief.py --slug <slug> --chapter <chapter> --out tmp/writer_brief_<chapter>.md`
   Spawn WRITER AGENT: prompt = "Execute the WRITER AGENT protocol in
   agents/writer-agent.md. Inputs: tmp/writer_brief_<chapter>.md + tone.md +
   research/narration_style_notes.md (read each once, nothing else). Output:
   scripts/<chapter>_script.md." It handles flow rule, pacing, harmonization, QA.
6. `python tools/tts_generate.py --script scripts/<chapter>_script.md --out-dir audio/<chapter>` (idempotent — safe to re-run; ~4 parallel workers by default, expect ~3–5 min)
7. `python tools/assemble.py --slug <slug> --chapter <chapter> --script scripts/<chapter>_script.md` (run in background; ~25–40 min for ~15 min of video)
8. Verify with ffprobe (duration ≈ sum of audio durations; 1920×1080; aac audio).
   Then refresh `story-so-far.md` per the writer protocol's continuity duty —
   the main session can do this directly from the handoffs + script; a subagent
   is unnecessary.
9. If anything fails mid-chain: every stage is idempotent and re-runnable — fix the specific stage, never restart the whole pipeline.
