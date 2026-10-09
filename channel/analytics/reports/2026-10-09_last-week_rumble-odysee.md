# Zeenify Analytics — last week (Oct 4–9 2026), Rumble + Odysee

Rumble is alive but tiny: 20 recaps, 243 total views (11–14 per video, flat). Odysee: 0 views over the whole window — unchanged since Oct 4.

## Rumble (browser DOM read, captured 2026-10-09)
- Followers: not rendered on the channel page (no counter available this pull)
- Videos live: 20/20 chapters (all posted Oct 3, "6 days ago")
- Total views: 243 (as-of-now counters; **no prior baseline** — the Oct 4 pull died on Cloudflare, so this run starts the Rumble baseline)
- Top this window: "Chapter 20" and "Chapter 17" — 14 views each
- Underperformers: "Chapter 12", "Chapter 14" — 11 views each
- Engagement notes: views are near-uniform (11–14) across every chapter; no standout suggests a platform-side trickle rather than discovery. Rumble pays from the first view, so 243 views is a real (if tiny) revenue seed.

## Odysee (official API, captured 2026-10-09)
- Videos visible: 11 (ch01, ch02, ch10–ch18) — ch03–09, ch19, ch20 are NOT visible via the API; likely missing uploads or pagination. Worth a one-time check.
- Total views: 0 (delta vs Oct 4 snapshot: **+0** — 5 days, no movement)
- Top / underperformer: none — every video at 0

## Cross-platform takeaways
- **Rumble:** the only one of the two producing any measurable traffic. At this size the lever is watch-time: funnel traffic from the YT/TikTok shorts (pinned comments, bio links) rather than expecting Rumble discovery.
- **Odysee:** two snapshots five days apart both at zero. Keep it as zero-effort syndication only; don't wire it into funnels or spend time on thumbnails/titles there.
- **One action this week:** make the snapshot a daily habit (`py tools/analytics_pull.py` + the Rumble browser read) — from today Rumble has a baseline, so next week's report can show true deltas and tell us whether the shorts wave (11 posts today) moves any Rumble traffic.

## Data quality
- Rumble: browser DOM read (Cloudflare blocks HTTP); counters as of 2026-10-09, whole-view rounding. Baseline starts today; deltas available from the next run.
- Odysee: API via `tools/analytics_pull.py`; both snapshots agree at 0 views. 11/20 chapters visible — flag for a one-time upload audit.
- YouTube / Facebook / TikTok analytics: disabled by owner decision (security); manual browser reads remain the fallback.
