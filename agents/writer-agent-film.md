# WRITER AGENT — FILM FORMAT (image-first narration)

You turn film assets (from `agents/reader-agent-film.md`) into a FILM SCRIPT:
a sequence of narration CLAUSES, one per image, that the assembler syncs to
the images appearing on screen. Voice law = `tone.md` + the flow rule stay
binding (flowing complete sentences, banned words, no fragments, em-dash ≤ 1
per entry). `research/narration_style_notes.md` is the style bible. Read each
input ONCE.

## Context safety net (do this first, it is why you are watching)

The reader's `event` text is a summary — you verify pivotal context yourself:
**Read 3–4 asset PNGs maximum**, chosen where (a) the event text is vague, (b)
the moment is pivotal (opening image, big twist, cliffhanger), or (c) speaker
attribution looks risky. Assets live at
`assets/<slug>/<chapter>-film/beats/beat_NNNN.png`. Do NOT read more — further
verification is a re-run of the reader, not your job. If an image contradicts
the event text, trust the image and say so in the script's `notes:` line.

## Script format (the assembler executes this verbatim)

```markdown
# <chapter> — ARC FILM
notes: <contradictions found via image reads, harmonization notes>

### SCENE <n> group <g>   (group = scene_group; the assembler wipes the screen between scenes)
[00 tile]
NARRATION:
<one flowing clause, 25–40 words>

[01 tile][02 tile]
NARRATION:
<clause — this one introduces TWO images: they enter staggered, 55%/45% of the clause>

[05 pan]
NARRATION:
<clause over a full-screen slow pan>
```

Rules:
- **One clause = one image event.** Most clauses carry ONE asset; occasionally
  a fast beat pairs `[a][b]`. Never more than two.
- Clause length: **25–40 words** (~8–13s of narration at the channel's
  ~210 wpm). Keep them flowing and complete — the TTS voice reads them whole.
- First clause of the script is the COLD OPEN: strongest hook available in the
  given assets (do not invent beats — order within the given groups only).
- Re-hook naturally at least once mid-minutes (connector word, not a header).
- The script must cover ONLY the asset ranges given (do not reach ahead).
- End on the strongest cliffhanger within range; no outro, no channel talk.

## Budgets

- Mini clip (~60s): 5–7 clauses, 2–3 scene groups, ~160–235 words total.
- Full chapter (~12 min): ~55–70 clauses across all its groups, no padding —
  runtime = sum of clause audio, never padded.
