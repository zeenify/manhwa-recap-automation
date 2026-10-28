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

Pipeline: frame-EXACT silent segments per entry (segment frame counts allocated
so each entry's video length equals its mp3 duration — no cumulative A/V skew)
→ concat (+ funnel endcard) → burn block captions as per-frame ASS events
(Akiel-Runes style: ONE big Rubik-Bold ALL-CAPS line dead-center; block births
anchored to real faster-whisper word onsets, clumped → letter-gaps ease open
with overshoot; subtle continuous vibration; no word karaoke) → mux narration
(loudnorm -14 LUFS, tail pad for the endcard).

Usage:
  py tools/assemble_shorts.py --slug a-wimps-strategy-guide --short 001_door_kick
  py tools/assemble_shorts.py --slug ... --short ... --test N   # first N entries, no endcard

Idempotent per segment clip — delete videos/<slug>/shorts/<short>/clips/ after
changing shots, beats, or timing; captions burn fresh on every run.
"""
import argparse
import json
import math
import random
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
CAP_FONT = "Rubik"   # rounded bold sans — the Akiel-Runes/CapCut-style caption look
CAP_SIZE = 96        # one big line, dead-center — measured chunks guarantee fit
CAP_MARGIN = 40      # side margin for the measured line budget (W - 2*margin)
CAP_FSP_TWEEN = (0.90, 1.10)  # letter-gap ratio: clumped birth -> settled width
CAP_POP_MS = 290     # birth pop: rise ~60% then decelerating settle (ease-out feel)
CAP_POP_OVERSHOOT = 1.12  # peak of the rise, fraction of the gap delta — springy
CAP_JITTER = 1.2     # px amplitude of the continuous caption vibration
DARK = (14, 14, 16)
FONTS = "C:/Windows/Fonts"
CAP_FONT_TTF = f"{FONTS}/Rubik-Bold.ttf"
if not Path(CAP_FONT_TTF).exists():  # machines without Rubik keep a clean bold look
    CAP_FONT, CAP_FONT_TTF = "Arial Black", f"{FONTS}/ariblk.ttf"

_WHISPER = None


def speech_spans(mp3: Path):
    """Real word start/end times via faster-whisper (local, CPU). Used ONLY to
    anchor block boundaries to actual speech onsets — never for per-word
    karaoke. Returns [(start, end), ...] or None (caller falls back to
    proportional timing). Model loads once per run."""
    global _WHISPER
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("captions: faster-whisper not installed — proportional block "
              "timing (install with: py -m pip install faster-whisper)", file=sys.stderr)
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
        q = f"clip(t/{dur:.4f},0,1)"
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


def render_segment(img: Path, frames: int, move: str, fp, out: Path):
    """frames-EXACT: -frames:v pins the segment length so an entry's segments
    sum to exactly round(entry_dur * FPS) — the anti-drift contract."""
    dur = frames / FPS
    vf = segment_filter(move, dur, fp)
    sh(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(img),
        "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264", "-preset",
        "veryfast", "-crf", "20", "-an", str(out)])


# ---------------------------------------------------------------- frames

def split_frames(total: int, n: int):
    """Balanced (Bresenham) split of an entry's exact frame count across its
    beats — sums back to `total`, so rounding can never accumulate."""
    if n <= 1:
        return [total]
    return [(i + 1) * total // n - i * total // n for i in range(n)]


# ---------------------------------------------------------------- captions

def word_weight(word: str) -> float:
    """Pronunciation-duration weight (syllable-ish chars + punctuation pause)
    — block timing weight for the proportional fallback."""
    w = len(re.sub(r"[^A-Za-z0-9']", "", word)) + 1.0
    if re.search(r"[.!?]$", word):
        w += 2.0
    elif re.search(r"[,;:]$", word):
        w += 1.0
    return w


_meas_font = None


def meas_font():
    global _meas_font
    if _meas_font is None:
        _meas_font = ImageFont.truetype(CAP_FONT_TTF, CAP_SIZE)
    return _meas_font


def line_wid(text) -> float:
    """Settled-state line width (PIL measure + 10% end tracking + libass fuzz)
    — a wrapped caption would break the one-line contract."""
    return meas_font().getlength(text) * CAP_FSP_TWEEN[1] * 1.03


def fsp_pair(text):
    """Clumped/settled \\fsp values for the birth pop."""
    natural = meas_font().getlength(text)
    gaps = max(1, len(text) - 1)
    lo, hi = CAP_FSP_TWEEN
    return (round((lo - 1.0) * natural / gaps, 2),
            round((hi - 1.0) * natural / gaps, 2))


def blockify(words):
    """Split narration into single-line caption blocks: greedily fill by
    measured width (uppercase, at settled tracking), prefer ending a block at
    sentence ends, and when a split must happen mid-sentence prefer the last
    comma/colon inside the line. Returns word-index ranges."""
    budget = W - 2 * CAP_MARGIN
    blocks, cur = [], []
    start = 0
    for i, w in enumerate(words):
        if cur and line_wid(" ".join(cur + [w])) > budget:
            cut = next((j for j in range(len(cur) - 2, 0, -1)
                        if re.search(r"[,;:]$", cur[j])), None)
            if cut is not None:
                blocks.append((start, start + cut))
                start += cut + 1
                cur = cur[cut + 1:] + [w]
            else:
                blocks.append((start, start + len(cur) - 1))
                start += len(cur)
                cur = [w]
        else:
            cur.append(w)
        if re.search(r"[.!?]$", w):
            blocks.append((start, start + len(cur) - 1))
            start += len(cur)
            cur = []
    if cur:
        blocks.append((start, start + len(cur) - 1))
    # safety: a comma-preferred leave-behind or a lone huge word can still sit
    # over budget — greedy-split those so no block ever needs a second line
    final = []
    for a, b in blocks:
        text = " ".join(words[a:b + 1])
        if b == a or line_wid(text) <= budget:
            final.append((a, b))
            continue
        c0 = a
        for j in range(a + 1, b + 1):
            if line_wid(" ".join(words[c0:j + 1])) > budget:
                final.append((c0, j - 1))
                c0 = j
        final.append((c0, b))
    return final


def ass_time(t: float) -> str:
    cs = max(0, int(round(t * 100)))
    return f"{cs // 360000:01d}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def pop_gap_frac(p: float) -> float:
    """Progress of the birth pop as fraction of the gap delta: fast ease-out
    rise that overshoots ~12% and settles back — never a hard stop."""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    rise, settle = 0.55, 0.45
    if p < rise:
        q = p / rise
        return CAP_POP_OVERSHOOT * (1.0 - (1.0 - q) ** 3)
    q = (p - rise) / settle
    e = 0.5 * (1.0 - math.cos(math.pi * q))
    return CAP_POP_OVERSHOOT + (1.0 - CAP_POP_OVERSHOOT) * e


def jitter_xy(t: float, seed: int):
    """Very subtle continuous vibration: two incommensurate sines per axis
    (~8-13 Hz), deterministic per block so re-renders are stable."""
    r = random.Random(seed * 7919 + 13)
    ph = [r.uniform(0, 2 * math.pi) for _ in range(4)]
    dx = CAP_JITTER * (0.6 * math.sin(2 * math.pi * 8.3 * t + ph[0])
                       + 0.4 * math.sin(2 * math.pi * 13.1 * t + ph[1]))
    dy = CAP_JITTER * (0.6 * math.sin(2 * math.pi * 9.7 * t + ph[2])
                       + 0.4 * math.sin(2 * math.pi * 12.3 * t + ph[3]))
    return dx, dy


def block_times(words, blocks, spans, dur, pad):
    """Video-relative (start, end) seconds per block, inside [0, dur]. Exact
    when whisper's word spans match the script word count (block birth = the
    block's real spoken onset); otherwise proportional across the real speech
    window. Blocks display contiguously; an entry's last block holds through
    its TTS tail pad so captions never blink between entries."""
    n = len(words)
    if spans is not None and len(spans) == n:
        times = []
        for bi, (a, b) in enumerate(blocks):
            start = spans[a][0]
            end = (spans[blocks[bi + 1][0]][0] if bi + 1 < len(blocks)
                   else spans[b][1] + 0.30)  # hold the tail pad (pad ~0.2)
            times.append((start, min(end, dur)))
        return times, "whisper"
    if spans is not None and len(spans) >= 2:
        lo, hi = spans[0][0], spans[-1][1]
        window = max(0.5, hi - lo)
    else:
        lo, hi = 0.0, max(0.5, dur - pad)
        window = hi - lo
    weights = [sum(word_weight(w) for w in words[a:b + 1]) for a, b in blocks]
    total = sum(weights)
    times, t = [], lo
    for bi, wt in enumerate(weights):
        start = t
        t += window * wt / total
        end = dur if bi == len(blocks) - 1 else t
        times.append((start, end))
    if spans is not None and len(spans) >= 2:
        return times, "speech-window"
    return times, "estimate"


def build_ass(entries, timing, out: Path):
    """Per-frame block captions, Akiel-Runes style. Each block emits one ASS
    event per video frame at a fixed dead-center anchor: fsp animates the
    letter-gap pop in Python (ease-out overshoot settle), a 1.2px sine
    vibration keeps the line barely alive, frame-0 alpha lands the birth
    near-solid. Block births come from real word onsets when whisper agrees
    with the script, else proportional timing across the measured speech
    window. One line per block, guaranteed by measured chunking."""
    pad = timing.get("pad_s", 0.0)
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
        "WrapStyle: 0\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,{CAP_FONT},{CAP_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,"
        f"&H00000000,-1,0,0,0,100,100,0,0,1,3,4,5,40,40,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n")
    pop_s = CAP_POP_MS / 1000.0
    lines, block_id = [], 0
    for ei, (e, tm) in enumerate(zip(entries, timing["entries"])):
        words = [w.upper() for w in e["narration"].split()]
        blocks = blockify(words)
        spans = speech_spans(Path(e["file"]))
        times, mode = block_times(words, blocks, spans, e["dur"], pad)
        v0 = e["vstart"] / FPS  # this entry's first frame on the video timeline
        for bi, ((a, b), (ts, te)) in enumerate(zip(blocks, times)):
            text = " ".join(words[a:b + 1])
            if line_wid(text) > (W - 2 * CAP_MARGIN):
                print(f"captions WARNING: block over one-line budget, "
                      f"libass may wrap: {text!r}", file=sys.stderr)
            fsp_lo, fsp_hi = fsp_pair(text)
            birth, dead = v0 + ts, v0 + te
            f0 = max(0, math.ceil(birth * FPS - 1e-6))
            f1 = math.ceil(dead * FPS - 1e-6)
            for f in range(f0, f1):
                ft = f / FPS
                p = (ft - birth) / pop_s
                fsp = fsp_lo + (fsp_hi - fsp_lo) * pop_gap_frac(p)
                jx, jy = jitter_xy(ft, block_id)
                alpha = "&H60&" if f == f0 else "&H00&"
                lines.append(
                    f"Dialogue: 0,{ass_time(ft)},{ass_time(min((f + 1) / FPS, dead))},Cap,"
                    f",0,0,0,,{{\\pos({540 + jx:.1f},{960 + jy:.1f})\\fsp{fsp:.2f}"
                    f"\\blur1.5\\alpha{alpha}}}{text}")
            block_id += 1
        print(f"captions entry '{e['title']}': {len(blocks)} blocks, {mode} timing, "
              f"video start {v0:.2f}s")
    out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"captions: {block_id} blocks as {len(lines)} per-frame events")


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

    # video frame allocation: each entry renders round(dur*FPS) frames split
    # across its segments — captions and audio can never drift apart
    vstart = 0
    for e in entries:
        e["seg_frames"] = split_frames(round(e["dur"] * FPS), len(e["imgs"]))
        e["n_frames"] = sum(e["seg_frames"])
        e["vstart"] = vstart
        vstart += e["n_frames"]

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
        for bi, img in enumerate(e["imgs"]):
            out = clips / f"seg_{n_seg:04d}.mp4"
            if not out.exists():
                render_segment(img, e["seg_frames"][bi],
                               move if len(e["imgs"]) == 1 else
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
    cap_font = fonts / Path(CAP_FONT_TTF).name
    if not cap_font.exists():
        cap_font.write_bytes(Path(CAP_FONT_TTF).read_bytes())
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
