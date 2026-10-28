# Changelog

Release docs in the pokeemerald-expansion `docs/changelogs` style: one folder
per minor version line (`1.0.x/`), one `.md` per release named by its version
(`1.0.1.md`), plus `template.md` — the skeleton every release copies. Each
release doc opens with a fenced "How to update" block, then emoji domain
sections (`Added / Changed / Fixed`), one imperative line per change, code
identifiers in backticks; empty domains are deleted, kept-but-unused sections
hold a `* N/A`.

| Line | Releases (newest first) |
| --- | --- |
| 1.0.x | [1.0.1 — Shorts captions rebuild](1.0.x/1.0.1.md) · [1.0.0 — Film lane](1.0.x/1.0.0.md) |

## Releasing a change

1. New doc: copy `template.md` to the current line folder as the next version
   (`1.0.x/1.0.2.md` — bump the patch per release; start a new line folder
   (`1.1.x/`) for a feature-era batch; the user decides when to cut).
2. Convert to a doc: the patch note lives at `changelog/<line>/<ver>.md`;
   several same-day passes are one release (list their commits in the Full
   Changelog footer range).
3. Fill the domains the release touched, one imperative bullet per change
   (`Add …`, `Fix …`, `Replace …`), *why* on the line for non-obvious
   changes, commit/compare hash at the bottom ("Full Changelog" compare of
   `prev...this`).
4. Evidence worth keeping: `changelog/<line>/media/` with descriptive names —
   image files are gitignored repo-wide EXCEPT under `changelog/` (see
   `.gitignore`); link them from a `## 🧶 Bundled media 🧶` section. Never
   reference `tmp/` — it is scratch.
5. Delete the untouched domain sections (or leave their `* N/A`), add the
   release row to the table above, and commit the doc + index together.
