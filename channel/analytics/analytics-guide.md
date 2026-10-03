# PLATFORM ANALYTICS GUIDE — how the analyzer agent pulls numbers

Verified 2026-10-04. This is the source of truth for HOW to fetch analytics per platform.
Companion protocol: `agents/analyzer-agent.md`. Starter script: `tools/analytics_pull.py`.

Status legend: ✅ WORKS TODAY (no login) · 🔑 WORKS (one-time user setup, then scripts) · 🌐 BROWSER FALLBACK (last resort only)

## Our account IDs (all platforms)

| Platform | Identity | Notes |
|---|---|---|
| YouTube | channel `@zeenifyrecaps` | 20 chapters + 1 compilation |
| Facebook Page | Page id `1365668179964095` (profile id 61594960413829) | 20 reels/videos |
| TikTok | `@zeenifyrecaps` | 20 videos |
| Rumble | channel `c-7963658` (https://rumble.com/c/c-7963658) | 20 videos |
| Odysee | channel `@edrickmartin101` (display "Zeenify"), claim_id `5c1422de080e00da3e0979c1209db3ca252378fb` | 20 videos |

## 1. YouTube — 🔑 YouTube Data API v3 (best data, needs ONE API key)

One-time setup (user, ~5 min):
1. https://console.cloud.google.com → new project → "APIs & Services" → Enable **YouTube Data API v3**.
2. Credentials → Create credentials → **API key**. No OAuth needed for public stats.
3. Put the key in `channel/analytics/credentials.json`: `{"youtube_api_key": "..."}`. NEVER commit it.

What the free key gives (10,000 units/day; each videos.list = 1 unit):
- Per video: `viewCount, likeCount, commentCount, publishTime, duration, title`
- Channel: `subscriberCount, viewCount, videoCount`

Endpoints (plain curl, no OAuth):
```
# channel stats
curl -s "https://www.googleapis.com/youtube/v3/channels?part=statistics,contentDetails&forHandle=zeenifyrecaps&key=KEY"
# all video ids (uploads playlist = channel uploads playlist id from channels.list contentDetails)
curl -s "https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId=UU...&maxResults=50&key=KEY"
# stats in batches of 50
curl -s "https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id=ID1,ID2,...&key=KEY"
```
Date filtering: `snippet.publishTime` — the agent filters client-side ("last week" = published in range,
and for views-delta you compare against a stored snapshot — see "Snapshots" below).
⚠️ What the free key does NOT give: watch time / retention / traffic sources → those need YouTube
Analytics API + OAuth (skip unless the user asks; the browser fallback for those numbers is
studio.youtube.com logged in as the user).

## 2. Facebook Page — 🔑 Graph API (needs ONE Page access token)

One-time setup (user, ~10 min):
1. https://developers.facebook.com → Create App (type: Business) — any name.
2. In the app: Tools → **Graph API Explorer** → generate **User token** with permissions
   `pages_show_list, pages_read_engagement, read_insights, pages_manage_metadata`.
   (The user logs in with the FB account that owns the Zeenify Page.)
3. Convert: `GET /me/accounts?access_token=USER_TOKEN` → copy the Page's `access_token`.
   Long-lived version: `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=USER_TOKEN` then `/me/accounts` again → Page token that lasts ~60 days.
4. Store in `channel/analytics/credentials.json`: `{"fb_page_id": "1365668179964095", "fb_page_token": "..."}`.

Endpoints (curl, version v21.0+):
```
# page level (most Page metrics update once per 24h)
curl -s "https://graph.facebook.com/v21.0/1365668179964095/insights?metric=page_views,page_impressions_unique,pages_read_engagement&period=day&access_token=TOKEN"
# our video/reel posts with engagement
curl -s "https://graph.facebook.com/v21.0/1365668179964095/posts?fields=id,message,created_time,permalink_url&limit=100&access_token=TOKEN"
# per-post stats (works for video posts)
curl -s "https://graph.facebook.com/v21.0/POST_ID?fields=likes.summary(true),comments.summary(true),sharedposts,views&access_token=TOKEN"
```
Date filtering: `created_time` client-side + `insights?period=day&since=...&until=...` with unix timestamps.

## 3. TikTok — split approach

**Account level (✅ works today, no login)** — the public profile page embeds a stats JSON:
```
curl -s "https://www.tiktok.com/@zeenifyrecaps" -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36" -o tmp/tiktok.html
```
Parse `<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">` JSON → `__DEFAULT_SCOPE__/webapp.user-detail/userInfo/stats`
= `followerCount, heartCount, videoCount`. (Verified working 2026-10-04; TikTok may start challenging
plain curl someday — if the fetch returns a "Just a moment..." page, that's the signal to switch to the
official API below.)

**Per-video level (🔑 official Display API)** — needs one-time user setup:
1. https://developers.tiktok.com → manage apps → create app (product: Display API, scopes: `user.info.basic`, `video.list`).
2. Sandbox → add the user's TikTok account as a test user.
3. Authorize once in a browser: `https://www.tiktok.com/v2/auth/authorize/?client_key=CLIENT_KEY&scope=user.info.basic,video.list&response_type=code&redirect_uri=REDIRECT` → code → exchange for user access token (lasts 24h; refresh token lasts 365d — store it, refresh programmatically).
4. Then per-video stats, no browser:
```
curl -s -X POST "https://open.tiktokapis.com/v2/video/list/?fields=id,title,view_count,like_count,comment_count,share_count,create_time" \
  -H "Authorization: Bearer USER_TOKEN" -d '{"max_count":20}'
```
⚠️ Display API may only return videos posted AFTER the authorization — test once after setup; if old
videos are missing, per-video history for the existing 20 stays browser-only (creator analytics page).

## 4. Rumble — 🌐 NO public analytics API; Cloudflare blocks plain curl

Verified: `rumble.com` video/channel/RSS pages all return a Cloudflare "Just a moment..." challenge to
curl (2026-10-04). Only the oEmbed endpoint is open (no view counts):
```
curl -s "https://rumble.com/api/Media/oembed.json?url=VIDEO_URL"   # title/author only
```
So Rumble = **browser fallback** (the only platform where it's unavoidable):
- IAB browser → open https://rumble.com/c/c-7963658 → the channel grid shows each video's **view count**;
  the creator dashboard (rumble.com, logged in) shows fuller analytics.
- The agent reads the numbers from the page DOM (browser-use, no computer-use needed — it's web content)
  and reports them like any other platform.
- Check once per quarter whether Rumble ships a real API; revisit.

## 5. Odysee — ✅ FULLY AUTOMATED (no login at all)

Verified end-to-end 2026-10-04. Two API layers:

```
# 1) channel uploads (claim_search — no auth):
curl -s -X POST "https://api.na-backend.odysee.com/api/v1/proxy?m=claim_search" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"claim_search","params":{"claim_type":["stream"],"channel":"@edrickmartin101","order_by":["release_time"],"page":1,"page_size":50},"id":1}'
# → items[] with claim_id, name (ch001..ch020), meta.creation_timestamp (unix), value.title/description/tags

# 2) anonymous auth token (for view counts):
curl -s "https://api.odysee.com/user/new"     # → data.auth_token (create once, cache it)

# 3) views per claim (legacy API, singular claim_id, token as query param):
curl -s "https://api.odysee.com/file/view_count?claim_id=CLAIM_ID&auth_token=TOKEN"
# → {"success":true,"data":[N]}    (views update slowly for fresh uploads — data:[0] right after publish is normal)
```
Date filtering: `meta.creation_timestamp`. Likes/dislikes: Odysee's reaction API needs a LOGGED-IN
token (not anon) — treat likes as optional/n-a for now.
⚠️ All Odysee requests must be `curl` (Python urllib fails with a local SSL cert error — known Windows
cert-store issue; curl is unaffected).

## Snapshots (how "views this week" works)

Views are cumulative counters on every platform. To report "last week's views", the agent:
1. Pulls current per-video counters and stores them in `channel/analytics/snapshots/<date>.json`
   (`{platform, video_id, views, likes, comments, captured_at}`).
2. Diff against the previous snapshot for the requested window (e.g. last-7-days = today vs 7 days ago;
   if no snapshot exists that far back, report "cumulative so far" and start the snapshot history).
3. So the FIRST run establishes the baseline; every later run gets real deltas. Run it daily (cron) for
   the best history.

## Credentials

- Real tokens live in `channel/analytics/credentials.json` — never echo, never commit.
- Template: `channel/analytics/credentials.example.json`. Add `channel/analytics/credentials.json` to `.gitignore`.
