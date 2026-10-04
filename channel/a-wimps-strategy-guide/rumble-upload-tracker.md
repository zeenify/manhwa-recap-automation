# RUMBLE UPLOAD TRACKER — Zeenify channel (rumble.com/c/c-7963658)

## Status
- ch001 ✓ LIVE — https://rumble.com/v7gbhto-a-wimps-tower-strategy-guide-chapter-1-manhwa-recap.html
- **RUMBLE COMPLETE ✓ 20/20 LIVE — verified on rumble.com/c/c-7963658/videos (ch001-ch020)**
- ch002-ch005 single-tab Studio loop; ch006-ch020 via 4 parallel Studio tabs (~470KB/s each, no bandwidth penalty).
- Chapters published out of order (parallel) — fine for a back-catalog dump; channel page sorts by date.
- Select-file lessons: click "Select File" via CUA elements() (not blind coords); click the
  File-name field, setValue, VERIFY value, then Return. If a stale "Open" dialog lingers,
  click its Cancel first. After Finish, dismiss toast, goto /home/upload to reopen modal.
- T&C checkbox clicks sometimes don't register in one pass — re-snapshot and verify
  both checkboxes [checked] before clicking Finish (it stays disabled otherwise).

## ODYSEE — Zeenify channel (odysee.com/@edrickmartin101) — upload recipe
- Channel created via onboarding: Display Name "Zeenify" (username locked: edrickmartin101),
  avatar = channel/brand/avatar_final.png, cover = channel/brand/odysee_cover.png (2048x320 crop of banner),
  description + website(youtube.com/@zeenifyrecaps) + 5 tags (manhwa, webtoon, manhwa recap, anime, manga) saved via Edit panel.
- DECISION: upload the 20 chapters SEPARATELY (not the 6h compilation) — per-view rewards, searchability,
  consistent with TikTok/FB/Rumble; compilation stays a YouTube hook.
- Upload wizard (odysee.com/$/upload), 4 steps File→Details→Visibility→Publish:
  1. CUA click "Select File" (raster ~950,400) → Open dialog → quoted path → Return → click Next (~1208,416)
  2. Playwright: fill Title (getByRole name "Descriptive titles work best") + Description (name /What is your content about/)
     — reuse channel/rumble_metadata.json (same titles/descriptions as Rumble)
  3. CUA: scroll down 10 → tag input (~1088,321): per tag [click input, Ctrl+A, type, wait 0.9s, click suggestion chip (~975,339)]
     ×5 — real typing required (DOM Enter events do NOT commit tags here)
  4. CUA: Next (~1207,558) → Visibility defaults are Public+Free → Next (~1207,538) → Publish (~1202,524)
  5. Publish starts the actual file upload (metadata first!) — the upload engine runs app-wide in background,
     so the next video's metadata can be prepped immediately in the same tab.
- Status: **ODYSEE COMPLETE ✓ 20/20 published** (ch001-ch020, all with title/description/5 tags/Public/Free,
  channel = @edrickmartin101 display "Zeenify"). Public grid may lag — LBRY claim confirmations take
  minutes-to-hours after a 20-publish burst; verify later on odysee.com/@edrickmartin101 (uploads manager
  /$/uploads shows the authoritative list).
- When a tab hits 100%: Next → 2 T&C checkboxes → Finish → verify "Upload finished successfully" → Dismiss →
  goto studio.rumble.com/home/upload → CUA select next file from queue → fill form → continue.
- NOTE: session quota (GLM) at 16% — if the run dies mid-loop, resume from this file: check which
  chapters exist on rumble.com/c/c-7963658, restart the 4-tab loop with the remaining queue.

## Channel branding (DONE)
- Created channel via rumble.com/account/channel/create: Name "zeenify", Title "Zeenify",
  description = platform-expansion.md Rumble copy (YouTube link + fair use), Facebook URL set,
  thumbnail = channel/brand/avatar_final.png, backsplash = channel/brand/rumble_backsplash.png (918x200 crop of banner).
- Channel id 7963658; account @zeenify. Custom URL "not eligible" yet (needs followers).

## Per-video metadata
- channel/rumble_metadata.json — keys chNNN.mp4 → {file, title, description, tags}.
- Title: "A Wimp's Tower Strategy Guide Chapter N - Manhwa Recap"
- Primary category: Entertainment. Secondary: none. Visibility: Public. License: Rumble Only (non-exclusive).
- Author/channel radio: "zeenify /c/zeenify" (NOT User Account).

## Studio upload cycle (studio.rumble.com/home/upload — works in its own IAB tab)
1. Click "Create" → "Upload" button → modal "Upload Video".
2. CUA real-click "+ Select File" → native Open dialog → setValue quoted path
   "C:\Users\EDRICK\Desktop\make mon\videos\chNNN\chNNN.mp4" → Return.
3. While uploading (starts immediately): Playwright-fill Title (required), Description (required),
   "Add tags"; click radio "zeenify /c/zeenify"; click button "Primary category Down arrow"
   then getByText("Entertainment", {exact:true}).first().click()  (dropdown is toggle — click once).
4. Wait until upload 100% AND "Go to next step" enabled (poll domSnapshot for `paragraph: N%`),
   click Next → step 2 has Monetization "Rumble Only" + Visibility "Public" defaults (leave),
   click both T&C checkboxes → click "Finish".
5. "SUCCESS Upload finished successfully" → Dismiss → modal closes. Record link from
   channel page at the end (rumble.com/c/c-7963658 lists all).

## Classic upload.php flow (fallback, used for ch001)
Select file → uploads → Video info form (title/description/tags) → channelId radio 7963658 via
evaluate (custom radios; set checked + dispatch change) → CUA: category dropdown (968,240-ish) →
Entertainment → wait 100% → licensing "Rumble Only" → 2 T&C checkboxes → Submit.

## Gotchas
- studio.rumble.com ERR_ABORTs on goto() from the rumble.com tab — open it as a SEPARATE IAB tab.
- Studio "Next" stays disabled until the upload completes (not just form filled).
- File picker clicks need Computer Use (real activation); dialog is its own pid, "File name:" field
  takes multiple quoted paths but only the FIRST file is used by both uploaders — one file per cycle.
- Upload speed oscillates 60-470KB/s; be patient, do NOT re-select the file (double upload).
