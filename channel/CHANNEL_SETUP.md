# CHANNEL SETUP GUIDE — manhwa recap channel

Scope: setup ONLY. No uploads. Everything here is done once; the upload workflow
is a separate guide. Save final brand images in `channel/brand/`.

## STATUS (updated after the live setup session)

- Channel exists: **Zeenify** — https://www.youtube.com/@zeenifyrecaps
  (handle cleaned from `zeenify-j7f`; `zeenify` alone was taken)
- DONE: description (general, no series name), channel keywords (general),
  audience = NOT made for kids, upload defaults (Public / Entertainment /
  English / Standard licence), community moderation (Comments On, Basic),
  country of residence = Philippines, contact email (user-entered),
  avatar + banner + watermark uploaded and published.
- Upload method note: the in-app browser can't open file choosers, so the
  three images were injected as File objects into Studio's hidden
  `input[type=file]` elements via page-side evaluate (crop dialogs confirmed
  with Done, then Publish). Banner travels as `banner_final.jpg` (904KB JPEG,
  4:4:4) because the bridge rejects multi-MB args — chunks of ≤400KB base64
  pass fine (assemble via `window.__b64chunk` if ever needed again).
- CHANNEL RULE (user decision): the channel stays series-AGNOSTIC. No series
  names, no series links at channel level — series-specific info (official
  reading link, "currently recapping X") belongs in per-video descriptions.
- STILL PENDING (only this): **phone verification** — Feature eligibility
  shows Intermediate = "Eligible", not "Enabled". Needed for >15-min videos
  and custom thumbnails BEFORE the first upload. youtube.com/verify.
- Minor cleanup candidate (user's call): a stray public playlist named "f"
  (1 video) is visible on the channel — delete or rename before going wide.

## BRAND ASSETS (final, ready to upload — from the ChatGPT session)

All in `channel/brand/`, built by `tmp/make_brand_assets.py` (rerunnable):

- `avatar_final.png` — 800×800, 687KB. Anime bestie with phone, orange bg.
  Upload: Studio → Customisation → Branding → Picture.
- `banner_final.png` — 2560×1440, 2.9MB. Same character on a couch + popcorn;
  "Zeenify — I read manhwa so you don't have to" rendered in the 1546×423
  safe area (Arial Black, cream with charcoal stroke).
  Upload: Branding → Banner image; check the desktop/mobile/TV previews.
- `watermark_final.png` — 150×150, 10KB. Orange roundel, cream "Z".
  Upload: Branding → Video watermark → display time "Entire video".
- Raw generations kept: `avatar_gpt_A.png`, `banner_gpt_raw.png`.

Style note: ChatGPT ignored "flat vector" and produced anime-style art —
kept deliberately, it matches the manhwa niche and both assets share one
style/palette. Prompts used are in this guide (Avatar A) + conversation.

---

## STEP 0 — Dedicated Google account (10 min)

Create a fresh Google account used only for the channel (e.g. the channel name
itself, like `roastedpanels.channel@gmail.com`).

Why separate from your personal account:
- The recap niche gets copyright claims and occasional strikes; you do not want
  that attached to your personal Gmail/Drive.
- The channel's Gmail doubles as the business/contact email for free.
- You can still manage everything from your own devices; just sign in to the
  new account in the browser (or use Chrome profiles to keep them separate).

Then immediately: enable 2-Step Verification on the new account (myaccount.google.com → Security).
This is required anyway to unlock video-length limits (Step 4).

---

## STEP 1 — Create the channel + name & handle

Go to youtube.com → sign in with the new account → click the profile icon →
**"Create a channel"**. It asks for a channel name and generates a handle.

### Name ideas (persona: "Roasting Best Friend")

| # | Name | Vibe |
|---|------|------|
| 1 | **Roasted Panels** | Brandable, niche-adjacent, pun on roasting panels. Recommended. |
| 2 | **The Manhwa Bestie** | Most persona-forward; "best friend watching with you" is literally the narration voice. Recommended. |
| 3 | **Bestie Recaps** | Persona + keyword hybrid; very clear what it does. |
| 4 | **Toon Roast** | Short, broad enough to cover webtoons beyond one series. |
| 5 | **Counting Ls** | Pulled from the narration's running gag ("that's L number four today"); unique, memorable, needs the tagline to explain. |
| 6 | **Panel Panic** | High-energy, brandable. |
| 7 | **Recap & Roast** | Descriptive alliteration. |
| 8 | **The Recap Sofa** | Cozy "watching together" angle. |

Recommendation: **Roasted Panels** (brandable, ages well across series) or
**The Manhwa Bestie** (instantly tells the viewer the tone). Pair either with
the tagline for the banner: **"I read it so you don't have to."**

Notes:
- Don't lock the name to "A Wimp's Strategy Guide" — you will recap other series.
- Check the handle is free when creating (try `@RoastedPanels`, `@RoastedPanelsYT`,
  `@TheManhwaBestie`). Handles can be changed later in Customization → Basic info,
  but grab the cleanest one now.
- Before committing, search the name on YouTube: you want it unclaimed (or the
  existing user tiny), so you own the search results for it.

---

## STEP 2 — Brand assets (avatar, banner, watermark)

### Specs

| Asset | Size to upload | Displays as | File |
|-------|----------------|-------------|------|
| Avatar / profile picture | 800×800 px PNG | 98×98 circle everywhere | ≤4MB |
| Banner / channel art | 2560×1440 px | TV: full, desktop: ~2560×423 strip, mobile: center **1546×423 safe area** | ≤6MB |
| Watermark (subscribe button) | 150×150 px PNG | Tiny bottom-right overlay on your videos | ≤1MB |

The trap: **banner text must sit inside the center 1546×423 safe area** or it
gets cropped on phones and desktop. That is why the GPT prompt generates the art
with an empty middle and you add the text yourself in Canva (AI text is also
frequently mangled — always add text manually).

### GPT image prompts (paste into ChatGPT / gpt-image)

Generate several candidates of each. Ask for 1:1 for avatar/watermark; 3:2
landscape (1536×1024) for the banner, then finish it in Canva (Step 2.3).

**Avatar A — mascot, male bestie:**

> Square 1:1 vector-style avatar for a YouTube channel about manhwa recap videos. A smug, confident cartoon young man with messy black hair and one eyebrow raised, grinning like he is about to spoil the plot, holding a smartphone up in one hand, the screen glowing orange with comic panels. Headphones around his neck. Flat bold illustration style, thick outlines, minimal shading, very high contrast. Palette: warm orange background, deep charcoal character, cream highlights, one small red accent. Simple centered composition, clean solid background, no text, no letters, no words anywhere. Must stay readable when shrunk to a tiny circle profile picture.

**Avatar B — mascot, female bestie:**

> Square 1:1 vector-style avatar for a YouTube channel about manhwa recap videos. A confident cartoon young woman with a high ponytail, smirking while holding a popcorn bucket in one arm and a smartphone in the other hand, the screen glowing orange with comic panels. Flat bold illustration style, thick outlines, minimal shading, very high contrast. Palette: warm orange background, deep charcoal character, cream highlights, one small red accent. Simple centered composition, clean solid background, no text, no letters, no words anywhere. Must stay readable when shrunk to a tiny circle profile picture.

**Avatar C — no character (panel on fire):**

> Square 1:1 flat vector icon for a YouTube channel. A single rounded-corner comic panel frame tilted slightly, drawn as a bold charcoal outline on a warm orange background, with three stylized cartoon flames rising from its top edge and small cream halftone dots around it. Minimal, bold, extremely high contrast, flat design, no text, no letters. Designed to be readable at 98 pixels.

**Watermark:**

> Simple flat vector icon, square format: a small rounded-corner comic panel outline in cream on a warm orange background, with a tiny flame on its top-left corner. Ultra-minimal, bold solid shapes, no text, no letters, readable at 150 pixels. Flat design, high contrast.

**Banner (art only — text added later):**

> Wide landscape YouTube channel banner art. Flat bold vector illustration with thick outlines. Left third: a smug cartoon best friend with messy hair lounging on a couch, phone raised, its screen glowing orange with comic panels. Right third: a striped popcorn bucket, a small phone showing comic panels, and one bold speech-bubble shape with nothing inside it. Middle third: intentionally calm — a subtle warm-orange halftone-dot comic grid with generous empty space where a channel name will be added later. Palette: warm orange, deep charcoal, cream, small red accents. High energy but clean and uncluttered. No text, no letters, no words anywhere.

### 2.3 Post-processing (all free)

1. **Check the circle crop.** Paste the avatar PNG into any editor, mask to a
   circle, shrink to ~100px. If the face/shape dies at that size, regenerate
   with "simpler, bolder shapes."
2. **Resize:** avatar → 800×800; watermark → 150×150. (Paint.net, Photopea, or Canva.)
3. **Banner:** open Canva → template "YouTube Banner" (2560×1440, shows the safe
   area guides) → place the generated art full-bleed → add the channel name
   centered in the safe area in a heavy font (Archivo Black, Luckiest Guy, or
   Bangers — cream or white with a charcoal outline) + the tagline "I read it
   so you don't have to." underneath, smaller. Export PNG ≤6MB.
4. Save finals to `channel/brand/`: `avatar.png`, `banner.png`, `watermark.png`.

### 2.4 Upload them

studio.youtube.com → **Customization → Branding**:
- Picture → upload `avatar.png`
- Banner image → upload `banner.png` (YouTube previews desktop/mobile/TV —
  confirm the channel name is visible in all three)
- Video watermark → upload `watermark.png` → display time: **"Entire video"**

---

## STEP 3 — About page, handle, links, contact

studio.youtube.com → **Customization → Basic info**.

### Channel description (LIVE on the channel now; 1,000-char limit)

Series-agnostic — never name a specific show here.

```
Manhwa & webtoon recaps — I read them so you don't have to, and I roast every terrible decision along the way.

New recap every Tuesday & Friday. Tower climbers, regressors, system holders, overpowered guild leaders — if a character makes a catastrophically bad decision, we will be there, counting the Ls.

Full story recaps told like your best friend is watching over your shoulder. Predictions (usually wrong), genuine hype when the art goes hard, and zero patience for villain monologues.

Recap requests and roasts: the comments.

All recaps are commentary and criticism under fair use.
```

### Other Basic info fields

- **Handle:** `@zeenifyrecaps` (locked in).
- **Links:** keep channel-level links to socials/business only when they exist.
  Per-series official links go in each video's description instead. (Official
  series page for the current show, for video descriptions:
  https://www.webtoons.com/en/action/a-wimps-tower-strategy-guide/list?title_no=9701 — verified.)
- **Contact email:** the channel's Gmail (shown on the About tab).

---

## STEP 4 — Studio settings (the ones that actually matter)

studio.youtube.com → **Settings** (gear, bottom-left).

### 4.1 Channel → Basic info
- **Country of residence:** yours.
- **Keywords:** LIVE on the channel (series-agnostic, 221/500 chars):
  `manhwa recap, webtoon recap, manhwa explained, webtoon explained, manhwa summary, action manhwa, tower climber manhwa, murim manhwa, hunter manhwa, regression manhwa, webtoon story recap, manhwa recap channel`

### 4.2 Channel → Advanced settings
- **Audience → "Do you want to set your channel as Made for Kids?"**
  → **NO, not made for kids** (channel-wide). This is the recap niche's correct
  setting; marking it kids kills comments, end screens, and recommendations.

### 4.3 Feature eligibility (IMPORTANT — do before first upload)
- Verify the phone number under **Intermediate features** ("Enable" → phone verification).
  This unlocks **custom thumbnails** and **videos longer than 15 minutes** — the
  chapter recaps run 15–20 minutes, so this is required, not optional.

### 4.4 Upload defaults
- Privacy: **Public** (you'll use "Schedule" at upload time anyway)
- License: Standard YouTube Licence
- Category: **Entertainment** (Film & Animation is for actual animation, not recaps)
- Language: English
- Leave title/description templates empty — per-video text is an upload-day task.

### 4.5 Community
- Moderation: **"Hold potentially inappropriate comments for review" = on**,
  and hold comments with links (spam protection). Everything else default.
- Add the pinned-comment habit later, on upload day.

### 4.6 Customization → Layout
- Leave everything empty for now. After ~3 uploads: set the newest chapter as
  the **video across all pages of the channel** (or a trailer once you have one),
  and add sections: "Latest recaps" + a series section per show.

---

## STEP 5 — Pre-upload checklist (nothing uploaded yet)

- [ ] Fresh Google account + 2FA on
- [ ] Channel created, clean handle claimed, name not clashing with an existing channel
- [ ] Avatar, banner (text inside 1546×423 safe area), watermark uploaded
- [ ] Description, links, contact email filled
- [ ] Channel keywords pasted; country set
- [ ] Audience = NOT made for kids
- [ ] Phone verified → custom thumbnails + >15-min videos unlocked
- [ ] Upload defaults set (Public, Entertainment, English)
- [ ] Comment moderation on "hold for review"
- [ ] 20 rendered MP4s parked in `videos/chNNN/` (already done — 6+ weeks of
      runway at a 3/week cadence)

## NEXT PHASE (after setup — separate session)

1. Upload workflow: titles, descriptions, tags, end screens, playlists
   ("A Wimp's Strategy Guide — Full Recap" playlist, created with the first upload).
2. Thumbnail pipeline (1280×720, series-consistent template).
3. Upload cadence: 20 chapters banked → publish on a fixed schedule (e.g.
   Tue/Fri 6pm EST) rather than dumping them; scheduling happens per-video at upload.
4. Monetization note: YPP needs 1,000 subs + 4,000 watch-hours. Recap channels
   get audited for "reused content" — the full diegetic narration + roasting
   commentary IS the transformation case; keep scripts original (they are) and
   keep the fair-use line in the description.
