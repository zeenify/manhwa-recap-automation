# LEO'S MANHWA FORMAT NOTES — the "Arc Film" format study

Source: Leo's Manhwa (https://www.youtube.com/@LeoManhwa-g1s, 4.29k subs, 66 videos),
studied 2026-10-15. Videos examined: the user-provided link (o-BvvXay_to) in full
sample windows (intro / 1h30 / 3h / ending) + #2 top video (S-78H1Vusfw) for
consistency. Evidence: yt-dlp metadata, auto-caption transcripts (~76k words),
720p sample windows downloaded to `tmp/leo_research/`, frame-by-frame inspection.

## Channel snapshot

| # | Video | Length | Views |
|---|-------|--------|-------|
| 1 | A Legendary Cultivator Reincarnates as a Weakling Hunted by S-Rank Girls! | 6:01:52 | 122k (2 wk) |
| 2 | He's The Only Summoner Who Can Fuse And Infinitely Evolve His Pets! | 10:26 | 116k |
| 3 | He's the ONLY One Who Can Absorb the Souls of Defeated Monsters! | 12:00 | 79k |
| 4 | A Necromancer Maxes Out Skeleton Summoning and Shocks Every Mage! | 14:00 | 64k |
| 5 | In the Zombie Apocalypse, He Built the Most Secure Base! | 13:00 | 58k |
| 6 | His Skeleton Summoning System Lets Him Level Up 100× Faster | 4:21 | 44k |
| 7 | He Steals the Souls and Abilities of Defeated Monsters | 1:20 | 43k |

Patterns that matter:

1. **One video = one entire story.** 4–15 hours per video; the video ends when
   the source story runs out (the 6h video literally ends on story art — no
   outro card, no "subscribe" screen, nothing). Views correlate with length:
   their 12–15h uploads are 58–79k, their 1–3h ones 12–43k. Watch time is the
   asset; the video is a binge product, not an episode.
2. **Cadence is factory-grade**: multiple multi-hour uploads per week from a
   4.29k-sub channel. No human team narrates 76k words per video at this
   rate — these are automated or semi-automated productions. Their subscriber
   count is tiny; the views come from browse/suggested binge-seeding.
3. Titles: premise-compression hooks with ALL-CAPS emphasis words, always
   "! | Manhwa Recap" tailed. Description: emoji-bullet synopsis of the
   premise + tag block stuffed with OTHER channels' names ("the manhwa man",
   "anicap", etc.) and every recapping keyword under the sun.
4. No chapter timestamps on even the 6h video (0 chapters in metadata).

## Visual mechanics (verified frame-by-frame)

- **One continuous slow pan per section — essentially zero cuts.** Scene-change
  detection across 2.5-min windows: 0–5 hard cuts per window (mid-story window:
  ONE cut in 150 s). The screen never switches to a "new slide" per sentence or
  per beat. This is the single biggest difference from our card-per-entry
  renderer.
- **What pans**: full page-screenshots of the source (Chinese manhua = grid
  pages; Korean manhwa = long strips), tiled/butted together, scrolled at a
  slow constant-ish rate (~1.5–2% of frame width per second measured between
  matching art across 20 s). Occasionally zooms in on a panel; occasionally a
  cut to the next section (only every ~30–150 s).
- **Composition**: sharp art column/tiles centered; background = blurred,
  darkened copy of the SAME art (self-fill). Sometimes art fills the frame,
  sometimes it sits as a small 2-tile block with huge blurred margins —
  composition follows source layout, not a fixed template.
- **All dialogue bubbles are BLANKED** (washed to white): no readable text
  anywhere in the art. Stylized onomatopoeia is LEFT IN. Source watermark
  (快看) also left in. No burned-in captions or subtitles anywhere.
- Video starts on art with narration from second 0 (no logo, no channel intro).
- 16:9, 1080p-class, standard h264/aac.

## Narration mechanics (from 76,146-word transcript)

- **210 words per minute, sustained for 6 hours.** (Our ch037 measures 211 WPM
  spoken — the delivery speed is already identical; our number includes pads.)
- **Third-person plot recitation, zero personality.** Every line attributed to
  a NAMED character and chained with "says that / states that / asks why /
  after this / meanwhile": "Joy asks why she needs the heavenly dao if it
  can't bring Marvin back to life. Marvin suddenly stops her and tells her
  that he is fine, so she should not rush." No jokes, no roasting, no narrator
  character, no direct audience address, no hooks beyond the opening.
- Opening is a 2-sentence premise thesis ("Unlike any other heroic story, this
  one begins in the most ugly way possible. The thing is, our main character,
  Marvin, who is 30 years old, dies of a heart attack. … what happens to him
  next is mind-boggling.") then straight plot.
- Pure information density: dialogue is reported compactly, not quoted or
  performed. Boring mechanics get one clause; fights get blow-by-blow.
- Voice character: not verified from captions (would need a listen). Nothing
  in the format requires a distinct voice.

## Translation to OUR pipeline — what actually carries the success

1. **Length and completeness** (the binge product): whole-story-per-video, not
   per-chapter. This is what the algorithm is rewarding here.
2. **Continuous-scroll visuals**: no per-sentence slide cuts; the eye follows
   the strip while the voice tells the story. Cheaper to watch AND cheaper to
   produce than composed cards.
3. **210 WPM + named attribution**: maximum plot per second. Personality is
   OPTIONAL in this format — Leo proves the format works without any.
4. Titles/descriptions as done above (premise hook, tag stuffing).

What we should NOT copy blindly:

- Blank-bubble art: costs a new image-processing stage (bubble detection +
  inpaint). Ours keeping bubble text is differentiation, and our narration is
  the "voice" of the bubbles anyway. Revisit as a v2 cosmetic / DMCA-surface
  reduction (blanked bubbles = no scanlation text shipped in frames).
- Zero personality: Leo has 4.29k subs for 500k+ monthly views — retention of
  the FORMAT, not the channel. A voice viewers recognize is our long-term moat.
- 14h lengths at launch: we have 20–40 chapters scanned per series; a
  realistic film is 1.5–3.5h. Grow length as chapters accumulate.

## Fit against our existing assets

- Reader stage: **unchanged** — beats.json + boundary-verified crops are
  exactly the scroll surface a film assembler needs.
- TTS: unchanged; voice already at the niche's WPM.
- Writer: needs a THIRD variant (arc-film writer; see proposal) — same script
  contract, arc-level composition, tighter word budgets (~half our current
  words per beat) so a scanned arc becomes one film.
- Assembler: build `tools/assemble_film.py` — per chapter, stack beat crops
  into a column and continuous-pan it over blurred self-fill at a rate set by
  the chapter's narration audio (reuse the speed-capped smoothstep pan-down
  from assemble_shorts.py; no per-entry cuts; only per-chapter gentle cuts).
- Comp stitcher (compile_video.py): still fine for the CARD-format compilations
  (keep both lanes; FDB writer stays as-is per user decision).
