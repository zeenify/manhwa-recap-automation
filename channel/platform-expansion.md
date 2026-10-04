# PLATFORM EXPANSION PACK — Zeenify beyond YouTube

Goal: chapter-by-chapter distribution on discovery platforms, each one
pointing back to the YouTube channel (the 5h43m compilation stays
YouTube-exclusive). Rule of the house: **when a login wall appears, STOP and
let the user log in** — never touch account credentials.

## Handles & branding (consistent everywhere)

- Handle: **@zeenifyrecaps** on every platform (grab it even where we post later)
- Profile image: `channel/brand/avatar_final.png` (works square on every platform)
- Facebook page cover: crop of `channel/brand/banner_final.png` → 851×315
  (`channel/brand/fb_cover.png`, build with PIL when the page is created)
- No new AI art needed per platform — one consistent brand reads stronger.

## STATUS (Oct 3)
- **TikTok: DONE.** 20/20 chapters posted, bio has youtube.com/@zeenifyrecaps.
  ch003+ch004 lack captions (mobile app → Edit caption to patch).
- **Facebook: DONE.** Page "Zeenify" created (id 61594960413829): avatar, cover,
  Arts & entertainment category, bio with clickable youtube.com/@zeenifyrecaps,
  website = channel URL. Remaining nicety: set username in Page settings →
  Page setup (@zeenifyrecaps); optional email in About.
- **Rumble / Odysee: NEXT** — signups need the user's email + password choice.

## Platform plan

### Tier 1 — discovery engines (do first)
1. **TikTok** — biggest manhwa/recap audience. Personal (NOT Business) account:
   personal keeps the full sound library and gets the bio website link at
   1,000 followers. **10-min upload cap** → each ~15-17 min chapter becomes
   **Part 1 / Part 2** (vertical 9:16 blurred-bg versions; converter tested —
   see "Vertical pipeline"). Caption: short hook + 4-6 hashtags. Link in bio:
   before 1k followers put "Full recap on YouTube: Zeenify" as text + pinned
   comment with the link.
2. **Facebook Page** (needs a personal FB profile to create the Page — user
   creates/logs in) — recap content performs well with the older FB demo, and
   Facebook pays via in-stream ads once eligible (60s+ videos, 10k followers,
   600k minutes viewed/60d). Upload chapters horizontally (no cap issue).
   Links in post captions get reach-penalised → link lives in the Page intro
   + first comment.
3. **YouTube Shorts** — same channel, zero extra accounts: cut the best 2-3
   moments of each chapter into Shorts. Feeds the main channel's subscriber
   count directly. Highest ROI of the whole expansion.

### Tier 2 — unorthodox platforms that PAY PER VIEW (user's ask)
4. **Rumble** — pays basic ad revenue **from the very first video** (no
   follower gate), RPM ≈ $2–10/1k views, $50 payout minimum; Creator
   Incentive Program kicks in at 1,000 followers. Upload full horizontal
   chapters. https://rumble.support/help/rumble-creator-program
5. **Odysee** — decentralized; pays **LBC credits for validated views** from
   day one plus viewer tips; withdrawable via crypto. Upload full chapters;
   same titles/tags as Rumble.

### Tier 3 — later / conditional
6. **Snapchat Spotlight** — vertical-only, ~$0.10–0.30/1k views and the
   rev-share pools are now invite-only. Only worth it once verticals exist
   anyway; treat as free syndication of TikTok clips.
7. **X (Twitter)** — ads revenue sharing needs X Premium + 5M impressions/3mo.
   Skip until we have clip volume.
8. **Dailymotion** — revenue share by application. Low priority.

Monetization gates (so we don't chase ghosts):
- TikTok Creator Rewards: 10k followers + 100k views/30d, videos >1 min
- Facebook in-stream: 10k followers + 600k minutes viewed/60d
- YouTube Partner: 1k subs + 4k watch-hours (compilation alone is 5h43m of watch-time bait)

Copyright note (one line, no lectures): smaller platforms run weaker Content
ID, which is exactly why recap channels syndicate there — but WEBTOON/Naver
takedowns are possible anywhere, so diversification is also risk-spreading.

## Account bios (copy-paste, per platform — ALWAYS use the real YouTube link)

Channel URL: **https://www.youtube.com/@zeenifyrecaps**

**TikTok** (LIVE, 75/80 chars):
`Manhwa recaps daily 📚 Full chapters on YouTube: youtube.com/@zeenifyrecaps`

**Instagram** (≤150 chars):
`Manhwa & webtoon recaps — I read them so you don't have to 📚 Full chapters on YouTube → youtube.com/@zeenifyrecaps`

**Facebook Page intro** (≤101 chars shown, about section longer):
`Manhwa & webtoon recaps — I read them so you don't have to. Full chapters on YouTube: youtube.com/@zeenifyrecaps`
About (long):
```
Manhwa & webtoon recaps — I read them so you don't have to, and I roast every terrible decision along the way.

Full chapters on YouTube: https://www.youtube.com/@zeenifyrecaps
New recaps every Tuesday & Friday.

All recaps are commentary and criticism under fair use. I do not own the manhwa/artwork — all rights belong to their respective owners.
```

**Rumble / Odysee channel description:**
```
Manhwa & webtoon recaps — I read them so you don't have to, and I roast every terrible decision along the way. Full chapter recaps of tower climbers, regressors and system holders, told like your best friend is watching over your shoulder.

Watch everything first on YouTube: https://www.youtube.com/@zeenifyrecaps — new recaps every Tuesday & Friday.

All recaps are commentary and criticism under fair use. I do not own the manhwa/artwork — all rights belong to their respective owners.
```

## Per-chapter caption template

- **TikTok / Reels caption** (Part 1):
  `He summoned an SSR assassin into his living room... and he's terrified of her 💀 Chapter [N] Part 1 — full recap on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide`
- **TikTok / Reels caption** (Part 2):
  `Chapter [N] Part 2 — it gets worse for him 💀 Full recap + all chapters on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #towermanhwa`
- **Facebook post**: 1-2 sentence hook + `Full chapter on YouTube →` (link in
  first comment) + same hashtags.
- **Rumble/Odysee title**: `A Wimp's Tower Strategy Guide Chapter [N] - Manhwa Recap` +
  the YouTube description's summary block + tags.

Hashtag core set (rotate 4-6 per post, don't spam all):
`#manhwa #manhwarecap #webtoon #manga #anime #awimpstowerstrategyguide #towermanhwa #manhwaedit #manhwarecommendation #recap`

## Vertical pipeline — TESTED, verdict: do NOT naive-convert

- The naive 16:9→9:16 blur-bg conversion (`blur bg + fg scaled to width`)
  was tested on ch001: our chapters are composed cards (blurred bg + tall
  webtoon panel column), so the converted vertical shows a **tiny column of
  art inside a tiny column** — illegible. Do not batch-convert this way.
- **Decision:** post chapters **horizontal** on TikTok (2 parts), Facebook,
  Rumble, Odysee — recap channels do this and it works (tap = full-screen
  landscape).
- **True vertical content** (Shorts / Reels / Spotlight) needs a purpose
  render: an `assemble.py` vertical mode (9:16 card, blurred fill, tall
  panel at ~85-100% width with pan-down — webtoon strips are naturally
  vertical so this can look great). Main-session tooling job, queued for
  after the first platform accounts exist. Shorts ≤3 min: cut 2-3 best
  beats per chapter.

## Account creation order (user logs in, always)

1. TikTok (personal/creator) → 2. Facebook Page → 3. Instagram → 4. Rumble →
5. Odysee. When any login/signup wall appears during browser work: STOP, ask
the user, let them type credentials.

## Facebook posting recipe (tested 2026-10-05, ch001 of Return of the Top Class Master)

FB merged page videos into the REEL pipeline — even 11-min horizontal uploads
go through the reel composer and publish as reels (the wimp chapters are all
reels in MBS). The "Edit reel" step is NORMAL, not a wrong turn.

1. Page (facebook.com/profile.php?id=61594960413829) → scroll to the timeline
   composer ("What's on your mind?" field — scrollIntoView + CUA click; the
   floating "Share a thought..." bubble opens NOTES, not a post — avoid).
2. In the dialog click the inner "Photo/video" → a file input mounts inside
   [role=dialog] (accept video/*) → inject the mp4 as a File (chunked base64
   ≤380KB/evaluate, ~371 chunks for 105MB, assemble via atob→Blob parts) →
   dispatch change. Upload reaches 100% in ~1-2 min (browser does the transfer).
3. Type the caption (from fb-captions.json — same format as the wimp bulk) via
   locator.type() into the dialog textbox → click "Next".
4. "Edit reel" screen: fill Reel title ("Series — Chapter N | Manhwa Recap"),
   3 reel tags via the Add tags box (fill + Enter), → "Next".
5. "Reel settings": caption carried over, audience Public, "Publish now" →
   click "Post" → dialog closes with a posting confirmation.
6. The reel then encodes server-side for 10-30 min before it appears on the
   timeline / MBS published grid / the page Reels tab. VERIFY AFTER A DELAY,
   not immediately — the published grid will show "Chapter N — ..." with the
   video duration next to the title.

Gotchas: MBS direct goto ERR_ABORTs — use a NEW IAB tab for
business.facebook.com. MBS's own composer never mounts its file input via
injection — the PAGE composer works. The profile feed scrolls inside an inner
container — use scrollIntoView, not window.scrollBy. Caption typing needs
locator.click() + locator.type() (real key events); fill() fails on FB fields.
