# Operating Boulder Votes

How to run, extend, and publish the site. The public pages are generated; the database is the record.

## What this is

A sourced map of **City of Boulder** mayor and council races (plus city ballot measures). Older voters first: large type, one column, no JavaScript required.

Three zooms:

- **Year** = that year’s ballot (`2026.html`, `2025.html`, …). Home *is* the current ballot.
- **Person** = dossier across years (`people/<slug>.html`), with an issue × year grid.
- **Issue × year** = people on *that* ballot (`issues/<slug>-<year>.html`). Earlier answers from returning candidates are labelled as earlier.

A number or a “position” without a source is not published. Two quotes are never averaged. A dash means we do not have it.

Live: https://bouldervotes.org/ — GitHub Pages from `/docs` on `main`, custom domain `bouldervotes.org`.

## Rebuild

Python 3 stdlib only (plus the sqlite3 module). From the repo root:

```bash
python3 harvest_brl.py   # optional; hits BRL WP JSON, writes data/harvest/brl_questionnaires.json
python3 seed.py          # destroys and rebuilds data/bouldervotes.db
python3 build.py         # writes static HTML into docs/
```

`seed.py` is the whole load. It calls `ingest.py` (forums, measures, BRL harvest, Boulder Beat 2023 quiz). The SQLite file is gitignored; the harvest JSON is committed so a rebuild does not need the network.

GitHub Pages serves `docs/` from `main`. After a merge to `main`, Pages rebuilds in ~30s. This machine’s system resolver often cannot see `bouldervotes.org`; `dig` and `curl --resolve bouldervotes.org:443:185.199.108.153 https://bouldervotes.org/` are the check.

## Adding a fact

1. Put it in `seed.py` or `ingest.py`, hanging off a `sources` row.
2. Rebuild. Confirm it on the person page **and** the matching `issues/<slug>-<year>.html`.
3. If it is a new year, add the year to `YEARS` in `build.py` and to `how` / council `seats`.

Do not invent campaign URLs, attendance, or nos from silence. If only four people were named as endorsing a measure, store those four.

## Adding a questionnaire

Preferred: harvest into `data/harvest/` (see `harvest_brl.py`) then ingest. For a small yes/no sheet, a function in `ingest.py` is fine — `ingest_beat_2023` is the pattern.

Binary `stance` (`yes` / `no` / `mixed`) only when the source is actually binary. Long BRL answers stay `stance=NULL` with `verbatim` as published.

## Adding a forum

`events` + `event_appearances`. Attendance only when a published source named who showed. Link `recording_url` when a video exists. Spoken answers become `answers` with `kind=forum` and `event_id` set — they file onto issue pages, they do not lengthen the year page.

## Publishing

Work in a git worktree, not on `main`. Branch, commit, PR to `unforcedagi/bouldervotes.org`, merge when the Pages tree in `docs/` is the thing you want live.

Local git identity in this repo is `unforcedagi` / `unforcedagi@users.noreply.github.com`.

## What is parked

- 2026 Chamber forum recording — they said they would publish; wait.
- Vote411 / LWV 2026 questionnaire — when it opens.
- Campaign-finance line items (city clerk, not TRACER).
- 2019 and earlier cycles.
- Forum transcripts as quotes (videos are linked; do not invent spoken words from a journalist’s grouping).
