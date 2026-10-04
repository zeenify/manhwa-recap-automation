# UPLOAD PREP — ch001 — Return of the Top Class Master (first YouTube chapter upload)

Status: PREP COMPLETE — waiting on ChatGPT thumbnail generation + YouTube upload session.
Follows the template from `channel/a-wimps-strategy-guide/upload-prep-merged-video.md`.
Thumbnail pipeline: `agents/thumbnail-agent.md`.

## Files

- **Video:** `videos/return-of-the-top-class-master/ch001/ch001.mp4` — 11m37s
  (697.4s), 1920×1080, h264+aac. Voice "mommy" (speed 1.07), verified against
  `audio/return-of-the-top-class-master/ch001/timing.json` (total 697.4s).
  **Do not use** `videos/return-of-the-top-class-master-mommy/` — that lane
  holds a stale pre-preset render (745.2s, raw voice, no speed preset).
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
