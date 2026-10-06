"""validate_shorts — QA gate for shorts scripts (main session runs this after
any writer agent works; writer self-QA is never trusted — ch10 precedent).

Checks per script in scripts/<slug>/shorts/ (skips _*.md and --skip ids):
- format: entry headers carry `BEAT NNNN` + `(chNNN)`; every referenced beat
  EXISTS in assets/<slug>/<chNNN>/beats/beats.json (the crop/render contract)
- narration hygiene: banned words (panel, sound effect, narrator, montage,
  caption, "all chapter"), asterisks, >1 em-dash per entry
- budgets: total narration <= --max-total words (default 150), per entry
  <= --max-entry (default 35), first entry (the hook) <= 15 words
- shape: 2..12 entries, TYPE line present, SHOT in the known vocabulary
- publishing pack is the last section (nothing speakable after an entry)

Usage:
  py tools/validate_shorts.py --slug a-wimps-strategy-guide
Exit code 1 if any script fails; prints one line per problem + JSON summary.
"""
import argparse
import json
import re
import sys
from pathlib import Path

BANNED = [r"\bpanel\b", r"\bsound\s+effect\b", r"\bnarrator\b", r"\bmontage\b",
          r"\bcaption\b", r"\ball\s+chapter\b"]
SHOTS = {"pan-down", "punch-in", "quick-zoom", "slow-zoom-out", "hold", "fit"}


def parse(script_path: Path):
    text = script_path.read_text(encoding="utf-8")
    entries = []
    for b in re.split(r"\n(?=### )", text):
        if not b.startswith("### "):
            continue
        header = b.split("\n", 1)[0]
        m_narr = re.search(r"NARRATION:\n(.*?)(?=\n---|\n## |\n### |\Z)", b, re.S)
        if not m_narr:
            entries.append({"header": header, "narration": None, "beats": [],
                            "chapter": None, "shot": None, "parse_error":
                            "no NARRATION block"})
            continue
        kept = [ln for ln in m_narr.group(1).splitlines()
                if not ln.lstrip().startswith("#")]
        narration = " ".join(" ".join(kept).split()).replace("*", "")
        m_beat = re.search(r"BEAT (\d+)", header)
        m_cov = re.search(r"covers (\d+)[–-](\d+)", header)
        m_ch = re.search(r"\((ch\d+)\)", header)
        m_shot = re.search(r"SHOT:\s*(\S+)", b)
        first = int(m_beat.group(1)) if m_beat else None
        beats = (list(range(int(m_cov.group(1)), int(m_cov.group(2)) + 1))
                 if (m_cov and first is not None) else
                 ([first] if first is not None else []))
        entries.append({"header": header, "narration": narration, "beats": beats,
                        "chapter": m_ch.group(1) if m_ch else None,
                        "shot": m_shot.group(1).lower() if m_shot else None,
                        "parse_error": None})
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="a-wimps-strategy-guide")
    ap.add_argument("--max-total", type=int, default=150)
    ap.add_argument("--max-entry", type=int, default=35)
    ap.add_argument("--skip", default="",
                    help="comma-separated short ids to skip (e.g. legacy scripts)")
    args = ap.parse_args()
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    beats_cache = {}
    def beats_of(ch):
        if ch not in beats_cache:
            p = Path(f"assets/{args.slug}/{ch}/beats/beats.json")
            beats_cache[ch] = ({b["beat"] for b in json.loads(p.read_text(encoding="utf-8"))}
                               if p.exists() else None)
        return beats_cache[ch]

    problems, summary = [], []
    files = sorted(Path(f"scripts/{args.slug}/shorts").glob("*.md"))
    for f in files:
        sid = f.stem
        if sid.startswith("_") or sid in skip:
            continue
        issues = []
        m_type = re.search(r"^TYPE:\s*(\S+)", f.read_text(encoding="utf-8"), re.M)
        if not m_type:
            issues.append("no TYPE line")
        entries = parse(f)
        if not (2 <= len(entries) <= 12):
            issues.append(f"{len(entries)} entries (need 2..12)")
        total_words = 0
        for ei, e in enumerate(entries):
            tag = f"{sid} e{ei:02d}"
            if e["parse_error"]:
                issues.append(f"{tag}: {e['parse_error']}")
                continue
            if not e["chapter"]:
                issues.append(f"{tag}: header missing (chNNN): {e['header'][:60]}")
            if not e["beats"]:
                issues.append(f"{tag}: header missing BEAT NNNN: {e['header'][:60]}")
            known = beats_of(e["chapter"]) if e["chapter"] else set()
            if known is None:
                issues.append(f"{tag}: no beats.json for {e['chapter']}")
            elif known:
                for b in e["beats"]:
                    if b not in known:
                        issues.append(f"{tag}: beat {b} not in {e['chapter']} beats.json")
            if e["shot"] not in SHOTS:
                issues.append(f"{tag}: SHOT '{e['shot']}' not in vocabulary")
            words = len(e["narration"].split())
            total_words += words
            if words > args.max_entry:
                issues.append(f"{tag}: {words} words > cap {args.max_entry}")
            if ei == 0:
                # hook must land a clause boundary within the first ~10 words
                # (the swipe decision happens by ~2.5s ≈ 7 spoken words)
                head = e["narration"].split()[:10]
                if not any(re.search(r"[,.!?;:]$", w) for w in head):
                    issues.append(f"{tag}: no hook boundary in first 10 words")
            low = e["narration"].lower()
            for pat in BANNED:
                if re.search(pat, low):
                    issues.append(f"{tag}: banned word /{pat}/")
            if "*" in e["narration"]:
                issues.append(f"{tag}: asterisk in narration")
            if e["narration"].count("—") > 1:
                issues.append(f"{tag}: {e['narration'].count('—')} em-dashes (>1)")
        if total_words > args.max_total:
            issues.append(f"{sid}: total {total_words} words > cap {args.max_total}")
        # nothing speakable may follow the last entry except the publishing pack
        tail = re.split(r"### [^\n]+\n(?:.(?!### ))*$", f.read_text(encoding="utf-8"),
                        flags=re.S)
        summary.append({"id": sid, "entries": len(entries), "words": total_words,
                        "ok": not issues})
        problems.extend(issues)
        print(("OK   " if not issues else "FAIL ") + f"{sid}  ({len(entries)} entries, {total_words}w)")
        for i in issues:
            print("     - " + i)
    print(json.dumps({"files": len(summary),
                      "ok": sum(1 for s in summary if s["ok"]),
                      "problems": len(problems)}))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
