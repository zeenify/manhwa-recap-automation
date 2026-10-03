# Zeenify Analytics — first report (Rumble + Odysee), captured 2026-10-04

**Headline:** Day 1 of distribution. All numbers are at zero — that is expected, not a problem.
The uploads went live yesterday; view counters on both platforms (and their dashboards) lag behind
real plays by hours to days. Today's run establishes the baseline that makes every future report
show real growth.

## Rumble (source: logged-in creator dashboard, account/dashboard)

Channel: rumble.com/c/c-7963658 — 20/20 videos live and public.

- All-time views: **0**
- Followers: **0** (Rumble Creator Program unlocks at 100 followers — worth pushing in video outros)
- Last 30 days: earnings $0.00, views 0, hours viewed 0, new followers 0
- Per-video: all 20 chapters show 0 views / 0 likes / 0 comments

Note: the first draft of this report quoted ~500K views — that was a measurement bug (the sweep
matched recommended-video counters in page sidebars, not the actual video). The dashboard is the
source of truth; the extraction method in the guide has been corrected.

## Odysee (source: open API, 2026-10-04)

Channel: odysee.com/@edrickmartin101 — all 20 chapters published.

- Views: **0** across the board — normal: LBRY view counters update slowly and the uploads are <36h old.
- 11 of 20 uploads are visible via the API so far; the other 9 are still confirming on the LBRY
  blockchain after the bulk publish (up to ~24h). No action needed.

## YouTube + Facebook — intentionally disabled

Owner decision (security): no API keys or tokens are connected to either platform, and the keys/apps
created during setup were removed (see "Security cleanup"). If you want YouTube numbers without any
API, the fallback is reading studio.youtube.com analytics in the browser while logged in.

## Security cleanup (done 2026-10-04)

- YouTube: the API key created during setup was deleted from local storage. It was also inert: it
  landed in a Google project (number 713371666174) that this account cannot manage, with the YouTube
  Data API disabled on it — the key could never return data. If Google ever emails about that
  project, delete it via the console's "Request access" flow.
- Facebook: the "Zeenify Analytics" Meta app was deleted (id 2154598331912323). No app secret was
  ever revealed and no access tokens were ever generated — the Page was never connected to it.
- TikTok analytics: disabled per owner decision (no keys were ever created for TikTok).

## What runs where now

- `py tools/analytics_pull.py` → Odysee (open API, fully automatic) + Rumble (logged-in dashboard
  via browser). Saves a dated snapshot to `channel/analytics/snapshots/`.
- Run it daily. After two snapshots exist, reports include real "views this week" deltas and per-video
  movers instead of baseline zeros.
