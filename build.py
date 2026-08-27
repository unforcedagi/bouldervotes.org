#!/usr/bin/env python3
"""Render a static, large-type prototype from data/bouldervotes.db into site/."""
from __future__ import annotations

import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "bouldervotes.db"
OUT = ROOT / "docs"  # GitHub Pages serves /docs from main

CSS = """
:root {
  --paper: #f6f0e4;
  --ink: #1c1916;
  --muted: #5c5348;
  --rule: #d4c7b0;
  --link: #1f4b73;
  --link-visited: #5a3d6e;
  --mark: #8b2e1a;
  --won: #215c3a;
}
* { box-sizing: border-box; }
html { font-size: 20px; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  line-height: 1.55;
}
header, main, footer { max-width: 46rem; margin: 0 auto; padding: 0 1.25rem; }
header { padding-top: 1.5rem; padding-bottom: 0.75rem; border-bottom: 2px solid var(--ink); margin-bottom: 1.5rem; max-width: 46rem; }
.brand { font-size: 1.35rem; font-weight: 700; letter-spacing: 0.01em; text-decoration: none; color: var(--ink); }
.tagline { color: var(--muted); font-size: 0.95rem; margin: 0.25rem 0 0.75rem; }
nav { display: flex; flex-wrap: wrap; gap: 0.75rem 1.1rem; font-size: 0.95rem; }
nav a { color: var(--link); }
h1 { font-size: 1.8rem; line-height: 1.2; margin: 0 0 0.75rem; }
h2 { font-size: 1.25rem; margin: 1.75rem 0 0.5rem; }
h3 { font-size: 1.05rem; margin: 1.2rem 0 0.35rem; }
p, li { max-width: 42rem; }
a { color: var(--link); }
a:visited { color: var(--link-visited); }
.lede { font-size: 1.1rem; }
.note { color: var(--muted); font-size: 0.95rem; }
table { width: 100%; border-collapse: collapse; font-size: 0.95rem; margin: 0.75rem 0 1.25rem; }
th, td { text-align: left; padding: 0.4rem 0.5rem 0.4rem 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font-weight: 600; }
.num { font-variant-numeric: tabular-nums; text-align: right; }
.won { color: var(--won); font-weight: 600; }
.badge { display: inline-block; font-size: 0.75rem; letter-spacing: 0.03em; text-transform: uppercase; border: 1px solid var(--ink); padding: 0.05rem 0.4rem; margin-right: 0.3rem; }
.badge.match { border-color: var(--mark); color: var(--mark); }
.badge.inc { border-color: var(--won); color: var(--won); }
ul.plain { padding-left: 1.1rem; }
footer { margin: 3rem auto 2rem; padding-top: 1rem; border-top: 1px solid var(--rule); color: var(--muted); font-size: 0.9rem; }
.cite { font-size: 0.9rem; }
@media (max-width: 640px) {
  html { font-size: 18px; }
  table { font-size: 0.9rem; }
}
@media print {
  nav { display: none; }
  a { color: inherit; text-decoration: none; }
}
"""


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s))


def page(title: str, body: str, crumb: str | None = None) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Boulder Votes</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <a class="brand" href="index.html">Boulder Votes</a>
  <p class="tagline">A map of who is running, what they have said, and where that information lives.</p>
  <nav>
    <a href="index.html">Home</a>
    <a href="2026-mayor.html">2026 mayor</a>
    <a href="2026-council.html">2026 council</a>
    <a href="2025.html">2025</a>
    <a href="2023.html">2023</a>
    <a href="forums.html">Forums</a>
    <a href="sources.html">Sources</a>
    <a href="about.html">About</a>
  </nav>
</header>
<main>
{body}
</main>
<footer>
  Prototype. Every number on this site is cited. We do not endorse candidates.
  City of Boulder only — not county, school board, or state races.
</footer>
</body>
</html>
"""


def person_href(slug: str) -> str:
    return f"people/{slug}.html"


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = con.execute

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "people").mkdir(exist_ok=True)

    # ----- home -----
    mayor_n = q("SELECT COUNT(*) FROM candidacies WHERE race_id = (SELECT r.id FROM races r JOIN elections e ON e.id=r.election_id JOIN offices o ON o.id=r.office_id WHERE e.year=2026 AND o.slug='mayor')").fetchone()[0]
    council_n = q("SELECT COUNT(*) FROM candidacies WHERE race_id = (SELECT r.id FROM races r JOIN elections e ON e.id=r.election_id JOIN offices o ON o.id=r.office_id WHERE e.year=2026 AND o.slug='council')").fetchone()[0]
    src_n = q("SELECT COUNT(*) FROM sources").fetchone()[0]

    home = f"""
    <h1>Boulder’s 2026 city election, in one place</h1>
    <p class="lede">On November 3, 2026, Boulder voters will elect a mayor (ranked-choice) and five city council members (plurality, at-large). This site is a first map of the candidates, the last two cycles, the forums, and the newsrooms that actually hold the record.</p>
    <p>Right now the database has <strong>{mayor_n} mayoral candidates</strong> and <strong>{council_n} council candidates</strong> certified for 2026, plus the full certified fields and results for 2023 and 2025, and {src_n} source records. Candidate beliefs are <em>not</em> invented here — they are attached to a source, or they are absent.</p>
    <h2>Start here</h2>
    <ul class="plain">
      <li><a href="2026-mayor.html">2026 mayor</a> — six certified candidates, ranked-choice.</li>
      <li><a href="2026-council.html">2026 city council</a> — thirteen candidates, five seats, including the vacant Wallach seat.</li>
      <li><a href="2025.html">How 2025 went</a> — four seats, eleven candidates, certified totals.</li>
      <li><a href="2023.html">How 2023 went</a> — first RCV mayor; council recount for the fourth seat.</li>
      <li><a href="forums.html">Forums</a> — Chamber (Aug 26, 2026) and the June Raucous Caucus so far.</li>
    </ul>
    <h2>Why five council seats this year</h2>
    <p>Four seats were already up (the 2023 class). Mark Wallach, reelected in 2025, resigned on July 23, 2026 after the 8–1 vote to pursue FAA grants for the municipal airport. Because he resigned before August 1, the charter puts that seat on the November ballot rather than filling it by appointment. Combined with Taishya Adams running for mayor instead of her council seat, this is a large reset: a majority of the dais is in play.</p>
    <p class="cite">Sources: <a href="https://www.axios.com/local/boulder/2026/07/24/boulder-city-council-mark-wallach-resigns">Axios, July 24 2026</a>; city clerk candidate list.</p>
    """
    (OUT / "index.html").write_text(page("Home", home), encoding="utf-8")

    def race_id(year: int, office: str) -> int:
        return q(
            """SELECT r.id FROM races r
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE e.year=? AND o.slug=?""",
            (year, office),
        ).fetchone()[0]

    def candidates_for(race: int):
        return q(
            """SELECT c.id AS candidacy_id, p.slug, p.full_name, c.status, c.is_incumbent,
                      c.certified_on, c.matching_funds, c.campaign_url, c.notes
               FROM candidacies c JOIN people p ON p.id=c.person_id
               WHERE c.race_id=?
               ORDER BY p.sort_name""",
            (race,),
        ).fetchall()

    def cand_table(rows, include_cert: bool = False) -> str:
        head = "<tr><th>Candidate</th><th></th>"
        if include_cert:
            head += "<th>Certified</th>"
        head += "</tr>"
        body = []
        for r in rows:
            flags = []
            if r["is_incumbent"]:
                flags.append('<span class="badge inc">incumbent</span>')
            if r["matching_funds"]:
                flags.append('<span class="badge match">matching funds</span>')
            name = f'<a href="{esc(person_href(r["slug"]))}">{esc(r["full_name"])}</a>'
            if r["campaign_url"]:
                name += f' · <a href="{esc(r["campaign_url"])}">campaign site</a>'
            row = f"<tr><td>{name}</td><td>{''.join(flags)}</td>"
            if include_cert:
                row += f"<td>{esc(r['certified_on'] or '')}</td>"
            row += "</tr>"
            body.append(row)
        return f"<table>{head}{''.join(body)}</table>"

    # ----- 2026 mayor -----
    r_m = race_id(2026, "mayor")
    mayor_body = f"""
    <h1>2026 mayor</h1>
    <p>One seat. Ranked-choice voting — the second time Boulder has used it for mayor. Election day is Tuesday, November 3, 2026. Official ballot order was drawn by lot on August 25.</p>
    <p>Voters mark candidates in order of preference. If no one has a majority of first-choice rankings, the last-place candidate is eliminated and those ballots move to the next choice, until someone crosses 50%.</p>
    {cand_table(candidates_for(r_m), include_cert=True)}
    <p class="cite">Candidate list and matching-funds flags: <a href="https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates">City of Boulder clerk, retrieved Aug 26 2026</a>. RCV explainer: <a href="https://bouldercolorado.gov/guide/ranked-choice-voting-guide">city RCV guide</a>.</p>
    <p class="note">Aaron Brockett is the sitting mayor. Taishya Adams is a sitting councilmember; running for mayor means she is not running to keep her council seat.</p>
    """
    (OUT / "2026-mayor.html").write_text(page("2026 mayor", mayor_body), encoding="utf-8")

    # ----- 2026 council -----
    r_c = race_id(2026, "council")
    council_body = f"""
    <h1>2026 city council</h1>
    <p>Five at-large seats. Simple plurality: the five candidates with the most votes win. Ranked-choice voting does <em>not</em> apply to council.</p>
    {cand_table(candidates_for(r_c), include_cert=True)}
    <p class="cite">Official list: <a href="https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates">City of Boulder clerk</a>.</p>
    <h2>Incumbents on this ballot</h2>
    <p>Tara Winer (mayor pro tem), Tina Marquis, and Ryan Schuchard. The other two seats are open: Taishya Adams’s (she is running for mayor) and Mark Wallach’s (resigned July 23, 2026).</p>
    <p>Councilmembers not on this ballot, terms through 2028: Matt Benjamin, Nicole Speer, Rob Kaplan.</p>
    """
    (OUT / "2026-council.html").write_text(page("2026 city council", council_body), encoding="utf-8")

    def results_table(year: int, office: str) -> str:
        rid = race_id(year, office)
        rows = q(
            """SELECT p.full_name, p.slug, c.is_incumbent, res.round, res.votes, res.vote_share,
                      res.place, res.elected, res.notes
               FROM results res
               JOIN candidacies c ON c.id=res.candidacy_id
               JOIN people p ON p.id=c.person_id
               WHERE c.race_id=?
               ORDER BY res.round, res.place, res.votes DESC""",
            (rid,),
        ).fetchall()
        # group by round if RCV
        rounds = sorted({r["round"] for r in rows})
        chunks = []
        for rnd in rounds:
            subset = [r for r in rows if r["round"] == rnd]
            label = f"Round {rnd}" if len(rounds) > 1 else "Results"
            chunks.append(f"<h3>{label}</h3>")
            body = ["<tr><th>Place</th><th>Candidate</th><th class='num'>Votes</th><th class='num'>Share</th></tr>"]
            for r in subset:
                share = f"{r['vote_share']:.2f}%" if r["vote_share"] is not None else "—"
                cls = "won" if r["elected"] else ""
                won = " (elected)" if r["elected"] else ""
                body.append(
                    f"<tr class='{cls}'><td class='num'>{r['place'] or ''}</td>"
                    f"<td><a href='{esc(person_href(r['slug']))}'>{esc(r['full_name'])}</a>{won}</td>"
                    f"<td class='num'>{r['votes']:,}</td><td class='num'>{share}</td></tr>"
                )
            chunks.append(f"<table>{''.join(body)}</table>")
        return "\n".join(chunks)

    y2025 = f"""
    <h1>2025 city council</h1>
    <p>November 4, 2025. Four at-large seats, eleven candidates, plurality. No mayoral race. Last odd-year municipal election; winners serve three-year terms as the city moves to even years.</p>
    {results_table(2025, "council")}
    <p class="cite">Totals: Boulder County Clarity ENR, last updated Nov 26 2025. Top four match the certified figures read at the Dec 4 2025 seating (<a href="https://www.dailycamera.com/2025/12/05/new-boulder-city-council-sworn-in-2/">Daily Camera</a>).</p>
    <p>Lauren Folkerts, then mayor pro tem, finished sixth and left the council. Rob Kaplan, a former Boulder Rural Fire-Rescue captain, took the open-ish fourth seat. Boulder Reporting Lab asked all eleven candidates the same six questions — housing, homelessness, wildfire, foreign affairs, budget — and published every answer. That questionnaire is the best existing structured comparison we have; it is catalogued, not yet ingested answer-by-answer.</p>
    <p class="cite"><a href="https://boulderreportinglab.org/2025/10/05/boulder-2025-voter-guide-what-to-know-before-election-day-nov-4/">BRL 2025 voter guide</a>.</p>
    """
    (OUT / "2025.html").write_text(page("2025 election", y2025), encoding="utf-8")

    y2023 = f"""
    <h1>2023 mayor and city council</h1>
    <p>November 7, 2023. First direct election of the mayor, using ranked-choice voting. Four council seats. City ballots counted: 34,249. Active city voters: 68,812.</p>
    <h2>Mayor (ranked choice)</h2>
    <p>Bob Yates led on first-choice rankings. After Nicole Speer and Paul Tweedlie were eliminated, enough of Speer’s second choices moved to Aaron Brockett that Brockett won the final round 16,823–15,592.</p>
    {results_table(2023, "mayor")}
    <p class="cite">Official RCV summary of votes, Boulder County Clerk.</p>
    <h2>City council (plurality, four seats)</h2>
    <p>Ryan Schuchard won the fourth seat by 46 votes over Terri Brncic after an automatic recount (Dec 5–6, 2023) — the first council recount in years. Certified totals below.</p>
    {results_table(2023, "council")}
    <p class="cite"><a href="https://assets.bouldercounty.gov/wp-content/uploads/2023/12/2023C-Boulder-County-Official-Summary-of-Votes-Recount.pdf">Amended official summary of votes (recount)</a>; <a href="https://bouldercounty.gov/elections/by-year/2023-election/">county 2023 election page</a>.</p>
    """
    (OUT / "2023.html").write_text(page("2023 election", y2023), encoding="utf-8")

    events = q(
        """SELECT e.*, o.name AS host
           FROM events e LEFT JOIN organizations o ON o.id=e.host_org_id
           ORDER BY e.starts_on DESC"""
    ).fetchall()
    ev_html = ["<h1>Forums and appearances</h1>",
               "<p>This is a thin calendar on purpose. The Chamber forum on August 26, 2026 is the season-opener; the rest of the two-month run is not yet mapped. If you have a flyer, a recording, or a host contact, that is the highest-leverage thing to add next.</p>"]
    for e in events:
        ev_html.append(f"<h2>{esc(e['name'])}</h2>")
        ev_html.append(f"<p>{esc(e['starts_on'])} · {esc(e['venue'] or 'venue not recorded')} · hosted by {esc(e['host'] or 'unknown')}</p>")
        if e["notes"]:
            ev_html.append(f"<p>{esc(e['notes'])}</p>")
        apps = q(
            """SELECT p.full_name, p.slug, a.attended
               FROM event_appearances a JOIN people p ON p.id=a.person_id
               WHERE a.event_id=? ORDER BY p.sort_name""",
            (e["id"],),
        ).fetchall()
        if apps:
            ev_html.append("<ul class='plain'>")
            for a in apps:
                flag = "attended" if a["attended"] == 1 else "did not attend" if a["attended"] == 0 else "unknown"
                ev_html.append(f"<li><a href='{esc(person_href(a['slug']))}'>{esc(a['full_name'])}</a> — {flag}</li>")
            ev_html.append("</ul>")
    (OUT / "forums.html").write_text(page("Forums", "\n".join(ev_html)), encoding="utf-8")

    sources = q(
        """SELECT s.*, o.name AS org
           FROM sources s LEFT JOIN organizations o ON o.id=s.org_id
           ORDER BY s.year DESC, s.published_on DESC, s.title"""
    ).fetchall()
    src_rows = ["<tr><th>Year</th><th>Kind</th><th>Source</th></tr>"]
    for s in sources:
        label = s["title"]
        src_rows.append(
            f"<tr><td>{s['year'] or ''}</td><td>{esc(s['kind'])}</td>"
            f"<td><a href='{esc(s['url'])}'>{esc(label)}</a>"
            f"<div class='note'>{esc(s['org'] or '')}{(' — ' + s['notes']) if s['notes'] else ''}</div></td></tr>"
        )
    src_body = f"""
    <h1>Where this information lives</h1>
    <p>The useful record is scattered across the city clerk, the county clerk, two or three newsrooms, advocacy groups that host forums, and the candidates themselves. This page is the catalog we are filling. Harvest priority is the official list, certified results, then questionnaires (BRL, Vote411), then forum recordings, then campaign sites.</p>
    <table>{''.join(src_rows)}</table>
    """
    (OUT / "sources.html").write_text(page("Sources", src_body), encoding="utf-8")

    about = """
    <h1>About this prototype</h1>
    <p>Boulder Votes is being built as a public-interest map of City of Boulder elections, starting with 2023, 2025, and the 2026 cycle now underway. The first store is a SQLite database. The first website is generated from that database. Nothing here is an endorsement.</p>
    <h2>Rules of the data</h2>
    <ul class="plain">
      <li>A number without a source is not published.</li>
      <li>A “position” is a quote or a journalist’s reported grouping, hanging off a source — not our summary of a person’s soul.</li>
      <li>Incumbency, matching funds, and certified-on dates come from the city clerk list unless noted.</li>
      <li>Older voters are the first audience: large type, one column, print-friendly, no motion.</li>
    </ul>
    <h2>What is not here yet</h2>
    <ul class="plain">
      <li>Full BRL 2025 questionnaire answers (catalogued, not ingested).</li>
      <li>Campaign finance line items (the city has a filings page; TRACER is state-level and does not cover this race).</li>
      <li>The rest of the 2026 forum season.</li>
      <li>Most campaign websites.</li>
      <li>Ballot measures, BVSD, county races.</li>
      <li>Any social layer — ratings, comments, AT Proto. That is later, on purpose.</li>
    </ul>
    <p>Live: <a href="https://unforcedagi.github.io/bouldervotes.org/">unforcedagi.github.io/bouldervotes.org</a>. Local path: <code>~/REPOS/bouldervotes.org</code>. Rebuild with <code>python3 seed.py && python3 build.py</code>.</p>
    """
    (OUT / "about.html").write_text(page("About", about), encoding="utf-8")

    # ----- person pages -----
    people = q("SELECT * FROM people ORDER BY sort_name").fetchall()
    for p in people:
        cands = q(
            """SELECT c.*, e.year, o.name AS office, o.slug AS office_slug, r.voting_method, r.seats_open
               FROM candidacies c
               JOIN races r ON r.id=c.race_id
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE c.person_id=?
               ORDER BY e.year DESC""",
            (p["id"],),
        ).fetchall()
        answers = q(
            """SELECT a.*, q.prompt, s.title AS source_title, s.url AS source_url
               FROM answers a
               JOIN questions q ON q.id=a.question_id
               JOIN sources s ON s.id=a.source_id
               WHERE a.person_id=?""",
            (p["id"],),
        ).fetchall()
        holders = q(
            """SELECT * FROM officeholders WHERE person_id=? ORDER BY term_start""",
            (p["id"],),
        ).fetchall()

        bits = [f"<h1>{esc(p['full_name'])}</h1>"]
        if p["notes"]:
            bits.append(f"<p>{esc(p['notes'])}</p>")
        if holders:
            bits.append("<h2>Office</h2><ul class='plain'>")
            for h in holders:
                end = h["term_end"] or "current"
                extra = f" — {h['how_ended']}" if h["how_ended"] else ""
                bits.append(f"<li>{esc(h['role'])}: {esc(h['term_start'])} to {esc(end)}{esc(extra)}</li>")
            bits.append("</ul>")
        if cands:
            bits.append("<h2>Campaigns</h2><ul class='plain'>")
            for c in cands:
                flags = []
                if c["is_incumbent"]:
                    flags.append("incumbent")
                if c["matching_funds"]:
                    flags.append("matching funds")
                extra = f" ({', '.join(flags)})" if flags else ""
                site = f' · <a href="{esc(c["campaign_url"])}">campaign site</a>' if c["campaign_url"] else ""
                bits.append(
                    f"<li>{c['year']} {esc(c['office'])} — {esc(c['status'])}{extra}{site}</li>"
                )
            bits.append("</ul>")
        res = q(
            """SELECT res.*, e.year, o.name AS office
               FROM results res
               JOIN candidacies c ON c.id=res.candidacy_id
               JOIN races r ON r.id=c.race_id
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE c.person_id=?
               ORDER BY e.year, res.round""",
            (p["id"],),
        ).fetchall()
        if res:
            bits.append("<h2>Results</h2><ul class='plain'>")
            for r in res:
                elected = " — elected" if r["elected"] else ""
                bits.append(
                    f"<li>{r['year']} {esc(r['office'])}, round {r['round']}: {r['votes']:,} votes{elected}</li>"
                )
            bits.append("</ul>")
        if answers:
            bits.append("<h2>On the record</h2>")
            for a in answers:
                bits.append(f"<h3>{esc(a['prompt'])}</h3>")
                if a["stance"]:
                    bits.append(f"<p><strong>{esc(a['stance']).upper()}</strong> — {esc(a['verbatim'])}</p>")
                else:
                    bits.append(f"<p>{esc(a['verbatim'])}</p>")
                bits.append(f"<p class='cite'><a href='{esc(a['source_url'])}'>{esc(a['source_title'])}</a></p>")
        if not cands and not holders:
            bits.append("<p class='note'>In the database as a candidate or officeholder; details still thin.</p>")
        rel = "../"
        html_page = page(p["full_name"], "\n".join(bits)).replace('href="index.html"', f'href="{rel}index.html"')
        for name in ["2026-mayor", "2026-council", "2025", "2023", "forums", "sources", "about"]:
            html_page = html_page.replace(f'href="{name}.html"', f'href="{rel}{name}.html"')
        html_page = html_page.replace('href="people/', 'href="')
        (OUT / "people" / f"{p['slug']}.html").write_text(html_page, encoding="utf-8")

    n_pages = len(list(OUT.rglob("*.html")))
    print(f"wrote {n_pages} html files into {OUT}")
    con.close()


if __name__ == "__main__":
    main()
