#!/usr/bin/env py
"""analytics_pull.py — pull current channel stats per platform into a dated snapshot.

Usage:
  py tools/analytics_pull.py                      # all platforms with working methods
  py tools/analytics_pull.py --platforms odysee,youtube

Verified methods live in channel/analytics/analytics-guide.md. Credentials (optional,
per-platform) come from channel/analytics/credentials.json. Output: a JSON snapshot in
channel/analytics/snapshots/<YYYY-MM-DD>.json plus a stdout summary. Counters are
cumulative — diff snapshots for window deltas.
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP_DIR = ROOT / "channel" / "analytics" / "snapshots"
CREDS_PATH = ROOT / "channel" / "analytics" / "credentials.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36"}


def http_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={"Content-Type": "application/json", **(headers or UA)})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def http_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def curl_json(url, data=None):
    cmd = ["curl", "-s", url]
    if data is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(data)]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    return json.loads(out)


def load_creds():
    if CREDS_PATH.exists():
        return json.loads(CREDS_PATH.read_text(encoding="utf-8"))
    return {}


# ---------------- YouTube (needs youtube_api_key) ----------------
def pull_youtube(creds):
    key = creds.get("youtube_api_key", "")
    if not key or "PASTE" in key:
        return {"error": "no youtube_api_key in credentials.json (one-time setup, see analytics-guide.md)"}
    ch = http_json(f"https://www.googleapis.com/youtube/v3/channels?part=statistics,contentDetails&forHandle=zeenifyrecaps&key={key}")
    c = ch["items"][0]
    uploads_playlist = c["contentDetails"]["relatedPlaylists"]["uploads"]
    vids, token = [], ""
    while True:
        u = f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={uploads_playlist}&maxResults=50&key={key}" + (f"&pageToken={token}" if token else "")
        r = http_json(u)
        vids += [i["contentDetails"]["videoId"] for i in r["items"]]
        token = r.get("nextPageToken", "")
        if not token:
            break
    stats = []
    for i in range(0, len(vids), 50):
        batch = ",".join(vids[i:i + 50])
        r = http_json(f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id={batch}&key={key}")
        for it in r["items"]:
            stats.append({"video_id": it["id"], "title": it["snippet"]["title"],
                          "published_at": it["snippet"]["publishedTime"],
                          "views": int(it["statistics"].get("viewCount", 0)),
                          "likes": int(it["statistics"].get("likeCount", 0)),
                          "comments": int(it["statistics"].get("commentCount", 0))})
    return {"subscribers": int(c["statistics"].get("subscriberCount", 0)),
            "channel_views": int(c["statistics"].get("viewCount", 0)), "videos": stats}


# ---------------- Facebook (needs fb_page_token) ----------------
def pull_facebook(creds):
    tok = creds.get("fb_page_token", "")
    if not tok or "PASTE" in tok:
        return {"error": "no fb_page_token in credentials.json (one-time setup, see analytics-guide.md)"}
    pid = creds.get("fb_page_id", "1365668179964095")
    posts = http_json(f"https://graph.facebook.com/v21.0/{pid}/posts?fields=id,message,created_time,permalink_url,likes.summary(true),comments.summary(true)&limit=100&access_token={tok}")
    vids = []
    for p in posts.get("data", []):
        vids.append({"video_id": p["id"], "title": (p.get("message") or "")[:60],
                     "published_at": p.get("created_time"), "url": p.get("permalink_url"),
                     "likes": p.get("likes", {}).get("summary", {}).get("total_count", 0),
                     "comments": p.get("comments", {}).get("summary", {}).get("total_count", 0)})
    return {"videos": vids}


# ---------------- TikTok (account level, no login) ----------------
def pull_tiktok(creds):
    html = http_text("https://www.tiktok.com/@zeenifyrecaps")
    m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html)
    if not m:
        return {"error": "profile page challenged (no rehydration JSON) — retry later or use official Display API"}
    d = json.loads(m.group(1))
    stats = d["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"].get("stats", {})
    return {"account_level_only": True,
            "followers": stats.get("followerCount"), "total_hearts": stats.get("heartCount"),
            "video_count": stats.get("videoCount"),
            "note": "per-video stats need the official Display API (analytics-guide.md)"}


# ---------------- Rumble (browser fallback — no HTTP method) ----------------
def pull_rumble(creds):
    return {"error": "no HTTP method (Cloudflare) — agent opens rumble.com/c/c-7963658 in the browser and reads view counts from the page"}


# ---------------- Odysee (fully open; MUST use curl — urllib hits an SSL cert issue) ----------------
def pull_odysee(creds):
    r = curl_json("https://api.na-backend.odysee.com/api/v1/proxy?m=claim_search",
                  {"jsonrpc": "2.0", "method": "claim_search",
                   "params": {"claim_type": ["stream"], "channel": "@edrickmartin101",
                              "order_by": ["release_time"], "page": 1, "page_size": 50}, "id": 1})
    items = r["result"]["items"]
    tok_path = ROOT / "tmp" / "odysee_user.json"
    if tok_path.exists():
        tok = json.loads(tok_path.read_text())["data"]["auth_token"]
    else:
        tok = curl_json("https://api.odysee.com/user/new")["data"]["auth_token"]
        tok_path.parent.mkdir(exist_ok=True)
        tok_path.write_text(json.dumps({"data": {"auth_token": tok}}))
    vids = []
    for it in items:
        cid = it["claim_id"]
        views = 0
        try:
            vc = curl_json(f"https://api.odysee.com/file/view_count?claim_id={cid}&auth_token={tok}")
            views = (vc.get("data") or [0])[0]
        except Exception:
            pass
        value = it.get("value", {})
        vids.append({"video_id": cid, "title": value.get("title", it["name"]),
                     "published_at": datetime.fromtimestamp(it["meta"]["creation_timestamp"], tz=timezone.utc).isoformat(),
                     "views": views})
    return {"videos": vids}


PULLERS = {"youtube": pull_youtube, "facebook": pull_facebook, "tiktok": pull_tiktok,
           "rumble": pull_rumble, "odysee": pull_odysee}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platforms", default="odysee,rumble")
    args = ap.parse_args()
    creds = load_creds()
    snapshot = {"captured_at": datetime.now(timezone.utc).isoformat(), "platforms": {}}
    for p in [x.strip().lower() for x in args.platforms.split(",") if x.strip()]:
        try:
            snapshot["platforms"][p] = PULLERS[p](creds)
        except Exception as e:
            snapshot["platforms"][p] = {"error": f"{type(e).__name__}: {e}"}
        time.sleep(0.5)
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAP_DIR / f"{date.today().isoformat()}.json"
    out.write_text(json.dumps(snapshot, indent=1), encoding="utf-8")
    print(f"snapshot -> {out}\n")
    for p, d in snapshot["platforms"].items():
        if "error" in d:
            print(f"[{p}] ERROR: {d['error']}")
        elif p == "tiktok":
            print(f"[{p}] followers={d.get('followers')} hearts={d.get('total_hearts')} videos={d.get('video_count')} (account level)")
        elif "videos" in d:
            vs = sorted(d["videos"], key=lambda v: -v.get("views", 0))
            total = sum(v.get("views", 0) for v in d["videos"])
            print(f"[{p}] videos={len(vs)} total_views={total} top=" +
                  "; ".join(f"{v['title'][:34]} ({v.get('views', 0)})" for v in vs[:3]))
        else:
            print(f"[{p}] {json.dumps({k: v for k, v in d.items() if k != 'videos'})[:120]}")


if __name__ == "__main__":
    main()
