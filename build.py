#!/usr/bin/env python3
"""Render a static, large-type prototype from data/bouldervotes.db into docs/.

Information architecture (why the pages look like this):
  People persist across years. A year is a race, not an archive.
  Issues are the comparison axis — the only place a wall of quotes belongs.
  Sources are citations, never navigation. Adding a Camera interview or a
  forum transcript attaches to a person + an issue; it does not lengthen
  the year page.
"""
from __future__ import annotations

import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "bouldervotes.db"
OUT = ROOT / "docs"

NAV = [
    ("index.html", "Home"),
    ("2026.html", "2026"),
    ("issues.html", "Issues"),
    ("people.html", "People"),
    ("forums.html", "Forums"),
    ("measures.html", "Measures"),
    ("2025.html", "2025"),
    ("2023.html", "2023"),
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
header { padding-top: 1.5rem; padding-bottom: 0.75rem; border-bottom: 2px solid var(--ink); margin-bottom: 1.5rem; }
.brand { font-size: 1.35rem; font-weight: 700; letter-spacing: 0.01em; text-decoration: none; color: var(--ink); }
.tagline { color: var(--muted); font-size: 0.95rem; margin: 0.25rem 0 0.75rem; }
nav { display: flex; flex-wrap: wrap; gap: 0.75rem 1.1rem; font-size: 0.95rem; }
nav a { color: var(--link); }
h1 { font-size: 1.8rem; line-height: 1.2; margin: 0 0 0.75rem; }
h2 { font-size: 1.25rem; margin: 1.75rem 0 0.5rem; }
h3 { font-size: 1.05rem; margin: 1.2rem 0 0.35rem; }
h4 { font-size: 1rem; margin: 1rem 0 0.3rem; }
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
.toc { font-size: 0.95rem; margin: 0 0 1.5rem; padding: 0.75rem 0; border-bottom: 1px solid var(--rule); }
.toc a { margin-right: 0.9rem; }
.record { margin: 0.6rem 0 1.1rem; padding-bottom: 0.6rem; border-bottom: 1px solid var(--rule); }
.record-head { margin: 0 0 0.25rem; }
details.quote { margin: 0.35rem 0 0.4rem; }
details.quote > summary {
  cursor: pointer;
  color: var(--ink);
  list-style: none;
}
details.quote > summary::-webkit-details-marker { display: none; }
details.quote > summary::after { content: " — read full answer"; color: var(--link); font-size: 0.9rem; }
details.quote[open] > summary::after { content: " — hide"; }
blockquote.answer { margin: 0.4rem 0 0.2rem; padding-left: 0.75rem; border-left: 3px solid var(--rule); font-size: 0.95rem; }
.year-sub { font-size: 0.95rem; margin: 0 0 1.25rem; }
@media (max-width: 640px) {
  html { font-size: 18px; }
  table { font-size: 0.9rem; }
}
@media print {
  nav, .toc { display: none; }
  a { color: inherit; text-decoration: none; }
  details.quote { display: block; }
  details.quote > summary { display: none; }
  details.quote > blockquote { display: block; }
}
"""


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s))


def clip(text: str, n: int = 220) -> str:
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
  <p class="tagline">Who is running, what they have said, cited. One issue at a time.</p>
  <nav>
    {nav_html(prefix)}
  </nav>
</header>
<main>
{body}
</main>
<footer>
  Prototype. Every number is cited. We do not endorse candidates.
  City of Boulder only. Live at <a href="https://bouldervotes.org/">bouldervotes.org</a>.
  <a href="{prefix}sources.html">Source catalog</a>.
</footer>
</body>
</html>
"""


def person_href(slug: str, prefix: str = "") -> str:
    return f"{prefix}people/{slug}.html"


def issue_href(slug: str, prefix: str = "") -> str:
    return f"{prefix}issues/{slug}.html"


def quote_block(verbatim: str) -> str:
    text = verbatim or ""
    compact = " ".join(text.split())
    if len(compact) <= 240:
        return f"<blockquote class='answer'>{esc(text)}</blockquote>"
    return (
        f"<details class='quote'><summary>{esc(clip(compact, 200))}</summary>"
        f"<blockquote class='answer'>{esc(text)}</blockquote></details>"
    )


def stance_html(stance: str | None) -> str:
    if not stance:
        return ""
    return f"<span class='stance {esc(stance)}'>{esc(stance)}</span> "


def kind_label(kind: str | None) -> str:
    return {
        "questionnaire": "written questionnaire",
        "forum": "forum",
        "interview": "interview",
        "article": "press",
    }.get(kind or "", kind or "source")


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = con.execute

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "people").mkdir(exist_ok=True)
    (OUT / "issues").mkdir(exist_ok=True)

    def race_id(year: int, office: str) -> int | None:
        row = q(
            """SELECT r.id FROM races r
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE e.year=? AND o.slug=?""",
            (year, office),
        ).fetchone()
        return None if row is None else row[0]

    def candidates_for(race: int):
        return q(
            """SELECT c.id AS candidacy_id, p.slug, p.full_name, c.status, c.is_incumbent,
                      c.certified_on, c.matching_funds, c.campaign_url, c.notes
               FROM candidacies c JOIN people p ON p.id=c.person_id
               WHERE c.race_id=?
               ORDER BY p.sort_name""",
            (race,),
        ).fetchall()

    def cand_table(rows, prefix: str = "", include_cert: bool = False, include_status: bool = False) -> str:
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
            name = f'<a href="{esc(person_href(r["slug"], prefix))}">{esc(r["full_name"])}</a>'
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

    def results_table(year: int, office: str, prefix: str = "") -> str:
        rid = race_id(year, office)
        if rid is None:
            return '<p class="empty">No race recorded.</p>'
        rows = q(
            """SELECT p.full_name, p.slug, res.round, res.votes, res.vote_share, res.place, res.elected
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
            if len(rounds) > 1:
                chunks.append(f"<h3>Round {rnd}</h3>")
            body = ["<tr><th>Place</th><th>Candidate</th><th class='num'>Votes</th><th class='num'>Share</th></tr>"]
            for r in subset:
                share = f"{r['vote_share']:.2f}%" if r["vote_share"] is not None else "—"
                cls = "won" if r["elected"] else ""
                won = " (elected)" if r["elected"] else ""
                body.append(
                    f"<tr class='{cls}'><td class='num'>{r['place'] or ''}</td>"
                    f"<td><a href='{esc(person_href(r['slug'], prefix))}'>{esc(r['full_name'])}</a>{won}</td>"
                    f"<td class='num'>{r['votes']:,}</td><td class='num'>{share}</td></tr>"
                )
            chunks.append(f"<table>{''.join(body)}</table>")
        return "\n".join(chunks)

    def field_section(year: int, prefix: str = "") -> str:
        bits = ["<h2>The field</h2>"]
        mayor = race_id(year, "mayor")
        council = race_id(year, "council")
        if mayor:
            bits.append("<h3>Mayor</h3>")
            bits.append(cand_table(candidates_for(mayor), prefix, include_cert=(year == 2026), include_status=(year != 2026)))
        if council:
            bits.append("<h3>City council</h3>")
            bits.append(cand_table(candidates_for(council), prefix, include_cert=(year == 2026), include_status=(year != 2026)))
        if not mayor and not council:
            bits.append('<p class="empty">No city candidate races recorded for this year.</p>')
        return "\n".join(bits)

    def results_section(year: int, prefix: str = "") -> str:
        bits = ["<h2>Results</h2>"]
        has = False
        if race_id(year, "mayor"):
            table = results_table(year, "mayor", prefix)
            if "not yet" not in table:
                bits.append("<h3>Mayor</h3>")
                bits.append(table)
                has = True
        if race_id(year, "council"):
            table = results_table(year, "council", prefix)
            if "not yet" not in table:
                bits.append("<h3>City council</h3>")
                bits.append(table)
                has = True
        if not has:
            bits.append('<p class="empty">Election day has not happened yet, or results are not in the database.</p>')
        return "\n".join(bits)

    def issues_with_answers(year: int | None = None):
        sql = """
            SELECT COALESCE(q.issue_slug, 'other') AS slug,
                   COALESCE(i.name, 'This race / other') AS name,
                   COUNT(a.id) AS n
            FROM answers a
            JOIN questions q ON q.id=a.question_id
            LEFT JOIN issues i ON i.slug=q.issue_slug
        """
        params: tuple = ()
        if year is not None:
            sql += " WHERE q.year=?"
            params = (year,)
        sql += " GROUP BY 1, 2 ORDER BY n DESC, name"
        return q(sql, params).fetchall()

    def said_section(year: int, prefix: str = "") -> str:
        rows = issues_with_answers(year)
        bits = ["<h2>What they said</h2>"]
        if not rows:
            bits.append(
                '<p class="empty">No comparable answers ingested for this cycle yet. '
                "When a questionnaire, forum transcript, or interview lands, it is filed "
                "under an issue — not dumped onto this page.</p>"
            )
            return "\n".join(bits)
        n = sum(r["n"] for r in rows)
        bits.append(
            f"<p>{n} sourced answers, filed by issue. A new article does not make this page longer — "
            f"it attaches to the issue and to the person.</p>"
        )
        bits.append("<ul class='plain'>")
        for r in rows:
            bits.append(
                f"<li><a href='{esc(issue_href(r['slug'], prefix))}'>{esc(r['name'])}</a> — {r['n']} answers</li>"
            )
        bits.append("</ul>")
        return "\n".join(bits)

    def forums_for_year(year: int):
        return q(
            """SELECT e.*, o.name AS host
               FROM events e LEFT JOIN organizations o ON o.id=e.host_org_id
               WHERE e.starts_on LIKE ?
               ORDER BY e.starts_on""",
            (f"{year}%",),
        ).fetchall()

    def forum_block(e, heading: str = "h3", prefix: str = "", attendance: bool = True) -> str:
        bits = [f"<{heading}>{esc(e['name'])}</{heading}>"]
        rec = f' · <a href="{esc(e["recording_url"])}">recording</a>' if e["recording_url"] else ""
        bits.append(
            f"<p>{esc(e['starts_on'])} · {esc(e['venue'] or 'venue not recorded')} · "
            f"hosted by {esc(e['host'] or 'unknown')}{rec}</p>"
        )
        if e["notes"] and attendance:
            bits.append(f"<p>{esc(e['notes'])}</p>")
        apps = q(
            """SELECT p.full_name, p.slug, a.attended
               FROM event_appearances a JOIN people p ON p.id=a.person_id
               WHERE a.event_id=? ORDER BY p.sort_name""",
            (e["id"],),
        ).fetchall()
        if not attendance:
            showed = sum(1 for a in apps if a["attended"] == 1)
            if showed:
                bits.append(f"<p class='note'>{showed} named attendees — full list on the forums page and on each person.</p>")
            return "\n".join(bits)
        if apps:
            bits.append("<ul class='plain'>")
            for a in apps:
                flag = "attended" if a["attended"] == 1 else "did not attend" if a["attended"] == 0 else "unknown"
                bits.append(
                    f"<li><a href='{esc(person_href(a['slug'], prefix))}'>{esc(a['full_name'])}</a> — {flag}</li>"
                )
            bits.append("</ul>")
        else:
            bits.append('<p class="empty">Attendance not independently listed. Recording or writeup is the source.</p>')
        return "\n".join(bits)

    def forums_section(year: int, prefix: str = "") -> str:
        bits = ["<h2>Forums</h2>"]
        events = forums_for_year(year)
        if not events:
            bits.append('<p class="empty">No forums catalogued for this year yet.</p>')
            return "\n".join(bits)
        bits.append(f"<p class='note'><a href='{prefix}forums.html'>Full calendar</a> with attendance.</p>")
        for e in events:
            bits.append(forum_block(e, prefix=prefix, attendance=False))
        return "\n".join(bits)

    def press_section(year: int) -> str:
        bits = ["<h2>Interviews and press</h2>"]
        rows = q(
            """SELECT s.url, s.title, s.published_on, o.name AS org
               FROM sources s LEFT JOIN organizations o ON o.id=s.org_id
               WHERE s.year=? AND s.kind IN ('article','interview')
               ORDER BY s.published_on, s.title""",
            (year,),
        ).fetchall()
        if not rows:
            bits.append('<p class="empty">No interview or profile pieces catalogued for this year yet.</p>')
            return "\n".join(bits)
        bits.append(
            "<p class='note'>These are the articles. Quoted claims from them belong on an issue page, "
            "attached to a person — cataloguing a URL is not the same as ingesting an answer.</p>"
        )
        bits.append("<ul class='plain'>")
        for s in rows:
            date = f"{s['published_on']} — " if s["published_on"] else ""
            org = f"{s['org']} — " if s["org"] else ""
            bits.append(f"<li>{esc(date)}{esc(org)}<a href='{esc(s['url'])}'>{esc(s['title'])}</a></li>")
        bits.append("</ul>")
        return "\n".join(bits)

    def measures_for_year(year: int):
        return q(
            """SELECT m.*, mr.yes_votes, mr.no_votes, mr.passed AS result_passed,
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
            if m["yes_votes"] is not None and m["no_votes"] is not None:
                total = m["yes_votes"] + m["no_votes"]
                pct = 100.0 * m["yes_votes"] / total if total else 0
                result = f"Yes {m['yes_votes']:,} ({pct:.1f}%) / No {m['no_votes']:,}"
                if m["result_passed"]:
                    result = f"Passed. {result}"
            else:
                result = m["status"]
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
            "November 3, 2026. First even-year municipal election. One mayor (ranked-choice), "
            "five council seats (plurality), four referred city measures. This page is the race. "
            "What people said lives under Issues and on each person."
        ),
        2025: (
            "November 4, 2025. Four council seats, no mayor. Last odd-year municipal election. "
            "BRL asked all eleven candidates the same six questions — filed under Issues."
        ),
        2023: (
            "November 7, 2023. First direct RCV mayor, four council seats. "
            "City ballots counted: 34,249. BRL’s six questions × 14 candidates are under Issues."
        ),
    }
    extras = {
        2026: """
        <p class="year-sub"><a href="2026-mayor.html">Mayor race</a> · <a href="2026-council.html">Council race</a></p>
        <p>Four seats were already up. Mark Wallach resigned July 23, 2026 after the 8–1 FAA-grant vote; because he left before August 1 the charter puts that seat on this ballot. Taishya Adams is running for mayor, so a majority of the dais is in play.</p>
        """,
        2025: """
        <p>Lauren Folkerts finished sixth. Rob Kaplan took the fourth seat. Clarity ENR totals match the Dec 4 2025 seating (<a href="https://www.dailycamera.com/2025/12/05/new-boulder-city-council-sworn-in-2/">Daily Camera</a>).</p>
        """,
        2023: """
        <p>Yates led round 1; Brockett won the final 16,823–15,592. Schuchard took the fourth council seat by 46 over Brncic after the recount.</p>
        """,
    }

    for year in (2026, 2025, 2023):
        body = f"""
        <h1>{year} city election</h1>
        <p class="lede">{esc(year_ledes[year])}</p>
        {extras[year]}
        {field_section(year)}
        {results_section(year)}
        {said_section(year)}
        {forums_section(year)}
        {press_section(year)}
        {measures_section(year)}
        """
        (OUT / f"{year}.html").write_text(page(f"{year} election", body), encoding="utf-8")

    # ----- home -----
    mayor_n = q(
        """SELECT COUNT(*) FROM candidacies c
           JOIN races r ON r.id=c.race_id JOIN elections e ON e.id=r.election_id
           JOIN offices o ON o.id=r.office_id
           WHERE e.year=2026 AND o.slug='mayor'"""
    ).fetchone()[0]
    council_n = q(
        """SELECT COUNT(*) FROM candidacies c
           JOIN races r ON r.id=c.race_id JOIN elections e ON e.id=r.election_id
           JOIN offices o ON o.id=r.office_id
           WHERE e.year=2026 AND o.slug='council'"""
    ).fetchone()[0]
    ans_n = q("SELECT COUNT(*) FROM answers").fetchone()[0]
    issue_rows = issues_with_answers()

    issue_lis = "".join(
        f"<li><a href='{esc(issue_href(r['slug']))}'>{esc(r['name'])}</a> — {r['n']} answers</li>"
        for r in issue_rows
    )
    home = f"""
    <h1>November 3, 2026</h1>
    <p class="lede">Boulder elects a mayor (ranked-choice) and five city council members, and votes on city measures. This site is a map of the candidates and of what they have actually said — quoted, cited, not scored.</p>
    <p>The 2026 ballot has <strong>{mayor_n} mayoral</strong> and <strong>{council_n} council</strong> candidates certified. The database holds {ans_n} sourced answers from 2023, 2025, and 2026. A new forum or newspaper piece should attach to a person and an issue. It should not make the year page longer.</p>
    <h2>Compare them on</h2>
    <ul class="plain">{issue_lis}</ul>
    <h2>This year’s race</h2>
    <ul class="plain">
      <li><a href="2026.html">2026 overview</a> — field, measures, forums so far.</li>
      <li><a href="2026-mayor.html">Mayor</a> · <a href="2026-council.html">Council</a></li>
      <li><a href="people.html">Everyone in the database</a> — dossiers, not a feed.</li>
    </ul>
    <h2>How 2023 and 2025 went</h2>
    <p>Those cycles are here so 2026 is readable: same issues, many of the same people, certified results. Start at <a href="2025.html">2025</a> or <a href="2023.html">2023</a> only if you want the race record. For beliefs, use Issues.</p>
    """
    (OUT / "index.html").write_text(page("Home", home), encoding="utf-8")

    r_m = race_id(2026, "mayor")
    (OUT / "2026-mayor.html").write_text(
        page(
            "2026 mayor",
            f"""
    <h1>2026 mayor</h1>
    <p>One seat, ranked-choice, second use. Ballot order drawn August 25. The comparison lives on <a href="issues.html">Issues</a>; this page is the field. See also the <a href="2026.html">2026 year page</a>.</p>
    {cand_table(candidates_for(r_m), include_cert=True)}
    <p class="cite"><a href="https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates">City clerk, retrieved Aug 26 2026</a>. <a href="https://bouldercolorado.gov/guide/ranked-choice-voting-guide">RCV guide</a>.</p>
    """,
        ),
        encoding="utf-8",
    )
    r_c = race_id(2026, "council")
    (OUT / "2026-council.html").write_text(
        page(
            "2026 city council",
            f"""
    <h1>2026 city council</h1>
    <p>Five at-large seats, plurality. RCV does not apply. <a href="2026.html">Year page</a> · <a href="issues.html">Issues</a>.</p>
    {cand_table(candidates_for(r_c), include_cert=True)}
    <p class="cite"><a href="https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates">City clerk</a>.</p>
    <p>Incumbents on this ballot: Tara Winer (mayor pro tem), Tina Marquis, Ryan Schuchard. Open: Adams’s (running for mayor) and Wallach’s (resigned). Terms through 2028, not on this ballot: Benjamin, Speer, Kaplan.</p>
    """,
        ),
        encoding="utf-8",
    )

    # ----- issues index + issue pages -----
    issues = q("SELECT slug, name, description FROM issues ORDER BY name").fetchall()
    issue_index_lis = []
    for iss in issues:
        n = q(
            "SELECT COUNT(*) FROM answers a JOIN questions q ON q.id=a.question_id WHERE q.issue_slug=?",
            (iss["slug"],),
        ).fetchone()[0]
        issue_index_lis.append(
            f"<li><a href='{esc(issue_href(iss['slug']))}'>{esc(iss['name'])}</a> — {n} answers"
            f"<div class='note'>{esc(iss['description'] or '')}</div></li>"
        )
    other_n = q(
        "SELECT COUNT(*) FROM answers a JOIN questions q ON q.id=a.question_id WHERE q.issue_slug IS NULL"
    ).fetchone()[0]
    if other_n:
        issue_index_lis.append(
            f"<li><a href='{esc(issue_href('other'))}'>This race / other</a> — {other_n} answers"
            f"<div class='note'>Lived experience, one-year visions, prompts that are not a city issue.</div></li>"
        )
    (OUT / "issues.html").write_text(
        page(
            "Issues",
            f"""
    <h1>Issues</h1>
    <p class="lede">This is the comparison. One issue, every candidate who answered, each source kept separate. We do not merge a 2023 questionnaire with a 2025 one, and we do not average two quotes into a score.</p>
    <ul class="plain">{''.join(issue_index_lis)}</ul>
    """,
        ),
        encoding="utf-8",
    )

    issue_pages = [(iss["slug"], iss["name"], iss["description"]) for iss in issues]
    issue_pages.append(("other", "This race / other", "Prompts that are not a single city issue."))

    for slug, name, desc in issue_pages:
        if slug == "other":
            questions = q(
                """SELECT q.id, q.prompt, q.year, q.kind
                   FROM questions q WHERE q.issue_slug IS NULL ORDER BY q.year, q.id"""
            ).fetchall()
        else:
            questions = q(
                """SELECT q.id, q.prompt, q.year, q.kind
                   FROM questions q WHERE q.issue_slug=? ORDER BY q.year, q.id""",
                (slug,),
            ).fetchall()
        bits = [f"<h1>{esc(name)}</h1>"]
        if desc:
            bits.append(f"<p class='lede'>{esc(desc)}</p>")
        bits.append(
            "<p>Each block is one question, in one year, from one kind of source. "
            "A person may appear twice if they answered two different sources. That is the point.</p>"
        )
        if not questions:
            bits.append('<p class="empty">No questions filed under this issue yet.</p>')
        current_year = None
        for qu in questions:
            if qu["year"] != current_year:
                bits.append(f"<h2>{qu['year'] or 'undated'}</h2>")
                current_year = qu["year"]
            bits.append(f"<h3>{esc(qu['prompt'])}</h3>")
            bits.append(f"<p class='note'>{esc(kind_label(qu['kind']))}</p>")
            answers = q(
                """SELECT p.slug, p.full_name, a.stance, a.verbatim, a.kind,
                          s.title AS source_title, s.url AS source_url, s.published_on
                   FROM answers a
                   JOIN people p ON p.id=a.person_id
                   JOIN sources s ON s.id=a.source_id
                   WHERE a.question_id=?
                   ORDER BY p.sort_name""",
                (qu["id"],),
            ).fetchall()
            if not answers:
                bits.append('<p class="empty">No answers stored.</p>')
                continue
            src0 = answers[0]
            bits.append(
                f"<p class='cite'><a href='{esc(src0['source_url'])}'>{esc(src0['source_title'])}</a></p>"
            )
            for a in answers:
                bits.append("<div class='record'>")
                bits.append(
                    f"<p class='record-head'><a href='{esc(person_href(a['slug'], '../'))}'>{esc(a['full_name'])}</a> "
                    f"{stance_html(a['stance'])}</p>"
                )
                bits.append(quote_block(a["verbatim"]))
                bits.append("</div>")
        html_page = page(name, "\n".join(bits), prefix="../")
        (OUT / "issues" / f"{slug}.html").write_text(html_page, encoding="utf-8")

    # ----- people index -----
    people = q("SELECT * FROM people ORDER BY sort_name").fetchall()
    plist = ["<h1>People</h1>", "<p>Dossiers. A person lasts across years; a candidacy does not.</p>", "<ul class='plain'>"]
    for p in people:
        years = q(
            """SELECT e.year, o.slug AS office, c.status
               FROM candidacies c JOIN races r ON r.id=c.race_id
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE c.person_id=? ORDER BY e.year DESC""",
            (p["id"],),
        ).fetchall()
        n_ans = q("SELECT COUNT(*) FROM answers WHERE person_id=?", (p["id"],)).fetchone()[0]
        ytxt = ", ".join(f"{y['year']} {y['office']}" for y in years) or "no candidacy"
        extra = f" · {n_ans} answers" if n_ans else ""
        plist.append(
            f"<li><a href='{esc(person_href(p['slug']))}'>{esc(p['full_name'])}</a> — {esc(ytxt)}{extra}</li>"
        )
    plist.append("</ul>")
    (OUT / "people.html").write_text(page("People", "\n".join(plist)), encoding="utf-8")

    # ----- forums -----
    ev_html = [
        "<h1>Forums</h1>",
        "<p>The calendar. Spoken answers harvested from a forum live on the matching issue page. "
        "Attendance is listed only when a published source named who showed.</p>",
        "<p>August 26, 2026 Chamber forum is parked until they publish the recording.</p>",
    ]
    all_events = q(
        """SELECT e.*, o.name AS host
           FROM events e LEFT JOIN organizations o ON o.id=e.host_org_id
           ORDER BY e.starts_on DESC"""
    ).fetchall()
    current_year = None
    for e in all_events:
        y = int(str(e["starts_on"])[:4])
        if y != current_year:
            ev_html.append(f"<h2>{y}</h2>")
            current_year = y
        ev_html.append(forum_block(e, heading="h3", prefix=""))
    (OUT / "forums.html").write_text(page("Forums", "\n".join(ev_html)), encoding="utf-8")

    meas_html = [
        "<h1>City ballot measures</h1>",
        "<p>City of Boulder items only. 2026 letters are not assigned yet.</p>",
    ]
    for year in (2026, 2025, 2023):
        meas_html.append(f"<h2>{year}</h2>")
        meas_html.append(measures_section(year).replace("<h2>City ballot measures</h2>", "", 1))
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
    (OUT / "sources.html").write_text(
        page(
            "Sources",
            f"""
    <h1>Source catalog</h1>
    <p>The basement. Useful for checking our work. Not how a voter should navigate. Quoted claims live on issue pages and person pages, hanging off these URLs.</p>
    <table>{''.join(src_rows)}</table>
    """,
        ),
        encoding="utf-8",
    )

    about = """
    <h1>About</h1>
    <p>Boulder Votes is a public-interest map of City of Boulder elections. SQLite in, static HTML out. No endorsements.</p>
    <h2>How the information is structured</h2>
    <ul class="plain">
      <li><strong>People</strong> persist. Tara Winer is one dossier across 2023 and 2026, not two brochure pages.</li>
      <li><strong>A year is a race</strong> — who ran, how they voted, which measures, which forums. It is not the quote archive.</li>
      <li><strong>Issues are the comparison.</strong> Housing, airport, camping, wildfire. Add a Daily Camera interview and it files here, next to the BRL questionnaire, as a second source — not a longer year page.</li>
      <li><strong>Sources are citations.</strong> Every number and every quote points at one. The catalog is for us, not the front door.</li>
    </ul>
    <h2>Rules</h2>
    <ul class="plain">
      <li>A number without a source is not published.</li>
      <li>Two quotes are not averaged. Absence is a blank.</li>
      <li>Older voters first: large type, one column, print-friendly, no motion, no JavaScript required. Long answers fold; print unfolds them.</li>
    </ul>
    <h2>Not here yet</h2>
    <ul class="plain">
      <li>2026 Chamber recording (parked until they publish).</li>
      <li>Line-by-line forum transcripts (videos are linked).</li>
      <li>Campaign finance line items.</li>
      <li>Most 2026 campaign sites, Vote411 when it opens.</li>
      <li>County, BVSD, state. Ratings, comments, AT Proto.</li>
    </ul>
    <p>Live: <a href="https://bouldervotes.org/">bouldervotes.org</a>. Rebuild: <code>python3 harvest_brl.py && python3 seed.py && python3 build.py</code>.</p>
    """
    (OUT / "about.html").write_text(page("About", about), encoding="utf-8")

    # ----- person pages -----
    for p in people:
        cands = q(
            """SELECT c.*, e.year, o.name AS office
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
                      COALESCE(q.issue_slug, 'other') AS issue_slug,
                      COALESCE(i.name, 'This race / other') AS issue_name,
                      s.title AS source_title, s.url AS source_url
               FROM answers a
               JOIN questions q ON q.id=a.question_id
               JOIN sources s ON s.id=a.source_id
               LEFT JOIN issues i ON i.slug=q.issue_slug
               WHERE a.person_id=?
               ORDER BY issue_name, q.year DESC, q.id""",
            (p["id"],),
        ).fetchall()
        holders = q(
            "SELECT * FROM officeholders WHERE person_id=? ORDER BY term_start",
            (p["id"],),
        ).fetchall()
        appearances = q(
            """SELECT e.name, e.starts_on, e.recording_url, a.attended
               FROM event_appearances a
               JOIN events e ON e.id=a.event_id
               WHERE a.person_id=?
               ORDER BY e.starts_on DESC""",
            (p["id"],),
        ).fetchall()
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

        bits = [f"<h1>{esc(p['full_name'])}</h1>"]
        toc = []
        if holders:
            toc.append("<a href='#office'>Office</a>")
        if cands:
            toc.append("<a href='#campaigns'>Campaigns</a>")
        if res:
            toc.append("<a href='#results'>Results</a>")
        if appearances:
            toc.append("<a href='#forums'>Forums</a>")
        if answers:
            toc.append("<a href='#record'>On the record</a>")
        if toc:
            bits.append(f"<nav class='toc'>{''.join(toc)}</nav>")
        if p["notes"]:
            bits.append(f"<p>{esc(p['notes'])}</p>")
        if holders:
            bits.append("<h2 id='office'>Office</h2><ul class='plain'>")
            for h in holders:
                end = h["term_end"] or "current"
                extra = f" — {h['how_ended']}" if h["how_ended"] else ""
                bits.append(f"<li>{esc(h['role'])}: {esc(h['term_start'])} to {esc(end)}{esc(extra)}</li>")
            bits.append("</ul>")
        if cands:
            bits.append("<h2 id='campaigns'>Campaigns</h2><ul class='plain'>")
            for c in cands:
                flags = []
                if c["is_incumbent"]:
                    flags.append("incumbent")
                if c["matching_funds"]:
                    flags.append("matching funds")
                extra = f" ({', '.join(flags)})" if flags else ""
                site = f' · <a href="{esc(c["campaign_url"])}">campaign site</a>' if c["campaign_url"] else ""
                bits.append(f"<li>{c['year']} {esc(c['office'])} — {esc(c['status'])}{extra}{site}</li>")
            bits.append("</ul>")
        if res:
            bits.append("<h2 id='results'>Results</h2><ul class='plain'>")
            for r in res:
                elected = " — elected" if r["elected"] else ""
                bits.append(
                    f"<li>{r['year']} {esc(r['office'])}, round {r['round']}: {r['votes']:,} votes{elected}</li>"
                )
            bits.append("</ul>")
        if appearances:
            bits.append("<h2 id='forums'>Forums</h2><ul class='plain'>")
            for a in appearances:
                flag = "attended" if a["attended"] == 1 else "did not attend" if a["attended"] == 0 else "unknown"
                rec = f' · <a href="{esc(a["recording_url"])}">recording</a>' if a["recording_url"] else ""
                bits.append(f"<li>{esc(a['starts_on'])} {esc(a['name'])} — {flag}{rec}</li>")
            bits.append("</ul>")
        if answers:
            bits.append("<h2 id='record'>On the record</h2>")
            bits.append("<p class='note'>Grouped by issue, then by year. Each quote keeps its own source.</p>")
            current_issue = None
            for a in answers:
                if a["issue_slug"] != current_issue:
                    bits.append(
                        f"<h3><a href='{esc(issue_href(a['issue_slug'], '../'))}'>{esc(a['issue_name'])}</a></h3>"
                    )
                    current_issue = a["issue_slug"]
                bits.append("<div class='record'>")
                bits.append(
                    f"<p class='record-head'>{a['q_year'] or ''} · {esc(kind_label(a['q_kind']))} "
                    f"{stance_html(a['stance'])}</p>"
                )
                bits.append(f"<h4>{esc(a['prompt'])}</h4>")
                bits.append(quote_block(a["verbatim"]))
                bits.append(f"<p class='cite'><a href='{esc(a['source_url'])}'>{esc(a['source_title'])}</a></p>")
                bits.append("</div>")
        if not cands and not holders:
            bits.append("<p class='note'>In the database as a candidate or officeholder; details still thin.</p>")
        (OUT / "people" / f"{p['slug']}.html").write_text(
            page(p["full_name"], "\n".join(bits), prefix="../"), encoding="utf-8"
        )

    n_pages = len(list(OUT.rglob("*.html")))
    print(f"wrote {n_pages} html files into {OUT}")
    con.close()


if __name__ == "__main__":
    main()
