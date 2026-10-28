# Changelog

Versioned bundles — one folder per version, pokeemerald-expansion release
style. A version folder (`changelog/vN/`) groups every change shipped in that
version: one doc per change, evidence bundled in its `media/`, and each doc
formatted like their release notes (emoji domain sections, `### Added /
Changed / Fixed / Removed`, one imperative line per change, commit hash).
Newest version first.

| Version | Dates | Bundled changes |
| --- | --- | --- |
| **v1** | 2026-10-17 → 2026-10-28 | [Film lane](v1/film-lane.md) ("arc film" format) · [Shorts captions rebuild](v1/shorts-captions.md) (one-line center blocks, Akiel-Runes style) |

## Adding a change / cutting a version

- **New change** (even a small one): drop a doc into the *current* (highest)
  version folder — `changelog/vN/<change-name>.md`, short kebab name. Its
  doc carries only that change.
- **Doc recipe**: title + `**Bundle:** vN` + `**Date:**` + `**Scope:**` (exact
  files/pipelines touched) + `**Commits:**` (hashes, oldest first; several
  same-day passes belong to the same doc, listed inline). Then `## <emoji>
  Domain <emoji>` sections per touched area, each with `### Added / Changed /
  Fixed / Removed` — one imperative bullet per change (`Add …`, `Fix …`,
  `Replace …`), functions/files in backticks, *why* on the line for
  non-obvious changes. Optional `## 🧪 Verification 🧪` with relative links
  into `media/`.
- **Evidence** that should survive goes into `changelog/vN/media/` with
  descriptive names — image files are gitignored repo-wide EXCEPT under
  `changelog/` (see `.gitignore` exception). Never reference `tmp/` in a
  changelog doc; tmp is scratch.
- **Cut a version**: when the batch of changes since the last bundle is
  worth naming as a unit (a rework, a feature sweep, a release to the
  channel), create the next `changelog/vN+1/` folder and start filing new
  changes there. The user decides when to cut.
- Update the index table above (newest version first, newest change first
  within a bundle) in the same commit as the change.
