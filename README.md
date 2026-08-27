# Boulder Votes

A sourced map of City of Boulder municipal elections — who is running, what they have said, which forums they showed up for, and where the underlying record lives.

**Audience, first:** older voters who want to read, not decode a dashboard. Large type, one column, citations on every number.

**Store, first:** SQLite. Cloudflare D1 is a later lift of the same schema, not a rewrite.

This is a prototype. It does not endorse anyone.

## Run it

Live: https://bouldervotes.org/ (GitHub Pages; custom domain). Mirror: https://unforcedagi.github.io/bouldervotes.org/

```bash
cd ~/REPOS/bouldervotes.org
python3 harvest_brl.py   # optional; writes data/harvest/brl_questionnaires.json
python3 seed.py          # rebuilds data/bouldervotes.db from schema + seed + harvest
python3 build.py         # writes static HTML to docs/ (GitHub Pages)
open docs/index.html
```

Python 3 stdlib only. No npm, no framework.

## What’s in the database

- People who ran or held office 2023–2026 (city mayor + council)
- Certified 2026 field (clerk list retrieved 2026-08-26)
- Certified 2023 mayor RCV + council (including the recount)
- Certified 2025 council totals
- Sitting/departed officeholders
- A first source catalog (clerk, county, BRL, Daily Camera, Chamber, LWV)
- BRL written questionnaires: all 14 candidates × 6 questions (2023) and all 11 × 6 (2025)
- Forum calendar for 2023 and 2025 (Chamber, PLAN, Progressives, LWV, VOTES!) with recordings where they exist
- City ballot measures: 2023 (2A, 2B, 302), 2025 (2A/2B CCRS, passed), 2026 referred bond / vacancy tax / two charter changes; DDA not referred
- One 2026 harvested spoken question (FAA airport grants at the June 6 caucus)

What’s *not* in it: invented positions, campaign-finance line items, most 2026 campaign sites, the 2026 Chamber recording (parked until they publish), county/BVSD races.

## Schema idea

This is an **evidence graph**, not a brochure.

`people` persist across years. `candidacies` hang on a `race`. `answers` always point at a `source`. Results keep RCV rounds. If we cannot cite it, it does not go on a page.

`schema.sql` is written so the same tables can move to D1.

## Editorial line

Quotes and reported stances stay attached to the journalist or the candidate’s own words. We do not collapse someone into a housing-score. If we later add a comparison UI, it will be “here is the question, here is each answer, here is the link.”
