# Changelog

Every user-visible change gets a numbered update folder. The number is just
the chronological order of updates (like the shorts numbering) — NOT a
software version; small changes get small entries, big rebuilds get big ones,
and related same-day iterations stay inside ONE entry listed as commits.
Newest first.

Format modeled on the
[pokeemerald-expansion](https://github.com/rh-hideout/pokeemerald-expansion)
release notes: emoji domain sections, each holding `### Added / Changed /
Fixed / Removed`, one imperative line per change, code identifiers in
backticks, and the originating commit per section.

| Update | Date | Pipeline | Title |
| --- | --- | --- | --- |
| [002](002-shorts-captions/update.md) | 2026-10-28 | Shorts captions | Shorts captions rebuild — one-line center blocks, Akiel-Runes style |
| [001](001-film-lane/update.md) | 2026-10-17 | Film lane | Film lane ("arc film" format, inspired by Leo's Manhwa) |

## Adding an entry

1. Create the folder: `changelog/NNN-short-kebab-name/` — the next free
   number in merge order (014, 015, …), short kebab name.
2. Write `update.md` inside it:
   - `# UPDATE NNN — <title>`, then `**Date:**`, `**Scope:**` (exact
     files/pipelines touched), `**Commits:**` (hashes, oldest first; several
     same-day passes all belong to the same entry — either on this line or
     inline at each domain bullet).
   - One `## <emoji> Domain <emoji>` section per touched area (e.g.
     `## 🎬 Shorts renderer 🎬`, `## 🔍 Research 🔍`, `## 📜 House docs 📜`).
   - Under each domain: `### Added` / `### Changed` / `### Fixed` /
     `### Removed` — one imperative bullet per change (`Add …`, `Fix …`,
     `Replace …`), functions/files in backticks, *why* on the line for
     non-obvious changes.
   - Optional `## 🧪 Verification 🧪` — how the change was proven (renders,
     probes, frame strips), with relative links into `media/`.
3. Bundle evidence: screenshots/notes that deserve to survive go into
   `changelog/NNN-.../media/` with descriptive names (never `tmp/` — it is
   scratch and gitignored).
4. Add the row to the table above (newest first).
5. Commit the folder and the index row in one commit.
