# TIKTOK UPLOAD TRACKER — Zeenify (@zeenifyrecaps)

## FACEBOOK PAGE PROGRESS (Zeenify Page, id 61594960413829) — COMPLETE ✓ 20/20
- ch001 + ch002: posted individually (Oct 3)
- ch003-ch020 (18 videos): posted via Meta Business Suite → Create post "More" → "Bulk upload reels" → one Add-videos dialog with all 18 quoted paths multi-selected → filled 18 description textboxes via Playwright fill() (rows are in filename order) → global Publish. 17 published first shot; ch005 errored once ("Unable to process all your reels"), retried via row Publish now → Update → global Publish, went through ("Your bulk upload is processing!").
- Captions: channel/fb-bulk/captions.json (exact texts used; hook + 💀 + "Full recap series on YouTube: youtube.com/@zeenifyrecaps" + 4 hashtags)
- Traps: a leftover "Leave Page?" draft dialog blocks ALL navigation (goto() returns ERR_ABORTED) — dismiss it first. business.facebook.com direct goto() works once no draft dialog is open.

## TikTok final status: ALL 20 CHAPTERS POSTED ✓

- ch001 ✓ video/7692102991926824200 — WITH caption
- ch002 ✓ video/7692105883546930439 — WITH caption
- ch003 ✓ — NO CAPTION (patch via post-edit)
- ch004 ✓ — NO CAPTION (patch via post-edit)
- ch005 ✓ video/7692127811946958087 — WITH caption
- ch006 ✓ video/7692129412325723410 — WITH caption
- ch007-ch020 ✓ — all WITH captions (posted via the CUA loop, Oct 3)
- ch020 + a few others show "Content under review / Only me" — flips public after review.

## Proven upload flow (IAB + Computer Use)
1. CDP: goto tiktok.com/tiktokstudio/upload?from=webapp&tab=video, wait ~4.5s, verify "Select video to upload"
2. CUA (one-shot cell): getApp({pid:2988, window_id:1901544}) → getScreenshot({emit:false}) → click([995,320] for drop-zone layout or [1000,446] for red-button layout) → listApps → find "Open" pid → elements() → find textfield title "File name:" → setValue(full path) → verify value → pressKey Return → confirm dialog gone
3. CDP: dismiss joyride overlays (up to 3×) → caption: ed.click → press Control+a → 8× Backspace → ed.type(CAPTION, {delayMs:5}) → verify length
4. CDP: poll /Uploaded \(/ up to ~40s (Post button enables early; clicking before badge worked for ch002/004/005)
5. CDP: click Post → if "Post now" button appears (continue-to-post dialog) click it → verify /@zeenifyrecaps/video/ ID
Gotchas: frame binding expires between cells (always re-screenshot in the same cell as the click); CDP JS clicks lack user activation (file picker blocked); dialog "Open" is a separate pid each time; delta element snapshots give stale indices — always verify value after setValue.

## Remaining captions (ch006-020)
- ch006: Chapter 6 — the tower sends something worse. He sends Gobang 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch007: Chapter 7 — the strategy is "let the OP spirits handle it" and honestly? It works 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch008: Chapter 8 — new floor, same coward, bigger summons 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch009: Chapter 9 — the household gains another legend and he loses another nerve 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch010: Chapter 10 — double digits and the tower still can't kill this man 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch011: Chapter 11 — the wimp is becoming the strongest player in the room 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch012: Chapter 12 — the mysteries pile up faster than the floors 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch013: Chapter 13 — the lore drops and it changes EVERYTHING 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch014: Chapter 14 — the bureau is onto him and the clock is ticking 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch015: Chapter 15 — elite contracts, bigger floors, same terrified genius 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch016: Chapter 16 — the S++ clear nobody saw coming 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch017: Chapter 17 — the family finds out and it goes about as well as you'd think 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch018: Chapter 18 — a traitor on live TV and a 92-day countdown 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch019: Chapter 19 — the holy sword rental business is OPEN 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide
- ch020: Chapter 20 — the fourth summon arrives and she's a SHAMAN PRINCESS 💀 Full recap series on YouTube (Zeenify) #manhwa #manhwarecap #webtoon #awimpstowerstrategyguide

## Post-queue fixes (later)
- ch003 + ch004: add captions via TikTok Studio post-edit (Posts → row → edit)
- channel/brand/fb_cover.png: crop banner for Facebook page cover
