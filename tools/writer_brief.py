"""writer_brief — pre-digest everything the writer agent needs into ONE file.

The writer used to read beats.json + both handoffs + story-so-far + the previous
script separately (lots of redundant reading = slow turns). This packs the same
information into a single brief: beats digest (with aspect ratios for shot
choices), handoff synopses, and the rolling continuity memo.

Usage:
  python tools/writer_brief.py --slug a-wimps-strategy-guide --chapter ch002 \
      --out tmp/writer_brief_ch002.md
"""
import argparse
import json
from pathlib import Path

PAN_TALL_ASPECT = 1.67  # informational: panels taller than this render as a centered column


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--chapter", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    beats = json.loads(
        Path(f"assets/{args.slug}/{args.chapter}/beats/beats.json").read_text(encoding="utf-8"))
    num = args.chapter.lower().lstrip("ch").lstrip("0") or "0"
    chapter_dir = None
    for pad in (len(num), 2, 3, 4):
        cand = Path(f"toonverse/{args.slug}/chapter-{num.zfill(pad)}")
        if cand.exists():
            chapter_dir = cand
            break
    if chapter_dir is None:  # fallback: newest chapter dir under the slug
        cands = sorted(Path(f"toonverse/{args.slug}").glob("chapter-*"))
        chapter_dir = cands[-1] if cands else Path(f"toonverse/{args.slug}/chapter-{num.zfill(2)}")
    handoffs = sorted(chapter_dir.glob("handoff_*.json"))
    story = Path("story-so-far.md")

    lines = []
    lines.append(f"# WRITER BRIEF — {args.slug} — {args.chapter}")
    lines.append("")
    lines.append("Auto-generated. Together with `tone.md` and `research/narration_style_notes.md`,")
    lines.append("this file is ALL you need — do not open beats.json, the handoff JSONs,")
    lines.append("story-so-far.md, or any previous script. Everything is already here.")
    lines.append("")
    lines.append("Aspect hint for SHOT choices: tall panels (aspect h/w above ~1.67) may use")
    lines.append("pan-down — a reduced-width scroll: the panel renders as a 70%-width centered")
    lines.append("column over a blurred background and scrolls down gently (never full-width).")
    lines.append("PACING: a pan-down scrolls at panel height ÷ narration duration, so any beat")
    lines.append("marked TALL (and especially aspect ≥ 2.2) needs the upper half of the word")
    lines.append("range (25–45 words) — a short entry over a tall strip scrolls too fast to read.")
    lines.append("Shorter-than-frame panels: moves on the composed card (hold / punch-in /")
    lines.append("quick-zoom / slow-zoom-out / fit).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## STORY SO FAR (rolling continuity memo — law for continuity)")
    lines.append("")
    if story.exists():
        lines.append(story.read_text(encoding="utf-8").strip())
    else:
        lines.append("(no story-so-far.md found — first chapter)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## READER HANDOFF SYNOPSES")
    lines.append("")
    for h in handoffs:
        d = json.loads(h.read_text(encoding="utf-8"))
        lines.append(f"### {h.name}")
        lines.append(f"Range: {d.get('range', '?')}" if d.get("range") else "")
        lines.append(f"Story: {d.get('story_so_far', '')}")
        chars = d.get("characters", [])
        if chars:
            lines.append(f"Characters seen: {'; '.join(chars)}")
        for an in d.get("anomalies", []):
            lines.append(f"- anomaly: {an}")
        lb = d.get("last_beat")
        if lb:
            lines.append(f"Last beat: y_end {lb.get('y_end')}, continues={lb.get('continues')} — {lb.get('description', '')}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## BEATS DIGEST — {len(beats)} beats (use these exact beat numbers)")
    lines.append("")
    for b in beats:
        w, h = b.get("w", 0), b.get("h", 0)
        aspect = h / max(1, w)
        tall = "  ← TALL (pan-down eligible)" if aspect > PAN_TALL_ASPECT else ""
        fx, fy = b.get("focal_point", [0.5, 0.5])
        lines.append(f"- B{b['beat']:03d} | {b.get('composition','?')} | {w}x{h} (aspect {aspect:.2f}) | focal ({fx:.2f}, {fy:.2f}){tall}")
        lines.append(f"  event: {b.get('event','')}")
    lines.append("")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "out": args.out, "beats": len(beats), "handoffs": [h.name for h in handoffs],
        "bytes": out_path.stat().st_size,
    }, indent=1))


if __name__ == "__main__":
    main()
