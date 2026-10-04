# manhwa-recap pipeline

An **AI-agent-driven production line** that turns manhwa/webtoon chapters into
narrated YouTube-style recap videos: AI reader agents judge the panel layout of
scanned chapters, a writer agent narrates the story in a fixed comedy persona, a
TTS engine speaks it, and an ffmpeg assembler renders a 1080p MP4 with synced
camera moves — end to end, about one chapter per working session.

```
your scans (toonverse/<slug>/chapter-NN/*.jpg)
        │
        ▼
  toonkit views ──► overlapping ruler-annotated reading pieces
        │
        ▼
  READER AGENTS (AI vision) ──► beat boundaries: which pixels are one panel,
        │                        which bubbles/captions are narration-only
        ▼
  merge_drafts ──► one beat list per chapter (seams fused, duplicates dropped)
        │
        ▼
  toonkit crop ──► one PNG per beat + beats.json (the contract)
        │
        ▼
  writer_brief ──► ONE pre-digested brief for the writer agent
        │
        ▼
  WRITER AGENT ──► narration script in the channel persona (tone.md is law)
        │
        ▼
  tts_generate (fish.audio) ──► one mp3 per script entry + timing.json
        │                        (audio duration IS the screen time)
        ▼
  assemble (ffmpeg) ──► 1920×1080/30fps MP4: blurred-pad cards, camera moves,
        │                side-by-side collages for merged beats
        ▼
  videos/<slug>/chNNN/chNNN.mp4
```

The design principle: **the AI agent is the reader and the writer; the Python
tools only execute its decisions.** Panel-judging and narration are vision and
language problems that automation gets wrong — so they're given to an agentic
coding assistant (ZCode, Claude Code, Cursor, …) working from protocol files in
this repo, while cropping, merging, TTS, and rendering stay deterministic.

## Requirements

- **Python 3.11+** with `Pillow` and `numpy` (`pip install -r requirements.txt`)
- **ffmpeg 8.x** on PATH (`ffprobe` too)
- **A fish.audio account + API key** (TTS; the free tier handled full chapters)
- **An agentic coding assistant that can read images** (ZCode, Claude Code, …).
  The reader/writer stages are prompted agent sessions — the protocols in
  `agents/` are written for them.

## Setup

```bash
git clone <this-repo>
cd manhwa-recap-automation
pip install -r requirements.txt
mkdir -p tmp
# put your fish.audio key here (never committed):
echo "sk-fish-..." > tmp/fish_api_key.txt
```

Optional environment overrides for TTS (defaults are the author's voice):

| Variable | Purpose |
|---|---|
| `FISH_API_KEY_FILE` | where the key file lives (default `tmp/fish_api_key.txt`) |
| `FISH_VOICE_ID` | the fish.audio voice to use — **pick your own** |
| `FISH_MODEL` | TTS model (default `s2.1-pro-free`) |

## Bring your own manhwa

Drop the chapter scans into `toonverse/` — see
[toonverse/README.md](toonverse/README.md) for the exact input contract
(one folder per chapter, zero-padded 720px-wide strips).

**A reference scraper is included** (`toonverse/download_chapters.py` — the
author's own tool, written for their workflow; expect it to break as sites
change). Whether you use it or fetch scans another way, **you are responsible
for what you download and process** — only fetch content you have the rights to
use, and check the source for duplicated pages (aggregators sometimes stitch two
scan sources together; reader agents will flag suspicious repeats, and you
should verify and dedupe before cropping).

## Running a chapter

Open your agentic assistant in this folder and give it one instruction:

> Produce chapter 10 for the series in `toonverse/<slug>/` following AGENTS.md's
> NEW CHAPTER RUNBOOK autonomously. Do not ask questions; report at the end.

`AGENTS.md` is the agent's brain: the stage-by-stage runbook, the non-negotiable
quality conventions (window-verified boundaries, art-first crops, flow-rule
narration, audio-as-the-clock sync), and the hard-won gotchas. The agent reads
`agents/reader-agent.md` and `agents/writer-agent.md` when it spawns the
sub-agents that do the actual panel-judging and writing. `tone.md` defines the
narration persona and pacing law — rewrite it to make the channel yours.

Each stage is **idempotent** — re-running skips finished work — and every stage
should be committed to git when it completes, so a bad run is always one
`git checkout -- .` away from recovery.

## What the stages produce

| Stage | Tool/agent | Output |
|---|---|---|
| reading pieces | `tools/toonkit.py views` | `toonverse/<slug>/chapter-NN/views/` |
| beat judging | reader agents (AI) | `beats_draft_*.json` + `handoff_*.json` |
| merging | `tools/merge_drafts.py` | `beats_full_chNN.json` |
| cropping | `tools/toonkit.py crop` | `assets/<slug>/chNNN/beats/` PNGs + `beats.json` |
| writer brief | `tools/writer_brief.py` | `tmp/writer_brief_chNNN.md` |
| narration | writer agent (AI) | `scripts/<slug>/chNNN_script.md` |
| TTS | `tools/tts_generate.py` | `audio/<slug>/chNNN/*.mp3` + `timing.json` |
| render | `tools/assemble.py` | `videos/<slug>/chNNN/chNNN.mp4` (1080p/30fps, AAC) |

## Worked example

`examples/` contains real artifacts from the author's production run (one test
series, 9 chapters produced with this exact pipeline): a finished narration
script, a reader's beat draft, a reader handoff, and a cropped-beats index. When
you boot a fresh agent session, pointing it at these files teaches the format
faster than any description. `story-so-far.md` is the rolling continuity memo —
it is rewritten after every chapter so the next chapter's agents need nothing
older.

## Cost & time expectations (real numbers)

- ~2.5–3.5 h wall clock per 15-minute chapter on a laptop, dominated by the
  AI agents' vision work (3 parallel reader agents, one writer agent)
- TTS: the fish.audio free tier voiced multiple full chapters
- Render: ~20–30 min of ffmpeg per chapter

## Repository layout

```
AGENTS.md      the AI agent's brain — runbook, conventions, gotchas
agents/        per-role protocols the main agent spawns sub-agents from
tone.md        narration persona + pacing law (make it yours)
research/      style bible distilled from a real recap channel's transcript
tools/         deterministic pipeline (crop/merge/brief/TTS/assemble)
story-so-far.md  rolling continuity memo (sample from the author's run)
examples/      real artifacts showing every file format
toonverse/     YOUR scans go here (gitignored; see its README)
scripts/ audio/ videos/ assets/ tmp/   outputs & scratch (gitignored)
```

## Legal note

This repository contains **no scanned pages and no scraped content** — the
included scraper is the author's own reference tool and ships empty-handed. The
sample narration in `examples/` is the author's original transformative
commentary. You are responsible for the content you run through this pipeline —
downloading, narrating and recapping someone else's work without permission may
infringe their rights depending on your jurisdiction and use. Monetizing such
videos on YouTube carries real copyright-strike risk; that business risk belongs
to you, not this repo.
