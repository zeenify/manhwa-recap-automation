import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SERIES = "return-of-the-top-class-master"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIRST, LAST = 1, 20  # user decision 2026-10-04: only the first 20 chapters for now
WORKERS = 6
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://toonverse.net/",
    "Origin": "https://toonverse.net",
}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_with_retry(url, tries=3):
    last = None
    for i in range(tries):
        try:
            return fetch(url)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def is_image(data):
    return len(data) > 10_000 and (data[:2] == b"\xff\xd8" or (data[:4] == b"RIFF" and data[8:12] == b"WEBP"))


def download_chapter(n):
    ch_dir = os.path.join(BASE_DIR, f"chapter-{n:02d}")
    os.makedirs(ch_dir, exist_ok=True)

    api = f"https://api.toonverse.net/api/reading/chapter/{SERIES}/{n}"
    data = json.loads(fetch_with_retry(api))
    if not data.get("success"):
        return n, 0, 0, f"API error: {data.get('error', {}).get('message', 'unknown')}"

    pages = data["data"]["chapter"]["pages"]
    pages = sorted(pages, key=lambda p: p["number"])
    urls = [p["imageUrl"] for p in pages]

    def grab(url):
        name = os.path.basename(url.split("?")[0])
        dest = os.path.join(ch_dir, name)
        if os.path.exists(dest) and is_image(open(dest, "rb").read(16) if os.path.getsize(dest) > 10_000 else b""):
            return True
        try:
            body = fetch_with_retry(url)
            if not is_image(body):
                return False
            with open(dest, "wb") as f:
                f.write(body)
            return True
        except Exception:  # noqa: BLE001
            return False

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(grab, urls))
    ok = sum(results)
    return n, ok, len(urls), None if ok == len(urls) else "some pages failed verification"


def main():
    os.chdir(BASE_DIR)
    failures = []
    for n in range(FIRST, LAST + 1):
        t0 = time.time()
        try:
            n, ok, total, err = download_chapter(n)
        except Exception as e:  # noqa: BLE001
            failures.append((n, str(e)))
            print(f"chapter {n:02d}: FAILED ({e})", flush=True)
            continue
        status = "OK" if err is None else err
        print(f"chapter {n:02d}: {ok}/{total} pages {status} ({time.time() - t0:.1f}s)", flush=True)
        if err:
            failures.append((n, err))

    print("---")
    if failures:
        print("FAILED CHAPTERS:", failures)
        sys.exit(1)
    print("all chapters complete")


if __name__ == "__main__":
    main()
