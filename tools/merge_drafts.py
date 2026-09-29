"""merge_drafts — fuse reader-agent part drafts into one chapter draft.

Handles both spawn layouts:
- SEQUENTIAL parts (adjacent ranges): fuses the seam panel when the previous part
  flagged "continues" and the next flagged "continues_from_previous".
- PARALLEL parts (ranges overlapping by ~2000px, both sides judged the seam):
  drops the next part's beats that duplicate the earlier part's coverage, and
  fuses the beat that COMPLETES a range-cut panel (prev flagged "continues" and
  the next beat straddles/touches prev's cut end — its far edge is the truth).

Usage:
  python tools/merge_drafts.py --out <merged.json> <part1.json> <part2.json> ...
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parts", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    parts = [json.loads(open(p, encoding="utf-8").read()) for p in args.parts]
    # defensive: process in y-order regardless of argument order
    order = sorted(range(len(parts)), key=lambda i: parts[i].get("range", [0])[0])
    parts = [parts[i] for i in order]

    beats, excluded = [], []
    fused = deduped = 0
    for d in parts:
        kept = []
        for nxt in d["beats"]:
            if beats:
                prev = beats[-1]
                if nxt["y_end"] <= prev["y_end"]:
                    deduped += 1  # entirely inside the earlier part's coverage
                    continue
                if nxt["y_start"] <= prev["y_end"]:  # touches or straddles the seam
                    if prev.get("continues"):
                        # completes prev's range-cut panel: fuse, far edge wins
                        prev["y_end"] = nxt["y_end"]
                        prev["event"] = (prev.get("event", "") + " || " + nxt.get("event", "")).strip(" |")
                        for k in ("continues", "continues_from_previous"):
                            prev.pop(k, None)
                        if nxt.get("continues"):
                            prev["continues"] = True
                        fused += 1
                        continue
                    # prev's end is a verified panel edge: keep only the new part
                    if nxt["y_end"] - prev["y_end"] < 100:
                        deduped += 1  # sub-100px sliver of duplicate coverage
                        continue
                    nxt = {k: v for k, v in nxt.items() if k != "continues_from_previous"}
                    nxt["y_start"] = prev["y_end"]
            kept.append(nxt)
        beats.extend(kept)
        excluded.extend(d.get("excluded", []))

    # dedup + sort excluded (overlap zones double-report exclusions)
    seen, uniq = set(), []
    for e in sorted(excluded, key=lambda x: (x["y_start"], x["y_end"], x.get("type", ""))):
        k = (e["y_start"], e["y_end"], e.get("type", ""))
        if k not in seen:
            seen.add(k)
            uniq.append(e)

    # sanity: report overlaps / gaps so problems surface before crop
    overlaps = gaps = 0
    for a, b in zip(beats, beats[1:]):
        if b["y_start"] < a["y_end"]:
            overlaps += 1
        elif b["y_start"] - a["y_end"] > 50:
            gaps += 1

    out = {
        "range": [beats[0]["y_start"], max(b["y_end"] for b in beats)],
        "beats": beats,
        "excluded": uniq,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({
        "out": args.out, "parts": len(args.parts), "seams_fused": fused,
        "duplicate_beats_dropped": deduped,
        "total_beats": len(beats), "total_excluded": len(uniq),
        "coverage": out["range"],
        "warnings": {"beat_overlaps": overlaps, "gaps_over_50px": gaps},
    }, indent=1))


if __name__ == "__main__":
    main()
