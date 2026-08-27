#!/usr/bin/env python3
"""Render a static, large-type prototype from data/bouldervotes.db into docs/."""
from __future__ import annotations

import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "bouldervotes.db"
OUT = ROOT / "docs"  # GitHub Pages serves /docs from main

NAV = [
    ("index.html", "Home"),
    ("2026.html", "2026"),
    ("2025.html", "2025"),
    ("2023.html", "2023"),
    ("forums.html", "Forums"),
    ("measures.html", "Measures"),
    ("sources.html", "Sources"),
    ("about.html", "About"),
]

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
.note, .empty { color: var(--muted); font-size: 0.95rem; }
.empty { font-style: italic; }
table { width: 100%; border-collapse: collapse; font-size: 0.95rem; margin: 0.75rem 0 1.25rem; }
th, td { text-align: left; padding: 0.4rem 0.5rem 0.4rem 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font-weight: 600; }
.num { font-variant-numeric: tabular-nums; text-align: right; }
.won { color: var(--won); font-weight: 600; }
.badge { display: inline-block; font-size: 0.75rem; letter-spacing: 0.03em; text-transform: uppercase; border: 1px solid var(--ink); padding: 0.05rem 0.4rem; margin-right: 0.3rem; }
.badge.match { border-color: var(--mark); color: var(--mark); }
.badge.inc { border-color: var(--won); color: var(--won); }
.stance { font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; font-size: 0.8rem; }
.stance.yes { color: var(--won); }
.stance.no { color: var(--mark); }
.stance.mixed { color: var(--muted); }
ul.plain { padding-left: 1.1rem; }
footer { margin: 3rem auto 2rem; padding-top: 1rem; border-top: 1px solid var(--rule); color: var(--muted); font-size: 0.9rem; }
.cite { font-size: 0.9rem; }
blockquote.answer { margin: 0.35rem 0 0.6rem; padding-left: 0.75rem; border-left: 3px solid var(--rule); font-size: 0.95rem; }
.year-sub { font-size: 0.95rem; margin: 0 0 1.25rem; }
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


def clip(text: str, n: int = 360) -> str:
    text = " ".join((text or "").split())
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + "…"


def nav_html(prefix: str = "") -> str:
    return "\n    ".join(f'<a href="{prefix}{href}">{label}</a>' for href, label in NAV)


def page(title: str, body: str, prefix: str = "") -> str:
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
  <a class="brand" href="{prefix}index.html">Boulder Votes</a>
  <p class="tagline">A map of who is running, what they have said, and where that information lives.</p>
  <nav>
    {nav_html(prefix)}
  </nav>
</header>
<main>
{body}
</main>
<footer>
  Prototype. Every number on this site is cited. We do not endorse candidates.
  City of Boulder only — not county, school board, or state races.
  Live at <a href="https://bouldervotes.org/">bouldervotes.org</a>.
</footer>
</body>
</html>
"""


def person_href(slug: str, prefix: str = "") -> str:
    return f"{prefix}people/{slug}.html"


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = con.execute

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "people").mkdir(exist_ok=True)

    def race_id(year: int, office: str) -> int | None:
        row = q(
            """SELECT r.id FROM races r
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE e.year=? AND o.slug=?""",
            (year, office),
        ).fetchone()
        return row[0] if row else None

    def candidates_for(race: int):
        return q(
            """SELECT c.id AS candidacy_id, p.slug, p.full_name, c.status, c.is_incumbent,
                      c.certified_on, c.matching_funds, c.campaign_url, c.notes
               FROM candidacies c JOIN people p ON p.id=c.person_id
               WHERE c.race_id=?
               ORDER BY p.sort_name""",
            (race,),
        ).fetchall()

    def cand_table(rows, include_cert: bool = False, include_status: bool = False) -> str:
        head = "<tr><th>Candidate</th><th></th>"
        if include_status:
            head += "<th>Status</th>"
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
            if include_status:
                row += f"<td>{esc(r['status'])}</td>"
            if include_cert:
                row += f"<td>{esc(r['certified_on'] or '')}</td>"
            row += "</tr>"
            body.append(row)
        return f"<table>{head}{''.join(body)}</table>"

    def results_table(year: int, office: str) -> str:
        rid = race_id(year, office)
        if rid is None:
            return '<p class="empty">No race recorded.</p>'
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
        if not rows:
            return '<p class="empty">Results not yet counted — or not yet ingested.</p>'
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

    def field_section(year: int) -> str:
        bits = ["<h2>The field</h2>"]
        mayor = race_id(year, "mayor")
        council = race_id(year, "council")
        if mayor:
            bits.append("<h3>Mayor</h3>")
            bits.append(cand_table(candidates_for(mayor), include_cert=(year == 2026), include_status=(year != 2026)))
        if council:
            bits.append("<h3>City council</h3>")
            bits.append(cand_table(candidates_for(council), include_cert=(year == 2026), include_status=(year != 2026)))
        if not mayor and not council:
            bits.append('<p class="empty">No city candidate races recorded for this year.</p>')
        return "\n".join(bits)

    def results_section(year: int) -> str:
        bits = ["<h2>Results</h2>"]
        mayor = race_id(year, "mayor")
        council = race_id(year, "council")
        has = False
        if mayor:
            table = results_table(year, "mayor")
            if "not yet" not in table:
                bits.append("<h3>Mayor</h3>")
                bits.append(table)
                has = True
        if council:
            table = results_table(year, "council")
            if "not yet" not in table:
                bits.append("<h3>City council</h3>")
                bits.append(table)
                has = True
        if not has:
            bits.append('<p class="empty">Election day has not happened yet, or results are not in the database.</p>')
        return "\n".join(bits)

    def questionnaire_section(year: int) -> str:
        questions = q(
            """SELECT q.id, q.prompt, q.kind, q.issue_slug, i.name AS issue
               FROM questions q LEFT JOIN issues i ON i.slug=q.issue_slug
               WHERE q.year=?
               ORDER BY q.kind, q.id""",
            (year,),
        ).fetchall()
        bits = ["<h2>Answers, question by question</h2>"]
        if not questions:
            bits.append(
                '<p class="empty">No comparable questionnaire ingested for this cycle yet. '
                "When Vote411 / BRL / Chamber Q&amp;A lands, it goes here in this same shape.</p>"
            )
            return "\n".join(bits)
        bits.append(
            "<p>Same question, every candidate who answered, the words they used, the source. "
            "A blank is a blank — we do not fill it in. Cells are clipped; full text is on each person’s page.</p>"
        )
        last_kind = None
        for qu in questions:
            if qu["kind"] != last_kind:
                label = {
                    "questionnaire": "Written questionnaires",
                    "forum": "Spoken answers at forums",
                    "interview": "Interviews",
                }.get(qu["kind"], qu["kind"].title())
                bits.append(f"<h3>{esc(label)}</h3>")
                last_kind = qu["kind"]
            issue = f" · {esc(qu['issue'])}" if qu["issue"] else ""
            bits.append(f"<h3>{esc(qu['prompt'])}{issue}</h3>")
            answers = q(
                """SELECT p.slug, p.full_name, a.stance, a.verbatim, s.title, s.url, a.kind
                   FROM answers a
                   JOIN people p ON p.id=a.person_id
                   JOIN sources s ON s.id=a.source_id
                   WHERE a.question_id=?
                   ORDER BY p.sort_name""",
                (qu["id"],),
            ).fetchall()
            if not answers:
                bits.append('<p class="empty">No answers stored for this question.</p>')
                continue
            src = answers[0]
            bits.append(f"<p class='cite'>Source: <a href='{esc(src['url'])}'>{esc(src['title'])}</a></p>")
            show_stance = any(a["stance"] for a in answers)
            head = "<tr><th>Candidate</th>"
            if show_stance:
                head += "<th>Stance</th>"
            head += "<th>Answer</th></tr>"
            rows = [head]
            for a in answers:
                name = f'<a href="{esc(person_href(a["slug"]))}">{esc(a["full_name"])}</a>'
                row = f"<tr><td>{name}</td>"
                if show_stance:
                    st = a["stance"] or "—"
                    cls = f" stance {esc(a['stance'])}" if a["stance"] else ""
                    row += f'<td><span class="{cls.strip()}">{esc(st)}</span></td>'
                row += f"<td>{esc(clip(a['verbatim']))}</td></tr>"
                rows.append(row)
            bits.append(f"<table>{''.join(rows)}</table>")
        return "\n".join(bits)

    def forums_for_year(year: int) -> list:
        return q(
            """SELECT e.*, o.name AS host
               FROM events e LEFT JOIN organizations o ON o.id=e.host_org_id
               WHERE e.starts_on LIKE ?
               ORDER BY e.starts_on""",
            (f"{year}%",),
        ).fetchall()

    def forum_block(e, heading: str = "h3") -> str:
        bits = [f"<{heading}>{esc(e['name'])}</{heading}>"]
        rec = f' · <a href="{esc(e["recording_url"])}">recording</a>' if e["recording_url"] else ""
        bits.append(
            f"<p>{esc(e['starts_on'])} · {esc(e['venue'] or 'venue not recorded')} · "
            f"hosted by {esc(e['host'] or 'unknown')}{rec}</p>"
        )
        if e["notes"]:
            bits.append(f"<p>{esc(e['notes'])}</p>")
        apps = q(
            """SELECT p.full_name, p.slug, a.attended
               FROM event_appearances a JOIN people p ON p.id=a.person_id
               WHERE a.event_id=? ORDER BY p.sort_name""",
            (e["id"],),
        ).fetchall()
        if apps:
            bits.append("<ul class='plain'>")
            for a in apps:
                flag = "attended" if a["attended"] == 1 else "did not attend" if a["attended"] == 0 else "unknown"
                bits.append(
                    f"<li><a href='{esc(person_href(a['slug']))}'>{esc(a['full_name'])}</a> — {flag}</li>"
                )
            bits.append("</ul>")
        else:
            bits.append('<p class="empty">Attendance not independently listed in the database. Recording or writeup is the source.</p>')
        return "\n".join(bits)

    def forums_section(year: int) -> str:
        bits = ["<h2>Forums</h2>"]
        events = forums_for_year(year)
        if not events:
            bits.append('<p class="empty">No forums catalogued for this year yet.</p>')
            return "\n".join(bits)
        for e in events:
            bits.append(forum_block(e))
        return "\n".join(bits)

    def press_section(year: int) -> str:
        bits = ["<h2>Interviews and press</h2>"]
        rows = q(
            """SELECT s.url, s.title, s.kind, s.published_on, o.name AS org
               FROM sources s LEFT JOIN organizations o ON o.id=s.org_id
               WHERE s.year=? AND s.kind IN ('article','interview')
               ORDER BY s.published_on, s.title""",
            (year,),
        ).fetchall()
        if not rows:
            bits.append('<p class="empty">No interview or profile pieces catalogued for this year yet.</p>')
            return "\n".join(bits)
        bits.append("<ul class='plain'>")
        for s in rows:
            date = f"{s['published_on']} — " if s["published_on"] else ""
            org = f"{s['org']} — " if s["org"] else ""
            bits.append(f"<li>{esc(date)}{esc(org)}<a href='{esc(s['url'])}'>{esc(s['title'])}</a></li>")
        bits.append("</ul>")
        return "\n".join(bits)

    def measures_for_year(year: int):
        return q(
            """SELECT m.*, e.year,
                      mr.yes_votes, mr.no_votes, mr.passed AS result_passed,
                      s.url AS source_url, s.title AS source_title
               FROM measures m
               JOIN elections e ON e.id=m.election_id
               LEFT JOIN measure_results mr ON mr.measure_id=m.id
               LEFT JOIN sources s ON s.id=m.source_id
               WHERE e.year=?
               ORDER BY m.letter IS NULL, m.letter, m.title""",
            (year,),
        ).fetchall()

    def measures_section(year: int) -> str:
        bits = ["<h2>City ballot measures</h2>"]
        rows = measures_for_year(year)
        if not rows:
            bits.append('<p class="empty">No city ballot measures recorded for this year.</p>')
            return "\n".join(bits)
        for m in rows:
            letter = f"{esc(m['letter'])}: " if m["letter"] else ""
            bits.append(f"<h3>{letter}{esc(m['title'])}</h3>")
            status = m["status"]
            if m["yes_votes"] is not None and m["no_votes"] is not None:
                total = m["yes_votes"] + m["no_votes"]
                pct = 100.0 * m["yes_votes"] / total if total else 0
                result = f"Yes {m['yes_votes']:,} ({pct:.1f}%) / No {m['no_votes']:,}"
                if m["result_passed"]:
                    result = f"Passed. {result}"
            else:
                result = status
            bits.append(f"<p><span class='badge'>{esc(m['kind'])}</span> {esc(result)}</p>")
            if m["summary"]:
                bits.append(f"<p>{esc(m['summary'])}</p>")
            if m["notes"]:
                bits.append(f"<p class='note'>{esc(m['notes'])}</p>")
            if m["source_url"]:
                bits.append(f"<p class='cite'><a href='{esc(m['source_url'])}'>{esc(m['source_title'])}</a></p>")
        return "\n".join(bits)

    year_ledes = {
        2026: (
            "November 3, 2026. First even-year municipal election. One mayor (ranked-choice) and five "
            "council seats (plurality), plus four referred city measures. Chamber recording is parked "
            "until they publish it."
        ),
        2025: (
            "November 4, 2025. Four at-large council seats, no mayoral race. Last odd-year municipal "
            "election; winners serve three-year terms. Boulder Reporting Lab asked all eleven candidates "
            "the same six questions — every answer is below."
        ),
        2023: (
            "November 7, 2023. First direct election of the mayor, ranked-choice. Four council seats. "
            "City ballots counted: 34,249. Active city voters: 68,812. BRL’s six-question survey of all "
            "14 candidates is the written record; Chamber, PLAN, Progressives, and LWV are the forum record."
        ),
    }

    extra_2026 = """
    <p class="year-sub"><a href="2026-mayor.html">Mayor race page</a> · <a href="2026-council.html">Council race page</a></p>
    <p>Four seats were already up (the 2023 class). Mark Wallach, reelected in 2025, resigned on July 23, 2026 after the 8–1 vote to pursue FAA grants for the municipal airport. Because he resigned before August 1, the charter puts that seat on the November ballot. Combined with Taishya Adams running for mayor, a majority of the dais is in play.</p>
    <p class="cite">Sources: <a href="https://www.axios.com/local/boulder/2026/07/24/boulder-city-council-mark-wallach-resigns">Axios, July 24 2026</a>; city clerk candidate list.</p>
    """
    extra_2025 = """
    <p>Lauren Folkerts, then mayor pro tem, finished sixth and left the council. Rob Kaplan, a former Boulder Rural Fire-Rescue captain, took the fourth seat. Totals: Boulder County Clarity ENR, last updated Nov 26 2025. Top four match the certified figures read at the Dec 4 2025 seating (<a href="https://www.dailycamera.com/2025/12/05/new-boulder-city-council-sworn-in-2/">Daily Camera</a>).</p>
    """
    extra_2023 = """
    <p>Bob Yates led on first-choice rankings. After Nicole Speer and Paul Tweedlie were eliminated, enough of Speer’s second choices moved to Aaron Brockett that Brockett won the final round 16,823–15,592. Ryan Schuchard won the fourth council seat by 46 votes over Terri Brncic after an automatic recount (Dec 5–6, 2023).</p>
    <p class="cite">RCV: <a href="https://assets.bouldercounty.gov/wp-content/uploads/2023/11/2023C-Boulder-County-Official-Summary-of-Votes.pdf">official summary of votes</a>. Council: <a href="https://assets.bouldercounty.gov/wp-content/uploads/2023/12/2023C-Boulder-County-Official-Summary-of-Votes-Recount.pdf">amended recount summary</a>.</p>
    """
    extras = {2026: extra_2026, 2025: extra_2025, 2023: extra_2023}

    for year in (2026, 2025, 2023):
        body = f"""
        <h1>{year} city election</h1>
        <p class="lede">{esc(year_ledes[year])}</p>
        {extras[year]}
        {field_section(year)}
        {results_section(year)}
        {questionnaire_section(year)}
        {forums_section(year)}
        {press_section(year)}
        {measures_section(year)}
        """
        (OUT / f"{year}.html").write_text(page(f"{year} election", body), encoding="utf-8")

    # ----- home -----
    mayor_n = q(
        "SELECT COUNT(*) FROM candidacies WHERE race_id = (SELECT r.id FROM races r JOIN elections e ON e.id=r.election_id JOIN offices o ON o.id=r.office_id WHERE e.year=2026 AND o.slug='mayor')"
    ).fetchone()[0]
    council_n = q(
        "SELECT COUNT(*) FROM candidacies WHERE race_id = (SELECT r.id FROM races r JOIN elections e ON e.id=r.election_id JOIN offices o ON o.id=r.office_id WHERE e.year=2026 AND o.slug='council')"
    ).fetchone()[0]
    src_n = q("SELECT COUNT(*) FROM sources").fetchone()[0]
    ans_n = q("SELECT COUNT(*) FROM answers").fetchone()[0]
    ev_n = q("SELECT COUNT(*) FROM events").fetchone()[0]
    meas_n = q("SELECT COUNT(*) FROM measures").fetchone()[0]

    home = f"""
    <h1>Boulder’s city elections, in one place</h1>
    <p class="lede">On November 3, 2026, Boulder voters will elect a mayor (ranked-choice) and five city council members (plurality, at-large), and vote on city ballot measures. This site maps the candidates, what they have said, the forums they showed up for, and the last two cycles in the same shape — so 2026 is easier to read once you have seen 2023 and 2025.</p>
    <p>Right now the database has <strong>{mayor_n} mayoral candidates</strong> and <strong>{council_n} council candidates</strong> certified for 2026, {ans_n} sourced answers, {ev_n} forums/events, {meas_n} city measures, and {src_n} source records. Candidate beliefs are <em>not</em> invented here — they are attached to a source, or they are absent.</p>
    <h2>Start here</h2>
    <ul class="plain">
      <li><a href="2026.html">2026</a> — field, forums so far, four referred measures. Chamber recording parked until they publish.</li>
      <li><a href="2025.html">2025</a> — eleven candidates, six BRL questions each, Chamber / VOTES! / LWV forums, CCRS 2A/2B.</li>
      <li><a href="2023.html">2023</a> — first RCV mayor, council recount, six BRL questions × 14 candidates, Chamber / PLAN / LWV, Safe Zones 4 Kids.</li>
      <li><a href="forums.html">Forums</a> — the calendar across years.</li>
      <li><a href="measures.html">Measures</a> — city ballot items 2023–2026.</li>
    </ul>
    <p>Each year page uses the same blocks, in the same order: the field, results, answers question-by-question, forums, interviews/press, ballot measures.</p>
    """
    (OUT / "index.html").write_text(page("Home", home), encoding="utf-8")

    # keep race-detail pages for 2026
    r_m = race_id(2026, "mayor")
    mayor_body = f"""
    <h1>2026 mayor</h1>
    <p>One seat. Ranked-choice voting — the second time Boulder has used it for mayor. Election day is Tuesday, November 3, 2026. Official ballot order was drawn by lot on August 25. The same information lives on the <a href="2026.html">2026 year page</a> with forums and measures.</p>
    <p>Voters mark candidates in order of preference. If no one has a majority of first-choice rankings, the last-place candidate is eliminated and those ballots move to the next choice, until someone crosses 50%.</p>
    {cand_table(candidates_for(r_m), include_cert=True)}
    <p class="cite">Candidate list and matching-funds flags: <a href="https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates">City of Boulder clerk, retrieved Aug 26 2026</a>. RCV explainer: <a href="https://bouldercolorado.gov/guide/ranked-choice-voting-guide">city RCV guide</a>.</p>
    <p class="note">Aaron Brockett is the sitting mayor. Taishya Adams is a sitting councilmember; running for mayor means she is not running to keep her council seat.</p>
    """
    (OUT / "2026-mayor.html").write_text(page("2026 mayor", mayor_body), encoding="utf-8")

    r_c = race_id(2026, "council")
    council_body = f"""
    <h1>2026 city council</h1>
    <p>Five at-large seats. Simple plurality: the five candidates with the most votes win. Ranked-choice voting does <em>not</em> apply to council. See also the <a href="2026.html">2026 year page</a>.</p>
    {cand_table(candidates_for(r_c), include_cert=True)}
    <p class="cite">Official list: <a href="https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates">City of Boulder clerk</a>.</p>
    <h2>Incumbents on this ballot</h2>
    <p>Tara Winer (mayor pro tem), Tina Marquis, and Ryan Schuchard. The other two seats are open: Taishya Adams’s (she is running for mayor) and Mark Wallach’s (resigned July 23, 2026).</p>
    <p>Councilmembers not on this ballot, terms through 2028: Matt Benjamin, Nicole Speer, Rob Kaplan.</p>
    """
    (OUT / "2026-council.html").write_text(page("2026 city council", council_body), encoding="utf-8")

    # ----- forums (all years) -----
    ev_html = [
        "<h1>Forums and appearances</h1>",
        "<p>Same calendar the year pages use, stacked newest first. Attendance is only listed when a published source named who showed. A missing name is unknown, not a secret no-show.</p>",
        "<p>The August 26, 2026 Chamber forum is parked until the Chamber releases the recording and materials.</p>",
    ]
    all_events = q(
        """SELECT e.*, o.name AS host
           FROM events e LEFT JOIN organizations o ON o.id=e.host_org_id
           ORDER BY e.starts_on DESC"""
    ).fetchall()
    current_year = None
    for e in all_events:
        y = int(e["starts_on"][:4])
        if y != current_year:
            ev_html.append(f"<h2>{y}</h2>")
            current_year = y
        ev_html.append(forum_block(e, heading="h3"))
    (OUT / "forums.html").write_text(page("Forums", "\n".join(ev_html)), encoding="utf-8")

    # ----- measures (all years) -----
    meas_html = [
        "<h1>City ballot measures</h1>",
        "<p>City of Boulder items only. County, BVSD, and state measures are out of scope. 2026 letters are not assigned yet.</p>",
    ]
    for year in (2026, 2025, 2023):
        meas_html.append(f"<h2>{year}</h2>")
        # reuse section without its own h2
        block = measures_section(year).replace("<h2>City ballot measures</h2>", "", 1)
        meas_html.append(block)
    (OUT / "measures.html").write_text(page("Measures", "\n".join(meas_html)), encoding="utf-8")

    sources = q(
        """SELECT s.*, o.name AS org
           FROM sources s LEFT JOIN organizations o ON o.id=s.org_id
           ORDER BY s.year DESC, s.published_on DESC, s.title"""
    ).fetchall()
    src_rows = ["<tr><th>Year</th><th>Kind</th><th>Source</th></tr>"]
    for s in sources:
        src_rows.append(
            f"<tr><td>{s['year'] or ''}</td><td>{esc(s['kind'])}</td>"
            f"<td><a href='{esc(s['url'])}'>{esc(s['title'])}</a>"
            f"<div class='note'>{esc(s['org'] or '')}{(' — ' + s['notes']) if s['notes'] else ''}</div></td></tr>"
        )
    src_body = f"""
    <h1>Where this information lives</h1>
    <p>The useful record is scattered across the city clerk, the county clerk, two or three newsrooms, advocacy groups that host forums, and the candidates themselves. This page is the catalog we are filling.</p>
    <table>{''.join(src_rows)}</table>
    """
    (OUT / "sources.html").write_text(page("Sources", src_body), encoding="utf-8")

    about = """
    <h1>About this prototype</h1>
    <p>Boulder Votes is a public-interest map of City of Boulder elections, starting with 2023, 2025, and the 2026 cycle now underway. The store is a SQLite database. The website is generated from that database. Nothing here is an endorsement.</p>
    <h2>Rules of the data</h2>
    <ul class="plain">
      <li>A number without a source is not published.</li>
      <li>A “position” is a quote or a journalist’s reported grouping, hanging off a source — not our summary of a person’s soul.</li>
      <li>Comparison grids stack sourced answers. They do not score candidates.</li>
      <li>Incumbency, matching funds, and certified-on dates come from the city clerk list unless noted.</li>
      <li>Older voters are the first audience: large type, one column, print-friendly, no motion.</li>
    </ul>
    <h2>What is not here yet</h2>
    <ul class="plain">
      <li>The August 26, 2026 Chamber forum recording — parked until the Chamber publishes it.</li>
      <li>Line-by-line transcripts of 2023/2025 forum video (the videos themselves are linked).</li>
      <li>Campaign finance line items (city filings page; TRACER does not cover this race).</li>
      <li>Most 2026 campaign websites.</li>
      <li>Vote411 / LWV 2026 questionnaire, when it opens.</li>
      <li>BVSD, county, state. Any social layer — ratings, comments, AT Proto. Later, on purpose.</li>
    </ul>
    <p>Live: <a href="https://bouldervotes.org/">bouldervotes.org</a>. Rebuild with <code>python3 harvest_brl.py && python3 seed.py && python3 build.py</code>.</p>
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
            """SELECT a.*, q.prompt, q.year AS q_year, q.kind AS q_kind,
                      s.title AS source_title, s.url AS source_url
               FROM answers a
               JOIN questions q ON q.id=a.question_id
               JOIN sources s ON s.id=a.source_id
               WHERE a.person_id=?
               ORDER BY q.year DESC, q.kind, q.id""",
            (p["id"],),
        ).fetchall()
        holders = q(
            """SELECT * FROM officeholders WHERE person_id=? ORDER BY term_start""",
            (p["id"],),
        ).fetchall()
        appearances = q(
            """SELECT e.name, e.starts_on, e.recording_url, e.kind, a.attended, o.name AS host
               FROM event_appearances a
               JOIN events e ON e.id=a.event_id
               LEFT JOIN organizations o ON o.id=e.host_org_id
               WHERE a.person_id=?
               ORDER BY e.starts_on DESC""",
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
        if appearances:
            bits.append("<h2>Forums</h2><ul class='plain'>")
            for a in appearances:
                flag = "attended" if a["attended"] == 1 else "did not attend" if a["attended"] == 0 else "unknown"
                rec = f' · <a href="{esc(a["recording_url"])}">recording</a>' if a["recording_url"] else ""
                bits.append(
                    f"<li>{esc(a['starts_on'])} {esc(a['name'])} — {flag}{rec}</li>"
                )
            bits.append("</ul>")
        if answers:
            bits.append("<h2>On the record</h2>")
            current = None
            for a in answers:
                year_kind = (a["q_year"], a["q_kind"])
                if year_kind != current:
                    kind_label = a["q_kind"] or "answer"
                    year_label = a["q_year"] or ""
                    bits.append(f"<h3>{esc(year_label)} {esc(kind_label)}</h3>")
                    current = year_kind
                bits.append(f"<h3>{esc(a['prompt'])}</h3>")
                if a["stance"]:
                    bits.append(
                        f"<p><span class='stance {esc(a['stance'])}'>{esc(a['stance'])}</span></p>"
                    )
                bits.append(f"<blockquote class='answer'>{esc(a['verbatim'])}</blockquote>")
                bits.append(f"<p class='cite'><a href='{esc(a['source_url'])}'>{esc(a['source_title'])}</a></p>")
        if not cands and not holders:
            bits.append("<p class='note'>In the database as a candidate or officeholder; details still thin.</p>")
        html_page = page(p["full_name"], "\n".join(bits), prefix="../")
        (OUT / "people" / f"{p['slug']}.html").write_text(html_page, encoding="utf-8")

    n_pages = len(list(OUT.rglob("*.html")))
    print(f"wrote {n_pages} html files into {OUT}")
    con.close()


if __name__ == "__main__":
    main()
