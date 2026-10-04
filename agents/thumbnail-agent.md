# THUMBNAIL AGENT — per-video thumbnail pipeline (Zeenify)

Produce ONE 1280×720 thumbnail per uploaded video. This file is the complete
context a fresh session needs — read nothing else except the files it points to.

Core idea (user's rule): **competitor thumbnails are inspiration ONLY; the
thumbnail must depict OUR manhwa's own characters and scene.** ChatGPT
(user's account) generates the art from our beat panels + sample compositions;
the yellow phrase text is always added by us locally, never by the AI.

## Inputs

- **Sample bank** — `channel/thumbnail-research/*.jpg`: 8 proven recap-channel
  thumbnails (video ids in filenames, scraped 2026-10-02). Reuse these; only
  re-scrape if the user asks to refresh the bank.
- **Extracted formula** (from those 8 + 3 description scrapes): central
  expressive character (glowing eyes / reaching hand / smug grin), ONE short
  yellow phrase with thick black outline (2–5 words MAX), optional
  arrows/labels/game-UI accents, super-saturated blue/orange/purple palette
  with red accents. Channel palette accent: orange/gold.
- **Art source** — `assets/<slug>/<chapter>/beats/beat_NNNN.png`. Pick 1–3
  dramatic beats (closeups: red/glowing eyes, grin, stab/betrayal, power
  reveal, villain-with-macguffin). The `event` field in
  `assets/<slug>/<chapter>/beats/beats.json` tells you what every beat shows
  WITHOUT opening any images — pick from it, then look at candidates via a
  small contact sheet (see QA rule below).

## Non-negotiable user rules

1. Samples = composition inspiration only. Never reproduce competitor art,
   characters, or text in the output.
2. NEVER advertise chapter counts or video length anywhere on the thumbnail
   (the competitor "CH. 1-40" badge style was deliberately dropped).
3. AI never bakes the text. AI-generated letters are routinely mangled; the
   yellow phrase is added in the local post-process. If ChatGPT bakes text
   anyway, regenerate with an explicit no-text instruction.
4. Vision safety: the main session never reads full-size images in bulk —
   build ONE small contact sheet (~≤500KB) of candidate beats and read that.

## Generation (user's ChatGPT, via browser)

1. Open chatgpt.com. If a login wall appears: STOP, let the user log in —
   never touch account credentials.
2. Fresh conversation per video is fine (the prompt below is self-contained);
   continuing the original brand conversation also works.
3. Attach: 5–8 competitor sample JPGs + our 1–3 chosen beat PNGs.
4. Prompt template (fill the brackets):

   > We run a manhwa recap YouTube channel. Attached are two kinds of images.
   > (1) Thumbnails from OTHER recap channels — composition and styling
   > INSPIRATION ONLY; do not copy their art, characters, or any text.
   > (2) [N] panels from OUR series, "[SERIES NAME]" — these are the subject:
   > keep these characters' faces, hair, outfits and the scene recognizable.
   > Task: one landscape 16:9 YouTube thumbnail of this exact scene from our
   > series, composed like the strongest inspiration samples: main character
   > large and central with an expressive face ([e.g. blood-red eyes, gritted
   > teeth]), [second character/element] behind him, dramatic saturated
   > colors ([scene palette]), high contrast, clean readable silhouette even
   > at small size. Absolutely NO text, letters, numbers, logos, or
   > watermarks anywhere in the image.

5. Download the result: the rendered image's `img src` is a pre-signed
   oaiusercontent URL — copy it from the DOM and `curl -o` it (no cookies
   needed). Save to `tmp/thumb_raw_<slug>_chNNN.png`. Keep every raw.

## Post-process (local, deterministic)

Pattern script: `tmp/make_thumb_ch001.py` (rerunnable per video).

1. Crop the raw to 16:9 centered on the faces (generations come 3:2
   1536×1024 → crop), resize to 1280×720 LANCZOS.
2. Saturation ×1.25–1.3, contrast ×1.08–1.12, sharpen ~1.4.
3. Bottom gradient scrim: black, alpha 0→~190 over the lower third, so text
   pops on any background.
4. Yellow phrase: Arial Black (`C:/Windows/Fonts/ariblk.ttf`), fill
   `#FFE03A`, stroke_width ~9–10 in near-black `#0C0A0A`, centered, 1–2
   lines, 2–5 words total.
5. QA: save a ≤500KB small preview, Read it, and check — faces readable at
   ~320px wide, phrase ≤5 words with no clipped letters, no AI-mangled text,
   no competitor art leaked through, nothing important hidden under text or
   scrim. Iterate the crop (1–2 rounds is normal) before accepting.
6. Save final: `channel/<slug>/thumbnail_chNNN.png` (raws stay in `tmp/` or
   `channel/<slug>/raws/`). Reference it from that chapter's upload-prep doc.

## Log

- **ch001 — Return of the Top Class Master** (2026-10-05): samples reused from
  bank; beats chosen: beat_0010 (betrayal stab, red eyes) primary,
  beat_0068 (predatory grin) backup. Phrase: "BETRAYED BY HIS BEST FRIEND".
  Status: [update when the ChatGPT generation lands].
