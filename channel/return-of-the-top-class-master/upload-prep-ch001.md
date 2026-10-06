# UPLOAD PREP — ch001 — Return of the Top Class Master (first YouTube chapter upload)

Status: **LIVE** — published Public on 2026-10-05.
Video: https://youtu.be/VXOM-9kPmPc — title as recommended (option 1), 1080p HD
verified available, 11:38, playlist "Return of the Top Class Master" created and
attached, tags 15/15, thumbnail custom (ChatGPT art + PIL text pass), audience
not-made-for-kids, English, Standard licence.

## Follow-ups (user, ~2 min)
1. **Pin the comment** — the rating-question comment IS posted (from
   @zeenifyrecaps); YouTube blocks PINNING behind a one-time anti-spam
   verification in Studio (user must complete it; agent rule: user handles
   verifications). Comment → ⋮ → Pin.
2. **Possible duplicate playlist** — the Studio picker showed two
   "Return of the Top Class Master" entries (first Create attempt may have
   made an empty one before the successful attach). Check
   studio.youtube.com → Content → Playlists and delete an empty duplicate.
3. **Copyright check was still running at publish time** ("taking longer than
   usual") — check Content tab next day for any claim.

## YouTube upload recipe (what worked — for ch002+)
- Drive the built-in browser via the control-browser skill; login walls = stop,
  user logs in. Studio was already logged in; ChatGPT too.
- Upload dialog: Create/Upload videos → inject File objects into the dialog's
  `input[type=file]` via page-side evaluate — **chunked base64 works at
  ~380KB/evaluate, ~47ms per chunk** → a 105MB mp4 injects in ~20s of evaluate
  calls; the browser then does the real upload natively and fast (105MB was
  "Upload complete" within ~2 min). Assemble in-page: chunks → atob in 8MB
  segments → Blob parts → File → DataTransfer → input.files → dispatch change.
- Metadata: title/description via getByRole fill; tags via the visible
  `#text-input` (fill + Enter per tag; there are TWO #text-input nodes —
  filter visible); thumbnail via `#file-loader` (accept jpeg/png).
- The new-playlist modal inside the upload dialog is FLAKY (may not mount);
  create it later on the video edit page — picker → New playlist menu →
  "Add title" textbox mounts there.
- The upload wizard can be advanced while the copyright check runs ("checks
  aren't final"); Published dialog confirmed.
- Pinned comments need a one-time Studio verification → user step.
- www.youtube.com feed pages render EMPTY in the built-in browser; watch pages
  and studio.youtube.com work.

## Files

- **Video:** `videos/return-of-the-top-class-master/ch001/ch001.mp4` — 11m37s
  (697.4s), 1920×1080, h264+aac. Series voice (speed preset 1.07), verified against
  `audio/return-of-the-top-class-master/ch001/timing.json` (total 697.4s).
  **Do not use** the legacy `…-mommy/` render lane — it holds a stale
  pre-preset render (745.2s, raw voice, no speed preset).
- **Thumbnail:** `channel/return-of-the-top-class-master/thumbnail_ch001.png`
  (1280×720). Fallback (PIL from beat_0010 + text pass) already saved; ChatGPT
  art version generated via the thumbnail-agent pipeline replaces it if QA passes.

## Title (pick one — power-word pattern; NEVER chapter counts, NEVER runtime)

1. **Strongest Master BETRAYED Mid-Trial, Wakes Up in His Own High School Body - Manhwa Recap** ← recommended
2. He Was One Step From Godhood. His Best Friend Stabbed Him. - Manhwa Recap
3. Betrayed by His Best Friend, a God Returns to His Own Past - Manhwa Recap

Pattern source: top competitor in the niche uses ALL-CAPS power words. User
rule from the wimp upload: no chapter ranges, no video length in titles.
Chapter numbering lives in the description + playlist only.

## Description (template from the wimp upload prep; this series has NO official
store page — Naver/Kakao/Webnovel all negative on 2026-10-05 search — so the
series block names the title without a reading link)

```
Manhwa Summary:

Ray was the strongest master on the planet Haons — one trial away from godhood, standing calm under several hundred billion volts. Then his most trusted friend put a knife in his back, ripped the core soul from his chest, and crowned himself master of Haons in Ray's place.

Death wasn't the end. Ray wakes up on Earth — inside his own past — in the body of Kang Tae Wook, the punching bag of a brutal high school. His aura is unreachable. His core soul is sealed. His first problem is a bully with a fist and an audience. Big mistake.

This recap is fully edited with narration, reactions and commentary throughout — built like your best friend retelling the entire story over your shoulder.

📖 Series: Return of the Top Class Master

How would you rate this chapter from 0 to 10? Drop your rating and why in the comments.

If you enjoyed it, like and subscribe — new recaps every Tuesday & Friday.

All recaps are commentary and criticism under fair use. I do not own the manhwa/artwork — all rights belong to their respective owners.
```

Cadence line kept consistent with every platform bio (Tue/Fri). If the channel
switches to daily uploads, edit this line at upload time.

## Tags (paste into the tags field)

`manhwa recap, manhwa recaps, webtoon recap, return of the top class master, regression manhwa, manhwa explained, webtoon explained, action manhwa recap, manhwa summary, korean manhwa, revenge manhwa, school manhwa, strongest mc, anime recap, fantasy manhwa`

## Upload-day checklist

1. Studio → Create → Upload videos → select `videos/return-of-the-top-class-master/ch001/ch001.mp4`
   (IAB has no file chooser — inject via page-side evaluate, chunked base64,
   per CHANNEL_SETUP.md method)
2. Title + description + tags from above
3. Thumbnail: `channel/return-of-the-top-class-master/thumbnail_ch001.png`
   — REQUIRES phone verification (Feature eligibility). If Intermediate
   features show "Eligible" not "Enabled": user must verify at
   youtube.com/verify first; upload everything else meanwhile.
4. Playlist: create "Return of the Top Class Master"
5. Audience: No, not made for kids (channel default)
6. Visibility: Public (user delegated the call for this upload)
7. Category Entertainment / language English (upload defaults already set)
8. After processing: verify 1080p HD available, add to playlist,
   pin the rating question as the first comment
9. Record the live URL in this file; update `channel/analytics/` trackers
