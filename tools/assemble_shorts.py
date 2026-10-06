"""assemble_shorts — render ONE 30-60s vertical short (1080x1920/30fps) from a
shorts script + TTS timing. The shorts sibling of assemble.py: same composed-card
camera grammar (blurred darkened panel fills the frame, sharp panel centered),
same shot vocabulary, same audio-is-the-clock sync contract, vertical edition.

Shorts script format (scripts/<slug>/shorts/<short>.md):

    # SHORT — <slug> — <short-id> — <title>
    TYPE: cliffhanger|loop|spotlight|countdown|roast
    (free-form header lines — ignored; a ## PUBLISHING PACK section is fine)

    ### BEAT 0070 (ch010) — title
    SHOT: pan-down|punch-in|quick-zoom|slow-zoom-out|hold|fit
    NARRATION:
    ...

- Header must contain `BEAT <digits>` and `(chNNN)` (chapter of the beat);
  optional `covers NNN-MMM` renders a sequential multi-beat entry.
- One TTS mp3 per entry; the entry's screen time = its mp3 duration.
- A short MAY cross chapters (refs name the chapter per beat).

Pipeline: one silent segment per entry (camera move) → concat (+ funnel
endcard) → burn karaoke captions (ASS, estimated word timing — no forced
alignment) → mux narration (loudnorm -14 LUFS, tail pad for the endcard).

Usage:
  py tools/assemble_shorts.py --slug a-wimps-strategy-guide --short 001_door_kick
  py tools/assemble_shorts.py --slug ... --short ... --test N   # first N entries, no endcard

Idempotent per segment clip — delete videos/<slug>/shorts/<short>/clips/ after
changing shots/beats/captions, or stale clips get reused (long-form gotcha).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FPS = 30
W, H = 1080, 1920
SS_W = 2160          # supersample width for zoompan quality
PAN_W = 0.75         # pan-down column width fraction (tall art fills 9:16 natively)
PAN_MAX_SPEED = 320  # px/s cap at output scale (research: 100-200 dialogue, 300-500 sparse)
ENDCARD_S = 1.8      # funnel endcard length (last frame = series + CTA)
CAP_FONT = "Arial Black"
CAP_SIZE = 72
CAP_TOP = 1230       # captions anchor TOP-center here — fixed first line, no jumping
CAP_MAX_WORDS = 3    # Hormozi-style short cards; longer cards wrap downward
DARK = (14, 14, 16)
FONTS = "C:/Windows/Fonts"

_WHISPER = None


def speech_spans(mp3: Path):
    """Real word start/end times via faster-whisper (local, CPU). Returns
    [(start, end), ...] or None if unavailable — the caller then falls back to
    proportional estimation. Model loads once per run."""
    global _WHISPER
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("captions: faster-whisper not installed — proportional timing "
              "(install with: py -m pip install faster-whisper)", file=sys.stderr)
        return None
    if _WHISPER is None:
        _WHISPER = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _info = _WHISPER.transcribe(str(mp3), language="en", word_timestamps=True)
    spans = []
    for s in segments:
        for w in (s.words or []):
            if w.word.strip():
                spans.append((w.start, w.end))
    return spans or None


def sh(cmd, cwd=None, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, **kw)
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd[:6])}...")


def ffprobe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def parse_short(script_path: Path):
    """Entries: header (BEAT n, covers n-m, (chNNN)), SHOT, NARRATION.
    Same leak guards as tts_generate.parse_script — narration ends at any
    ## header, and #/SHOT/NARRATION lines never reach the spoken text."""
    text = script_path.read_text(encoding="utf-8")
    entries = []
    for b in re.split(r"\n(?=### )", text):
        if not b.startswith("### "):
            continue
        header = b.split("\n", 1)[0]
        m_narr = re.search(r"NARRATION:\n(.*?)(?=\n---|\n## |\n### |\Z)", b, re.S)
        if not m_narr:
            continue
        kept = [ln for ln in m_narr.group(1).splitlines()
                if not ln.lstrip().startswith("#")]
        narration = " ".join(" ".join(kept).split()).replace("*", "")
        if "#" in narration or "SHOT:" in narration:
            raise SystemExit(f"DIRTY narration in {header}")
        m_beat = re.search(r"BEAT (\d+)", header)
        m_ch = re.search(r"\((ch\d+)\)", header)
        if not m_beat or not m_ch:
            raise SystemExit(f"header needs `BEAT NNNN (chNNN)`: {header}")
        first = int(m_beat.group(1))
        m_cov = re.search(r"covers (\d+)[–-](\d+)", header)
        beats = list(range(int(m_cov.group(1)), int(m_cov.group(2)) + 1)) if m_cov else [first]
        m_shot = re.search(r"SHOT:\s*(\S+)", b)
        title = re.sub(r"^### [^—]*—\s*", "", header).strip()
        entries.append({"chapter": m_ch.group(1), "beats": beats, "shot":
                        (m_shot.group(1).lower() if m_shot else "hold"),
                        "title": title, "narration": narration})
    return entries


def segment_filter(move: str, dur: float, fp) -> str:
    """Vertical edition of assemble.py's segment_filter. pan-down scrolls a
    75%-width centered column (smoothstepped) over the blurred bg; every other
    move is a composed card under zoompan."""
    frames = max(2, round(dur * FPS))
    fx, fy = (fp or [0.5, 0.5])[:2]
    if move == "pan-down":
        cw = int(W * PAN_W)
        q = f"clip(t/{dur:.3f},0,1)"
        ease = f"({q})*({q})*(3-2*({q}))"  # smoothstep in/out — no whip starts
        return (
            f"[0:v]split[bgs][fgs];"
            f"[bgs]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=luma_radius=16:luma_power=2,eq=brightness=-0.12[bg];"
            f"[fgs]scale={cw}:-2[fg];"
            f"[bg][fg]overlay=x=(W-w)/2:y='-(h-{H})*{ease}',"
            f"fps={FPS},setsar=1,format=yuv420p")
    if move == "punch-in":
        z = f"min(1+0.12*on/{frames},1.12)"
    elif move == "quick-zoom":
        z = f"min(1+0.16*on/{frames},1.16)"
    elif move == "slow-zoom-out":
        z = f"max(1.12-0.12*on/{frames},1.0)"
    elif move == "fit":
        z = f"min(1+0.035*on/{frames},1.035)"
    else:  # hold
        z = f"min(1+0.05*on/{frames},1.05)"
    bx = max(0.2, min(0.8, 0.5 + 0.4 * (fx - 0.5)))
    by = max(0.2, min(0.8, 0.5 + 0.4 * (fy - 0.5)))
    return (
        f"[0:v]split[bgs][fgs];"
        f"[bgs]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"boxblur=luma_radius=16:luma_power=2,eq=brightness=-0.12[bg];"
        f"[fgs]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,scale={SS_W}:-2,"
        f"zoompan=z='{z}':x='(iw-iw/zoom)*{bx}':y='(ih-ih/zoom)*{by}':"
        f"d=1:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")


def render_segment(img: Path, dur: float, move: str, fp, out: Path):
    vf = segment_filter(move, dur, fp)
    sh(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}",
        "-i", str(img), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-an", str(out)])


# ---------------------------------------------------------------- captions

def word_weight(word: str) -> float:
    w = len(re.sub(r"[^A-Za-z0-9']", "", word)) + 1.0
    if re.search(r"[.!?]$", word):
        w += 2.0
    elif re.search(r"[,;:]$", word):
        w += 1.0
    return w


def keyword_of(card):
    best, blen = None, 4
    for wd in card:
        core = re.sub(r"[^A-Za-z0-9']", "", wd)
        if len(core) > blen:
            best, blen = wd, len(core)
    return best


def ass_time(t: float) -> str:
    cs = max(0, int(round(t * 100)))
    return f"{cs // 360000:01d}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def build_ass(entries, timing, out: Path):
    """Karaoke captions synced to real speech: word times come from
    faster-whisper on each entry's mp3 (exact per-word spans when the tokenizer
    agrees with the script, else proportional interpolation inside the real
    speech window; falls back to duration estimates only if whisper fails).
    Cards anchor TOP-center at a fixed line so multi-line cards never make the
    text jump around — that was the 'shaky caption' defect."""
    pad = timing.get("pad_s", 0.0)
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
        "WrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,{CAP_FONT},{CAP_SIZE},&H00FFFFFF,&H00303030,&H00000000,"
        f"&H00000000,0,0,0,0,100,100,0,0,1,5,0,8,50,50,{CAP_TOP},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n")
    lines, offset = [], 0.0
    for e, tm in zip(entries, timing["entries"]):
        words = e["narration"].split()
        weights = [word_weight(w) for w in words]
        window = max(0.5, tm["duration_s"] - pad)
        spans = speech_spans(Path(e["file"]))
        if spans is not None:
            # whisper timestamps are relative to the entry's own mp3 — shift
            # them into the short's timeline (concat position of this entry)
            spans = [(s + offset, t + offset) for s, t in spans]
        if spans is not None and len(spans) != len(words):
            if len(spans) >= 2:
                # tokenizer mismatch: interpolate inside the REAL speech window
                lo, hi = spans[0][0], spans[-1][1]
                total_w = sum(weights)
                spans, acc = [], lo
                for wt in weights:
                    spans.append((acc, acc + (hi - lo) * wt / total_w))
                    acc += (hi - lo) * wt / total_w
                mode = "anchor"
            else:
                spans = None
        if spans is None:
            total_w = sum(weights)
            spans, acc = [], offset
            for wt in weights:
                spans.append((acc, acc + window * wt / total_w))
                acc += window * wt / total_w
            mode = "estimate"
        else:
            mode = "whisper"
        # regroup into short cards anchored at real word times
        cards, cur = [], []
        for i, wd in enumerate(words):
            cur.append(i)
            nxt = words[i + 1] if i + 1 < len(words) else ""
            if len(cur) >= CAP_MAX_WORDS or (len(cur) >= 2 and re.search(r"[.!?]$", wd)) \
                    or (nxt and len(nxt) > 9):
                cards.append(cur)
                cur = []
        if cur:
            cards.append(cur)
        for card in cards:
            start = spans[card[0]][0]
            end = max(spans[card[-1]][1], start + 0.25) + 0.12  # small linger
            parts = []
            kw = keyword_of([words[i] for i in card])
            for pos, i in enumerate(card):
                # \k runs back-to-back from the card start, so each word's k
                # must span UP TO the next word's real start (gaps included)
                # or pauses inside a card would fire the highlight early
                nxt = spans[card[pos + 1]][0] if pos + 1 < len(card) else spans[i][1]
                kcs = max(4, int(round((nxt - spans[i][0]) * 100)))
                mark = f"{{\\c&H00FFFF&}}" if words[i] == kw else ""
                reset = "{\\c&HFFFFFF&}" if words[i] == kw else ""
                parts.append(f"{{\\k{kcs}}}{mark}{words[i]}{reset}")
            lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},"
                         f"Cap,,0,0,0,,{' '.join(parts)}")
        offset += tm["duration_s"]
        print(f"captions entry '{e['title']}': {mode} timing")
    out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def build_endcard(out: Path, series_title: str):
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    black = ImageFont.truetype(f"{FONTS}/ariblk.ttf", 88)
    small = ImageFont.truetype(f"{FONTS}/ariblk.ttf", 46)
    def center(text, font, y, fill):
        tw = d.textlength(text, font=font)
        d.text(((W - tw) / 2, y), text, font=font, fill=fill)
    # long titles wrap onto two lines — a 1080px frame fits ~18 Arial Black
    # glyphs at 88pt, so never render the title as one long line
    words = series_title.split()
    line1, line2 = series_title, None
    while d.textlength(line1, font=black) > W - 160 and len(words) > 1:
        line2 = words.pop() + ("" if line2 is None else " " + line2)
        line1 = " ".join(words)
    if line2:
        center(line1, black, 620, (255, 255, 255))
        center(line2, black, 740, (255, 255, 255))
    else:
        center(line1, black, 700, (255, 255, 255))
    d.rectangle([(W - 360) / 2, 900, (W + 360) / 2, 906], fill=(255, 255, 0))
    center("FULL RECAP ON THE CHANNEL", small, 960, (170, 170, 170))
    img.save(out)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default="a-wimps-strategy-guide")
    ap.add_argument("--short", default="001_door_kick",
                    help="short id; script at scripts/<slug>/shorts/<short>.md")
    ap.add_argument("--test", type=int, default=0,
                    help="render only the first N entries (smoke test, no endcard)")
    ap.add_argument("--series-title", default=None,
                    help="title shown on the funnel endcard")
    args = ap.parse_args()

    script_path = Path(f"scripts/{args.slug}/shorts/{args.short}.md")
    entries = parse_short(script_path)
    timing = json.loads(Path(
        f"audio/{args.slug}/shorts/{args.short}/timing.json").read_text(encoding="utf-8"))
    if len(entries) != len(timing["entries"]):
        raise SystemExit(f"script has {len(entries)} entries, timing.json has "
                         f"{len(timing['entries'])} — re-run tts_generate")

    for e in entries:
        ch = e["chapter"]
        idx = {b["beat"]: b for b in json.loads(Path(
            f"assets/{args.slug}/{ch}/beats/beats.json").read_text(encoding="utf-8"))}
        missing = [b for b in e["beats"] if b not in idx]
        if missing:
            raise SystemExit(f"beat(s) {missing} not in assets/{args.slug}/{ch}/beats/beats.json")
        e["imgs"] = [Path(f"assets/{args.slug}/{ch}/beats/{idx[b]['file']}") for b in e["beats"]]
        e["meta"] = [idx[b] for b in e["beats"]]
        e["file"] = None
    for e, tm in zip(entries, timing["entries"]):
        e["file"] = tm["file"]
        e["dur"] = tm["duration_s"]

    work = Path(f"videos/{args.slug}/shorts/{args.short}")
    clips = work / "clips"
    clips.mkdir(parents=True, exist_ok=True)

    n_seg = 0
    for ei, e in enumerate(entries):
        if args.test and ei >= args.test:
            break
        # pan-down eligibility: the 75%-width column must clear the frame,
        # and the implied scroll speed must stay readable
        move = e["shot"]
        b = e["meta"][0]
        col_h = b["h"] * (W * PAN_W) / max(1, b["w"])
        if move == "pan-down" and (col_h <= H * 1.15
                                   or (col_h - H) / max(0.1, e["dur"]) > PAN_MAX_SPEED):
            move = "fit"
        per = e["dur"] / len(e["imgs"])
        for bi, img in enumerate(e["imgs"]):
            out = clips / f"seg_{n_seg:04d}.mp4"
            if not out.exists():
                render_segment(img, per, move if len(e["imgs"]) == 1 else
                               (move if move != "pan-down" else "fit"),
                               e["meta"][bi].get("focal_point"), out)
            n_seg += 1
    print(f"{n_seg} segments ready")

    seg_files = sorted(clips.glob("seg_*.mp4"))
    lst = work / "segments.txt"
    lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in seg_files),
                   encoding="utf-8")
    silent = work / "silent.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c", "copy", str(silent)])

    if not args.test:
        build_endcard(work / "endcard.png",
                      args.series_title or args.slug.replace("-", " ").upper())
        sh(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{ENDCARD_S}",
            "-i", str(work / "endcard.png"), "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-an", str(work / "endcard.mp4")])
        with open(lst, "a", encoding="utf-8") as f:
            f.write(f"file '{(work / 'endcard.mp4').resolve().as_posix()}'\n")
        sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
            "-c", "copy", str(work / "silent_full.mp4")])
        silent = work / "silent_full.mp4"

    # captions burn LAST so they sit on the final cut but never on the endcard;
    # the caption font is copied local so fontsdir stays a colon-free relative
    # path (drive-letter colons are a filtergraph-escaping trap)
    fonts = work / "fonts"
    fonts.mkdir(exist_ok=True)
    cap_font = fonts / "ariblk.ttf"
    if not cap_font.exists():
        cap_font.write_bytes(Path(f"{FONTS}/ariblk.ttf").read_bytes())
    build_ass(entries, timing, work / "captions.ass")
    sh(["ffmpeg", "-y", "-i", "silent_full.mp4" if not args.test else "silent.mp4",
        "-vf", "ass=captions.ass:fontsdir=fonts",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an",
        "silent_captions.mp4"], cwd=str(work))

    n_audio = args.test if args.test else len(entries)
    alst = work / "audio_list.txt"
    alst.write_text("".join(f"file '{Path(e['file']).resolve().as_posix()}'\n"
                            for e in entries[:n_audio]), encoding="utf-8")
    narr = work / "narration.m4a"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(alst),
        "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11,apad=pad_dur={ENDCARD_S}",
        "-c:a", "aac", "-b:a", "160k", str(narr)])

    final = Path(f"videos/{args.slug}/shorts/{args.short}.mp4")
    mux = ["ffmpeg", "-y", "-i", "silent_captions.mp4", "-i", "narration.m4a",
           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
           "-b:a", "192k"]
    if args.test:
        mux.append("-shortest")
    sh(mux + [str(final.resolve())], cwd=str(work))
    total = ffprobe_duration(final)
    print(json.dumps({"final": str(final), "duration_s": round(total, 2),
                      "audio_budget": timing["total_duration_s"], "segments": n_seg,
                      "endcard": not args.test}))


if __name__ == "__main__":
    main()
