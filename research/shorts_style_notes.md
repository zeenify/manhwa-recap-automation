# SHORTS STYLE NOTES — research bible for the shorts pipeline

Researched 2026-10-06 (three parallel web-research passes: platform mechanics,
manhwa-niche formats, production craft). This file is LAW for the shorts
writer agent and the design reference for the shorts tools. Evidence tiers:
**[P]** platform-official, **[S]** peer-reviewed/large study, **[T]** third-party
analyst data (directional, platforms publish no weights), **[E]** observed real
account/video artifacts, **[G]** vendor/guide content, **[D]** derived for our
pipeline (no published standard exists).

Target material: **A Wimp's Strategy Guide** (completed, 20 chapters —
`scripts/a-wimps-strategy-guide/ch01–ch020`, beat PNGs + `beats.json` under
`assets/a-wimps-strategy-guide/ch*/beats/`, continuity memo at
`assets/a-wimps-strategy-guide/story-so-far-final.md`). Voice: the `default`
fish.audio voice. One short = one self-contained scene or small arc, 30–60s,
9:16 vertical 1080×1920, reusing existing beats. A short MAY pull beats from
multiple chapters. Unrestricted count: every short-able scene we find is a
short (research expects 40–80 units from 20 chapters).

---

## 1. Platform verdicts — what gets a short pushed

**YouTube Shorts (the priority surface — it compounds with our long-form).**
- Ranking is a seed-audience loop: a short is shown to viewers predicted to
  like it; "watched vs. swiped away" is the CTR-analog and the single most
  decisive signal; then Average % Viewed and engaged views carry quality.
  "The audience is the algorithm." (Todd Sherman, Shorts product lead) [P]
- Benchmarks to aim at: **viewed-vs-swiped ≥ 70%**, **avg % viewed ≥ 80%**
  (70% floor; 1M-view shorts average ~76%) [T]. Since Aug 24 2026 views count
  from the first frame — public view counts are a *reach* number; engaged
  views + avg % viewed are the health metrics. [P]
- **No length penalty** (up to 3 min since Oct 15 2024 [P]) but completion %
  drives distribution, so padding length = burial. 30–45s is the retention
  optimum for narrative. [T]
- Shorts = discovery layer: ~74% of Shorts views come from non-subscribers;
  combined Shorts+long-form channels grow ~40% faster — but the funnel is NOT
  automatic (an arXiv study found long-form views can *drop* after channels
  start Shorts). **Every short needs an explicit mechanical funnel** (see §4). [P/T/S]
- Policy armor matters: Jul 15 2025 YPP "inauthentic content" policy + Oct 1
  2026 originality ranking change target exactly "reused visuals + minimal
  transformation". **Our persona narration IS the transformation layer.** [P]

**TikTok (highest variance, fastest decay).** Completion + rewatch dominate
(analyst estimates: 40–50%+ of ranking weight; rewatch is the strongest single
signal — 15–20% replay rate = strong positive) [T]. Sub-30s videos average
~72% completion vs ~54% for 30–60s [T]. Shares & saves outweigh likes.
Pure interest graph — any short can cold-start, follower count is not a
direct factor [P]. Engagement bait = shadowban risk (2026 enforcement) [T].

**Instagram Reels.** Mosseri (Jan 2025): the three signals are **watch time,
likes per reach, and SENDS per reach** — DM shares drive 3–5× distribution
[P/T]. So: make clips people *send to a friend* (a shocking twist beat, not a
mid-scene recap). Suppresses watermarked/re-used content — native clean
uploads only. [P]

**Facebook Reels.** Older skew (Gen X 43% / Boomers+ 39% — the most-used
short-video platform for those cohorts) [T]; **85% watch muted** (Facebook
internal research — the origin of the famous stat), captions lift view time
~12% [T]. Discovery weakest of the four; treat as a free re-post surface.

## 2. The anatomy of a winning 30–60s narrative short

**The swipe window.** ~67% of viewers swipe away if not engaged within 3
seconds; survivors of the first 3s overwhelmingly stay (65% watch 10+s more)
[T]. A hook in the first 2 seconds retains ~19% more viewers [T]. **Deliver
the complete hook by 2.0–2.5s.** If 3-second retention sits below ~60% in
Studio, the hook wording is the variable — re-cut and re-test. [T]

**Hook formulas that survive the swipe** (rated for narrative content) [T]:
1. **Mid-action open** — start inside the most dramatic frame, context after.
   The natural fit for manhwa: open ON the humiliation / reveal / absurd panel.
2. **Contradiction / pattern interrupt** — "Everyone thinks he's F-rank. He's
   the one who killed the S-rank."
3. **Direct promise with a number** — "3 seconds of backstory explain his
   whole revenge."
4. **Specific curiosity question** — never self-identifying filler ("Want
   more?"); specific ("Why did she hand him the poison herself?").
5. **Reverse structure** — start at the payoff, then explain how we got there.
Combos (contradiction + promise) beat single devices.

**Niche hook generators** (from 23 observed real hooks, manhwa niche [E]) —
four cover ~90%: (a) **flat injustice statement** ("Kicked out for being
useless, his fiancée…"), (b) **withheld-knowledge gap** ("not knowing he…",
"doesn't know yet"), (c) **superlative claim** ("the most feared X in…"),
(d) **deadpan recontextualization** ("bro really said…"). All four are
*situational*, never *contextual*: **never open with the series name, chapter
number, or "in this manhwa."** First frame = the most extreme panel, narration
speaking at frame one, ZERO dead air at the top.

**Mid-clip pacing.** A visual change every **3–5s** (cut, zoom push-in, pan,
caption event); nothing static longer than ~12s [T]. A 30–45s short wants
**8–12 visual events**. Cheapest interrupts on static art: zoom punch-ins and
caption pops. Silence is the other bleed: dead air reads 2× longer in a feed
than in long-form; trim gaps hard. [T]

**Endings** (evidence-ranked):
1. **Seamless loop** for ≤30s punchline beats — last panel matches first
   panel + a verbal callback; replay = 2 views per impression and inflates
   exactly the ranked metrics. [T]
2. **Cliffhanger / open loop** for 45–60s arcs — cut right before the twist
   lands (or one line after, no resolution). Comment sections demanding Part 2
   are themselves engagement signal; niche data claims cliffhanger structures
   convert 3–5× better than complete-answer shorts [G]. YouTube shipped native
   Shorts series/seasons (Sept 2026) for episodic content [P].
3. **One organic question** tied to the story ("Would you have taken the
   deal?") earned ~44% more comments [T]. **Zero engagement bait** ("like if",
   "comment X") — demoted on FB since 2017 [P], guidelines risk on TikTok [T].
   Consensus: "loop for the algorithm, question for the humans."

**Length law for us:** one beat/scene per short. 30–45s default; 45–60s only
when the arc genuinely needs it AND ends on a cliffhanger; sub-20s only for
looping roast beats. **Never stretch narration to fill time — audio is the
clock (our existing convention holds).** Word budget at shorts pace
(~150–160 WPM ≈ 2.5 words/sec): **30s ≈ 75–85 words, 45s ≈ 110–120,
60s ≈ 150 max.**

## 3. The format menu (manhwa niche, observed 2024–2026)

Full taxonomy observed: POV panel scroll, face-slap arc, character spotlight,
roast commentary, two-part cliffhanger, ranking/countdown, wait-for-the-end
payoff, lore micro-essay, phonk hype edit, comic dub, rec listicle [E].
**Our core rotation of 5** (matches our assets + roast persona):

1. **Face-slap arc (40–55s)** — the niche workhorse [E]. Structure: flat
   injustice statement (0–2.5s) → roast-narrated buildup → the reversal gets
   the most screen time and the narration slows → hold/freeze on the
   humiliator's reaction panel as the payoff. Mine `beats.json` for
   humiliation-beat + reversal-beat pairs, ACROSS chapters freely. End: loop
   or organic question. Expect 5–15 self-contained face-slaps in a 20-ch
   series.
2. **Roast beat (12–30s)** — our persona's native format [E]. One absurd /
   over-serious panel + deadpan TTS roast; punchline = the narration; no CTA.
   Lowest cost, highest shareability. ALSO our fair-use armor: commentary-
   dense redistribution is the transformation that keeps recap content inside
   the line. Our scripts are full of these ("That's a scheduled funeral",
   "The produce did nothing to anyone" — ch010).
3. **Character spotlight (25–40s)** — superlative claim ("the most feared
   thing to crawl out of a summoning circle") → 3–6 iconic panels, one
   narration line each → end on a rating/argument question (comment fuel).
   For the wimps series: the barbarian, the mom, the wolfgod, the gunman.
4. **Countdown / ranking (45–60s)** — "Top 5 coldest moments in this story":
   5 numbered beats ~8–12s each, cut on beat, "#1" held longest, end "did
   yours make the list?" Fan-service for recap viewers, trailer for
   strangers. One completed series is exactly the right scope. [E]
5. **Two-part cliffhanger (2 × ~45s)** — reserve for the 3–5 BEST arcs only;
   cut at the reversal, Part 2 within 24h. Overuse teaches viewers to wait
   instead of follow. [E/G]

Optional low-cost extra: **phonk hype edit (10–25s, no narration)** for
#manhwaedit discovery — panels flash on beat hits. Music-first, zero script.

**Hook-line examples to imitate structurally** (real, [E]): "Kicked Out for
Being 'Useless', His Fiancée Cheated with the Hero" · "She was reborn to take
her revenge" · "He Doesn't Remember Her But They Have A Daughter" · "POV:
you're the villainess" · "Bro really said everything without saying a word
💀" · "These Top 5 Manhwa Moments Are Insane" · "Don't judge a book by its
cover". Pattern: situational, no series name, no chapter number.

## 4. The funnel (mechanical, on every short)

Shorts-acquired subs convert worse than organic ones — the funnel must be
built, not hoped for [T/S]. Niche conversion reality: ~1M Shorts views yields
only 0.05–0.5% subs [G]. The mechanics that actually convert:
- **Pinned comment on every short → the exact chapter long-form video** (we
  have one per chapter — a rare advantage; link the playlist for arcs).
- **End frame (last ~2s):** series name + "full recap on the channel".
- **CTA mid-short, not at the tail** (many viewers swipe before the end);
  30–85% watch muted, so on-screen text beats voice for CTAs.
- A **"watch in order" playlist** of all 20 recaps; channel trailer addressed
  to Shorts arrivals reportedly converts 2–4× better [G].
- Frame the funnel narratively: "this whole arc is chapters 9–11 — full recap
  on the channel."

## 5. Production specs (1080×1920, 30fps)

**Canvas & framing.** Blurred darkened copy fills the frame (existing card
pattern), sharp panel column 70–85% width centered — tall webtoon strips are
natively vertical and fill 9:16 far better than they ever filled 16:9. All
text + critical art inside the universal safe box: **x 100–980, y 240–1440**
(strictest-denominator of TikTok/Reels/Shorts UI overlays; Shorts' bottom
title bar is the biggest intruder at ~440px) [D from 2025–26 zone guides].

**Captions — mandatory, burned in.** 60–85% of the audience may be on mute;
the short must fully work sound-off (FB's 85%-muted stat; captions +12% view
time) [T]. House style: bold sans (Anton/Montserrat Black), white with thick
black stroke, **one keyword per card in yellow**, **2–4 words per card**
(sweet spot 3), ~60px, center-lower inside the safe box, card appears on or
just before its spoken word (word-level "karaoke" pop is the default that
wins) [S/G]. Also export an SRT for YouTube accessibility/SEO; disable
platform auto-captions where possible. [S]

**Voice.** ~150–160 WPM (~2.5 words/sec) — run the persona ~10–15% hotter
than long-form [M, convergent]. Punctuation is the pacing API (commas =
micro-breaths, ellipses = dramatic pauses). Kill dead air: **shorts TTS pad
0.15–0.25s, not the long-form 0.4s**; hook line starts within 1–2s of frame
one. Robotic-cheap TTS correlates with ~70% lower retention [M] — our fish
voice + roast writing is the mitigation; write FOR the voice.

**Music & SFX.** Voice normalized to **−14 LUFS**, true peak ≤ −1 dBTP;
music bed sits **18–25 LU under the voice** (static low bed — no sidechain
pumping in ffmpeg); judge in LUFS, never peak meters [S]. Genre by mood:
phonk/percussive = hype, low drone + riser = tension, sparse tactile stingers
= comedy. Whoosh INTO hard cuts, impact ON the landing; SFX on real scene
changes only. Licensed-safe sources only: YouTube Audio Library, Pixabay,
Uppbeat. NOTE: our long-form "no music" convention was an authoring decision
for constant narration; in shorts a quiet bed is standard practice and masks
TTS seams — **pending user decision** (see §8).

**Motion.** Pan-down speed: **100–200 px/s over dialogue-dense panels,
300–500 px/s over sparse action**; 2–4s minimum dwell per panel; ease-in/
ease-out on every move, never reverse mid-pan, no whip pans (cybersickness
guard) [D — no published px/s standard exists; tune]. A visual event every
3–5s; the blurred layer can carry the motion while the sharp panel stays
stable. Merged side-by-side only when heights are comparable (existing ≤1.6
ratio rule carries over). **No full-chapter title cards, no site junk, no
spillover bubbles — same beat rules as long-form; on Shorts a title card is
a swipe trigger.**

## 6. Cross-posting matrix (one master, native uploads)

| | YT Shorts | TikTok | IG Reels | FB Reels |
|---|---|---|---|---|
| Sweet spot | 30–45s (3min max) | 21–34s | ≤45s | ≤45s |
| Mute norm | sound-on culture | sound-on | mixed | **85% muted** |
| Text | title/desc keywords rule SEO | caption + spoken words indexed | keyword caption | keyword caption |
| Watermark | clean upload preferred | n/a (source) | **suppresses watermarked content (active 2025)** | same Meta originality scoring |
| Identical file? | OK | OK (native upload) | OK if clean | OK if clean |

Rules: ONE clean watermark-free 1080×1920 master per short; upload natively
to each platform; per-platform metadata (titles/captions/hashtags written per
platform, keywords in hook + caption + spoken audio); stagger post times.
Identical video files are fine — identical metadata is not. [S]

## 7. Copyright & policy armor (read before the first upload)

- **Enforcement is real in this exact niche:** manhwa recap channels have
  taken strikes, including from Naver Webtoon directly; 3 strikes = channel
  termination. Korean publishers intensified DMCA enforcement 2024–2025. [S]
- Fair-use disclaimers are legally meaningless; a panel-by-panel recap of a
  whole chapter fails the amount + market-effect factors. [S]
- **Our mitigations, in order:** (1) roast/commentary-forward narration —
  "lead with analysis, reaction or criticism, not a panel-by-panel readthrough"
  (niche guidance) — our persona is structurally compliant; (2) one moment or
  joke per short with dense commentary, never a compressed chapter substitute;
  (3) narration dominant over art screen time; (4) keep panel count per short
  low (3–8); (5) YouTube altered/synthetic-content disclosure for TTS.
- Log every takedown; a single rights-holder strike on Shorts = stop-everything.

## 8. What this means for OUR pipeline (design sketch)

**We already have** (no rebuild needed): beat PNGs per chapter with verified
boundaries (`assets/a-wimps-strategy-guide/ch*/beats/beat_NNNN.png` +
`beats.json` incl. aspect ratios), 20 locked scripts whose entries map 1:1 to
beats, the fish.audio TTS tool (idempotent, prosody presets), the assembler's
composed-card rendering logic, per-chapter long-form videos for the funnel,
and a completed-series continuity memo for context.

**What the shorts agent/pipeline adds:**
1. **Scene-miner agent** (`agents/shorts-miner-agent.md`) — reads all 20
   chapter scripts (+ the final story-so-far for character context), outputs
   `shorts/<slug>/scene_catalog.md` (or .json): one catalog entry per
   short-able unit — type (face-slap / roast / spotlight / countdown item /
   cliffhanger), title, hook line draft, covered beats with chapter+beat IDs,
   suggested duration, why it works. Unrestricted count.
2. **Shorts writer protocol** (`agents/shorts-writer-agent.md` + THIS file) —
   turns chosen catalog entries into short scripts: hook ≤2.5s, one-scene
   body, loop/cliffhanger ending, 75–150 words, no banned words (tone.md flow
   rule carries over — plus never open with series name/chapter number).
3. **Vertical assembler** (`tools/assemble_shorts.py`) — 1080×1920/30fps;
   per-short beat list from the script; pan/punch-in motion (§5 specs);
   burned-in caption cards (ffmpeg ASS, 2–4 words/card, keyword colored);
   TTS at shorts pad (0.2s) + optional licensed music bed ducked 18–25 LU;
   loop or end-frame last 2s; outputs `videos/<slug>/shorts/<NN>_<title>.mp4`.
   Idempotent per short; purge clips on setting changes (long-form gotcha
   applies).
4. **Publishing pack** — per short: pinned-comment text (chapter link), YT
   title/description, TikTok/IG/FB captions + tag sets, all in the script's
   metadata section (never spoken — `##`-header rule already guards TTS).

**Sequencing:** catalog first (mining pass over the 20 scripts), then batch
write + TTS + assemble 10–15 shorts in one production pass, publish 3–5/week
(conservative) or daily (aggressive). Measure ONLY: viewed-vs-swiped ≥70%,
avg % viewed ≥80%, and pinned-comment→long-form clicks. Shorts views are
volatile by design ("10k then flat" is the documented norm) — plan a
portfolio, not single hits. [T]

## 9. Open decisions (user must pick before the first render)

1. **Music bed in shorts?** Long-form convention says no music; shorts
   research says a quiet licensed bed (18–25 LU under voice) is standard and
   masks TTS seams; the hype-edit format is music-first. Recommendation: YES
   for shorts only, quiet bed, YT Audio Library/Pixabay sources.
2. **Caption style:** burned-in karaoke cards (recommended; needs the ASS
   caption renderer) vs. no captions for v1.
3. **Voice:** reuse the wimps series `default` voice as-is, or +5–7% speed
   preset for shorts tempo (research: ~10–15% hotter than long-form pace).
4. **Batch-1 size & cadence:** recommendation 10–15 shorts first batch,
   3–5/week publishing.
5. **Formats to greenlight for batch 1:** recommendation — face-slap arcs,
   roast beats, spotlights, one countdown; reserve two-part cliffhangers
   until the funnel (pinned comments, playlist) is in place.

## 10. Source index (condensed)

- **Platform official:** YouTube Help (3-min Shorts, engaged views),
  blog.youtube (Aug 2026 view redefinition), Todd Sherman Shorts Q&A, TikTok
  Newsroom recommendation post, Mosseri Reels statements (via Fanpage Karma /
  Hootsuite), Meta Reels unification (creators.facebook.com / MediaPost),
  YouTube "inauthentic content" policy (Jul 2025, via Subsub.io/Umbrella
  Creators), FB engagement-bait demotion.
- **Studies:** arXiv:2402.18208 (Shorts effect on long-form), cybersickness
  research (Brill/Healthline), NuVoodoo platform-by-age survey (Apr 2025).
- **Analyst/vendor data (directional):** OutlierKit, vidIQ, Lenostube,
  Shortimize, Opus Pro (hook formulas, pattern interrupts), Hootsuite (loops),
  HashMeta/FindMeCreators/Dataslayer (TikTok weights, completion benchmarks),
  fluxnote.io (Shorts-to-subs funnel, manhwa channel guides), recapmanga.com
  (fair-use posture), StratBoost, Zella (ducking dB), VirVid (TTS retention).
- **Observed niche artifacts [E]:** @manhw.panel, @baixy__, @wyful,
  @manhwanoid_, @barry..lyndon, @manwha_moments, @jay_yaj, BlackGlyph,
  Animation Lore, Perfect Secret Love part-serialized recaps, "Top 5 Manhwa
  Moments" shorts, manga-dub channel catalogs, Pippit/CapCut template
  ecosystems.

*Full verbatim briefs from the three research passes are preserved in the
session transcript; this file is the curated, actionable distillation.*
