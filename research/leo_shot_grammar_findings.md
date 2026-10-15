# LEO SHOT GRAMMAR — verified findings (supersedes the "continuous scroll" analysis)

Method: first 60 seconds watched frame-by-frame (0.5s motion-event detection +
1s contact sheets in `tmp/leo_research/fb/`), aligned word-by-word against the
auto-caption timeline. This replaces the earlier "one continuous scroll" and
v2 "train slide" interpretations — both wrong. These findings are for
verification BEFORE implementation.

## The verified grammar, phrase by phrase (0–60s timeline)

| t (s) | Narration (caption-timed) | Visual |
|-------|---------------------------|--------|
| 0.0–0.8 | "Unlike any other heroic story, this one" | **Background only** (blurred art, no tiles). Narration starts on empty stage. |
| 0.8–3 | "…begins in the most ugly way possible." | TILE 1 (the "ugly beginning" panel) slides in FROM THE LEFT, settles left-of-center (~35% width). |
| 4.7–6 | "The thing is, our main character," | TILE 2 (his death scene) slides in FROM THE RIGHT, right-of-center (~30% width). PAIR formed. |
| 6–9.5 | "Marvin, who is 30 years old, dies of a heart attack." | Pair HOLDS (micro creep only). |
| 9.5–10.5 | "dies of a heart attack. This happens while…" | Whole set wipes OUT in one flash; TILE 3 (his face close-up, ~43%) enters FROM TOP-LEFT. |
| 15–16.5 | "Our hero is reborn and finds himself in another world" | TILE 4 (Marvin + the woman who finds him) slides in from bottom-right → pair. |
| 17–21 | "…where he is picked up by a beautiful woman who is very happy to see him." | Pair holds, zoom creeping. |
| 21.5–24 | "She talks about how she was expelled…" | Set wipes; TILE 5 (the woman hugging him, closer crop ~45%) enters from top-left. |
| 28–30 | "…she would like to make him a follower of her cult" | TILE 6 (the sinister red-eyed cult shadow) slides in from the right — **tile content = exact word being spoken** ("cult" → cult panel). |
| 32.5–33 | "…explains that he is unusually talented." | Full-set wipe → **FULL-SCREEN long strip** (the chibi explainer sequence, white bg) begins. |
| 33–39 | "She assures him that the future of the cult is in his hands…" | The long strip **pans top→bottom for ~6s, then ZOOMS into the girl's face** for ~4s. Single art owns the whole screen. |
| 40–44 | "10 long years of training pass, but for our hero, it flies by…" | Back to tiles: TILE 7 (explosion burst) enters small (~25%) and **scales up while creeping** to ~40% over 4s. |
| 44–52 | "6 months ago, his mentor disappeared…" | TILE 8 (meditating in the hall, empty bubbles) slides in top-left, holds ~8s, creeping. |
| 52–56 | "…after which she told him all the necessary secrets…" | TILE 9 (Marvin, sparkles bg) enters from bottom-right → pair. |
| 58–60 | "…the seal was removed and he will finally be able to go out into the world." | Set wipes; new brighter outdoor scene enters. |

## The rules extracted

1. **One image per narration clause. Every image appears ONLY when the
   narration reaches it** — slides in over ~0.8–1.2s with an ease-out, then
   holds. Multiple images ACCUMULATE (1→2→3) as the narration moves through
   the scene; they do not all appear at once. (This was the main v3 defect.)
2. **Tile inventory**: 1–3 square-ish tiles visible at once (~30–45% width
   each, height-staggered left/right of center, never overlapping). Singles
   often start smaller (~25–30%) and scale up as the creep resumes.
3. **Set swap on scene change**: when the narration moves to a new beat/
   subject, the entire current set wipes out (~0.3–0.5s) and the next tile
   enters. Sets live ~10–20s.
4. **Zoom creep between events**: whichever tiles are on screen slowly zoom
   (≈ +8–12% over 4–5s) so the frame is never dead-still.
5. **Full-screen mode for long strips**: scenic/explanatory multi-panel strips
   appear SOLO at (near-)full width and pan slowly top→bottom, sometimes
   finishing with a zoom into a detail. This ran 11+ consecutive seconds. Long
   strips are NEVER cropped into square tiles (second v3 defect — we were
   cutting explainer strips into pairs).
6. **Tile content locks to the spoken words** — images illustrate the exact
   clause being said (the "cult" tile lands on the word "cult").
7. All dialogue bubbles remain blank; no burned captions; site watermarks stay.

## What this means for our pipeline (PROPOSAL — not implemented)

- **Reader**: must hand the assembler asset CLASSES per beat: (a) the beat's
  full-range strip (for full-screen pan presentation of long/explanatory
  stretches), (b) a square-ish focal window crop per beat (for tiles), (c) a
  shape classification (long strip vs panel page), and (d) scene-group labels
  so set swaps align with story beats. Current reader only exports
  panel-boundary crops — "grabbing images" without presentation classes.
- **Writer**: the script must be written **image-first**: one flowing clause
  per scheduled image, e.g. every 1–2 sentences = one beat, marked in the
  script as `[IMG: beat N — slide dir]`, plus `FULL-PAN` marks on long-strip
  beats, and scene-group boundaries where set swaps happen. This replaces
  per-entry blob narration; image schedule = narration structure. This is
  what "the writer should know exactly how to use three/two/one images"
  means — the writer authors the shot list.
- **Assembler**: consumes the written shot list verbatim: tiles enter one at
  a time on their clause, accumulate, creep; full-set wipe at scene-group
  boundaries; full-screen top-down pan for FULL-PAN strips; audio still the
  clock.

Numbers for implementation (measured): slide-in 0.8–1.2s; tile width 0.30–0.45
frame; creep +8–12%/4–5s; set swap wipe 0.3–0.5s; full-pan rate such that a
long strip crosses most of its height in ~6–11s (≈100–150px/s at 1080p);
clause-to-tile latency ≈ 0–0.5s after the clause starts.

---

# CROP VERIFICATION — what the sample actually crops (verified against the source manhua)

Method: identified the source series ("It Turns Out That They Are the
Protagonists", original 刺猬猫/Ciweimao), found a paginated mirror (toonz.to,
chapter 1 = 98 separate page files at `uploads/chapters/1069605/13065064/NNN.webp`),
downloaded the first pages, and compared them frame-by-frame against the YouTube
tiles. Proof pairs: `tmp/crop_review/yt_vs_source_pairs.jpg` (disposable; pages
of chapter 1 in `tmp/crop_review/src_pages/`).

## Findings

1. **The source's native unit is a near-square PAGE.** Chapter 1's 98 pages are
   individual files at 1080×1080 (16 of 98 slightly shorter — 1080×600–940 —
   at scene transitions). No long strips anywhere in the distribution.

2. **The YouTube "tiles" are whole source pages, verbatim.** Five tiles matched
   pixel-for-pixel: YT@3s = page 005 (woman on bed), YT@7s = page 007 (death
   scene), YT@13s = page 008 (face close-up), YT@19s = page 011 (woman holding
   him), YT@44s = page 020 (explosion burst). Same art, same composition, same
   white margins/caption bars — no creative cropping.

3. **All page text is WASHED WHITE.** Page 011's bubble ("OHH? THIS OTHERWORLD
   REALLY IS CONVENIENT.") is present on the source and shows as an EMPTY white
   bubble on YouTube — same shape, no text. Dialogue bubbles and the bottom
   caption blocks all go blank. (Also kills the site watermark bands wholesale.)
   The pair sometimes sits slightly tighter than the page (margins trimmed).

4. **Full-screen pan sections = runs of consecutive pages** (the chibi
   explainer block at 33–44s is several 1080×1080 pages stacked seamlessly on
   their shared white background, panning through them).

5. Chapter math: 98 pages/chapter; observed YouTube pacing ≈ one page per
   6–15s of narration, so a 6-hour video covers roughly the first 30–40
   chapters — the "whole story" is a page-count game.

## What "crop smartly" means for us

- **The reader dictates crops today** (it judges beat y-ranges; the cropper
  only executes them) — and it crops ART-RUNS: "all of the art it can see" in
  a y-range, hence tall multi-panel rectangles. That is the core mismatch.
- The sample does NO creative cropping: it shows the source's PAGE units and
  blanks the text. Smart cropping = don't invent crops at all.
- Therefore the film lane should consume a PAGINATED source (per-page image
  files, which the reader did not have to cut at all), and the reader's film
  job becomes: per page — classify (tile / explainer-run page / skip), group
  into scenes (set-swap boundaries), flag polluted pages (ads, watermark-only
  bands), pass the page file path as the asset. Text-blanking is a page-image
  operation (bubble/caption detection → fill white), not a crop.
- Our current scrape source (toonverse.net long strips) cannot yield these
  page units; the film lane needs a paginated source or a page-boundary
  detector on the strips (implementation decision, open).
