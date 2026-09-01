#!/usr/bin/env python3
"""Render Boulder Votes from SQLite into docs/.

Voter chrome, not an essay:
  A year is a ballot you zoom into (who is running, what is on it).
  A person is a dossier you zoom into (what they have said, year by year).
  An issue is a comparison you zoom into (this year's field, then earlier).
  Sources stay citations. Full quotes fold. Absence is a blank cell.
"""
from __future__ import annotations

import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "bouldervotes.db"
OUT = ROOT / "docs"
YEARS = (2026, 2025, 2023, 2021, 2019, 2017)

CSS = """
:root {
  --paper: #f4efe6;
  --ink: #1c1916;
  --muted: #5c5348;
  --rule: #d4c7b0;
  --link: #1f4b73;
  --link-visited: #5a3d6e;
  --mark: #8b2e1a;
  --won: #215c3a;
  --chip: #efe6d6;
}
* { box-sizing: border-box; }
html { font-size: 19px; scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  line-height: 1.45;
}
header {
  position: sticky; top: 0; z-index: 5;
  background: var(--paper);
  border-bottom: 2px solid var(--ink);
}
.header-inner, main, footer { max-width: 46rem; margin: 0 auto; padding: 0 1.1rem; }
.header-inner { padding-top: 0.7rem; padding-bottom: 0.7rem; }
.brand { font-size: 1.2rem; font-weight: 700; text-decoration: none; color: var(--ink); }
.rail { display: flex; flex-wrap: wrap; gap: 0.35rem 0.5rem; margin-top: 0.45rem; align-items: center; }
.rail a, .pill {
  display: inline-block;
  padding: 0.12rem 0.55rem;
  border: 1px solid var(--ink);
  text-decoration: none;
  color: var(--ink);
  font-size: 0.9rem;
}
.rail a.on, .pill.on { background: var(--ink); color: var(--paper); }
.rail .sep { color: var(--muted); margin: 0 0.25rem; }
nav.util { margin-top: 0.35rem; display: flex; flex-wrap: wrap; gap: 0.6rem 0.9rem; font-size: 0.9rem; }
nav.util a { color: var(--link); }
h1 { font-size: 1.7rem; line-height: 1.15; margin: 1.1rem 0 0.5rem; }
h2 { font-size: 1.2rem; margin: 1.5rem 0 0.45rem; }
h3 { font-size: 1.02rem; margin: 1rem 0 0.3rem; }
p, li { max-width: 42rem; }
.lede { font-size: 1.05rem; margin-top: 0; }
.note, .empty { color: var(--muted); font-size: 0.92rem; }
.empty { font-style: italic; }
a { color: var(--link); }
a:visited { color: var(--link-visited); }
.jump { font-size: 0.92rem; margin: 0.4rem 0 1rem; }
.jump a { margin-right: 0.8rem; }
.card {
  border: 1px solid var(--rule);
  padding: 0.65rem 0.8rem;
  margin: 0 0 0.55rem;
  background: #f8f3ea;
}
.card h3 { margin: 0 0 0.2rem; font-size: 1.05rem; }
.card .meta { color: var(--muted); font-size: 0.88rem; }
.chips { margin-top: 0.35rem; }
.chip {
  display: inline-block;
  font-size: 0.78rem;
  border: 1px solid var(--rule);
  background: var(--chip);
  padding: 0.05rem 0.4rem;
  margin: 0 0.25rem 0.25rem 0;
  text-decoration: none;
  color: var(--ink);
}
.badge { display: inline-block; font-size: 0.72rem; letter-spacing: 0.03em; text-transform: uppercase; border: 1px solid var(--ink); padding: 0.02rem 0.35rem; margin-right: 0.25rem; }
.badge.match { border-color: var(--mark); color: var(--mark); }
.badge.inc { border-color: var(--won); color: var(--won); }
.choice {
  display: block;
  border: 2px solid var(--ink);
  padding: 0.7rem 0.9rem;
  margin: 0.45rem 0;
  text-decoration: none;
  color: var(--ink);
  background: #f8f3ea;
  font-size: 1.05rem;
}
.choice:hover { background: var(--chip); }
.choice .meta { font-size: 0.88rem; color: var(--muted); margin-top: 0.15rem; }
.stance { font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; font-size: 0.78rem; }
.stance.yes { color: var(--won); }
.stance.no { color: var(--mark); }
.stance.mixed { color: var(--muted); }
table { width: 100%; border-collapse: collapse; font-size: 0.92rem; margin: 0.5rem 0 1rem; }
th, td { text-align: left; padding: 0.35rem 0.4rem 0.35rem 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font-weight: 600; }
.num { font-variant-numeric: tabular-nums; text-align: right; }
.won { color: var(--won); font-weight: 600; }
.matrix td, .matrix th { text-align: center; }
.matrix th:first-child, .matrix td:first-child { text-align: left; }
.matrix a { text-decoration: none; }
details.quote { margin: 0.25rem 0; }
details.quote > summary { cursor: pointer; }
details.quote > summary::after { content: " — full"; color: var(--link); font-size: 0.88rem; }
details.quote[open] > summary::after { content: " — hide"; }
blockquote.answer { margin: 0.35rem 0; padding-left: 0.7rem; border-left: 3px solid var(--rule); font-size: 0.95rem; }
.crumb { font-size: 0.9rem; color: var(--muted); margin: 0.8rem 0 0; }
footer { margin: 2.5rem auto 1.5rem; padding-top: 0.8rem; border-top: 1px solid var(--rule); color: var(--muted); font-size: 0.88rem; }
@media (max-width: 640px) {
  html { font-size: 18px; }
}
@media print {
  header { position: static; }
  nav.util, .jump, .print-hint { display: none; }
  a { color: inherit; text-decoration: none; }
  details.quote > summary { display: none; }
  details.quote > blockquote { display: block; }
  @page { size: letter; margin: 0.55in; }
  h1 { font-size: 1.45rem; }
}
"""


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s))


def clip(text: str, n: int = 160) -> str:
    text = " ".join((text or "").split())
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + "…"


def dollars(n: object) -> str:
    if n is None:
        return "—"
    try:
        x = float(n)
    except (TypeError, ValueError):
        return "—"
    if abs(x - round(x)) < 0.005:
        return f"${x:,.0f}"
    return f"${x:,.2f}"


def stance_html(stance: str | None) -> str:
    if not stance:
        return ""
    return f"<span class='stance {esc(stance)}'>{esc(stance)}</span>"


def kind_label(kind: str | None) -> str:
    return {
        "questionnaire": "questionnaire",
        "forum": "forum",
        "interview": "interview",
        "article": "press",
    }.get(kind or "", kind or "source")


def quote_block(verbatim: str) -> str:
    text = verbatim or ""
    compact = " ".join(text.split())
    if len(compact) <= 180:
        return f"<blockquote class='answer'>{esc(text)}</blockquote>"
    return (
        f"<details class='quote'><summary>{esc(clip(compact, 150))}</summary>"
        f"<blockquote class='answer'>{esc(text)}</blockquote></details>"
    )


def page(title: str, body: str, *, prefix: str = "", year: int | None = None) -> str:
    rail = []
    for y in YEARS:
        on = " on" if y == year else ""
        rail.append(f'<a class="{on.strip()}" href="{prefix}{y}.html">{y}</a>')
    util = [
        f'<a href="{prefix}find.html">Find</a>',
        f'<a href="{prefix}issues.html">Issues</a>',
        f'<a href="{prefix}people.html">People</a>',
        f'<a href="{prefix}finance.html">Money</a>',
        f'<a href="{prefix}print/index.html">Print</a>',
        f'<a href="{prefix}about.html">About</a>',
    ]
    home = f"{prefix}index.html"
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
  <div class="header-inner">
    <a class="brand" href="{home}">Boulder Votes</a>
    <div class="rail">{''.join(rail)}</div>
    <nav class="util">{''.join(util)}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer>
  City of Boulder only. Cited, not scored, not an endorsement.
  <a href="{prefix}sources.html">Sources</a> ·
  <a href="{prefix}forums.html">Forums</a> ·
  <a href="{prefix}find.html">Find</a> ·
  <a href="{prefix}finance.html">Money</a> ·
  <a href="{prefix}questionnaires.html">Questionnaires</a> ·
  <a href="{prefix}print/index.html">Print</a> ·
  <a href="{prefix}measures.html">All measures</a> ·
  <a href="https://bouldervotes.org/">bouldervotes.org</a>
</footer>
</body>
</html>
"""


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = con.execute
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "people").mkdir(exist_ok=True)
    (OUT / "issues").mkdir(exist_ok=True)
    (OUT / "print").mkdir(exist_ok=True)
    (OUT / "find").mkdir(exist_ok=True)

    def race_id(year: int, office: str) -> int | None:
        row = q(
            """SELECT r.id FROM races r
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE e.year=? AND o.slug=?""",
            (year, office),
        ).fetchone()
        return None if row is None else row[0]

    def candidates_for(year: int, office: str):
        rid = race_id(year, office)
        if rid is None:
            return []
        return q(
            """SELECT c.id AS candidacy_id, p.id AS person_id, p.slug, p.full_name,
                      c.status, c.is_incumbent, c.matching_funds, c.campaign_url, c.certified_on
               FROM candidacies c JOIN people p ON p.id=c.person_id
               WHERE c.race_id=?
               ORDER BY p.sort_name""",
            (rid,),
        ).fetchall()

    def prior_years(person_id: int, year: int) -> list[sqlite3.Row]:
        return q(
            """SELECT e.year, o.slug AS office, c.status, res.votes, res.elected
               FROM candidacies c
               JOIN races r ON r.id=c.race_id
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               LEFT JOIN results res ON res.candidacy_id=c.id AND res.round = (
                 SELECT MAX(round) FROM results r2 WHERE r2.candidacy_id=c.id
               )
               WHERE c.person_id=? AND e.year<?
               ORDER BY e.year""",
            (person_id, year),
        ).fetchall()

    def issues_answered(person_id: int) -> list[sqlite3.Row]:
        return q(
            """SELECT DISTINCT COALESCE(q.issue_slug,'other') AS slug,
                      COALESCE(i.name,'This race / other') AS name
               FROM answers a
               JOIN questions q ON q.id=a.question_id
               LEFT JOIN issues i ON i.slug=q.issue_slug
               WHERE a.person_id=?
               ORDER BY name""",
            (person_id,),
        ).fetchall()

    def finance_for(person_id: int, year: int = 2026):
        return q(
            "SELECT * FROM finance_snapshots WHERE person_id=? AND year=?",
            (person_id, year),
        ).fetchone()

    def person_href(slug: str, prefix: str = "") -> str:
        return f"{prefix}people/{slug}.html"

    def issue_href(slug: str, year: int | None = None, prefix: str = "") -> str:
        if year:
            return f"{prefix}issues/{slug}-{year}.html"
        return f"{prefix}issues/{slug}.html"

    def candidate_card(row, year: int, office: str, prefix: str = "") -> str:
        flags = []
        if row["is_incumbent"]:
            flags.append('<span class="badge inc">incumbent</span>')
        if row["matching_funds"]:
            flags.append('<span class="badge match">matching funds</span>')
        prior = prior_years(row["person_id"], year)
        prior_bits = []
        for p in prior:
            bit = f"{p['year']} {p['office']}"
            if p["elected"]:
                bit += " elected"
            elif p["status"] == "lost":
                bit += " lost"
            prior_bits.append(bit)
        returning = f"<div class='meta'>Also: {esc(', '.join(prior_bits))}</div>" if prior_bits else ""
        issues = [i for i in issues_answered(row["person_id"]) if i["slug"] != "other"]
        chips = ""
        if issues:
            chips = "<div class='chips'>" + "".join(
                f"<a class='chip' href='{esc(issue_href(i['slug'], year, prefix))}'>{esc(i['name'])}</a>"
                for i in issues
            ) + "</div>"
        elif year == 2026:
            chips = "<div class='meta'>No sourced answers yet this cycle.</div>"
        site = (
            f" · <a href='{esc(row['campaign_url'])}'>campaign</a>"
            if row["campaign_url"]
            else ""
        )
        status = "" if year == 2026 else f"<div class='meta'>{esc(row['status'])}</div>"
        money = ""
        if year == 2026:
            snap = finance_for(row["person_id"], 2026)
            if snap:
                match = (
                    f" · matching {dollars(snap['matching_received'])}"
                    if snap["matching_received"]
                    else ""
                )
                money = f"<div class='meta'>Raised {dollars(snap['contributions'])}{match}</div>"
        return f"""<div class="card">
          <h3><a href="{esc(person_href(row['slug'], prefix))}">{esc(row['full_name'])}</a> {''.join(flags)}{site}</h3>
          {status}{returning}{money}{chips}
        </div>"""

    def results_table(year: int, office: str, prefix: str = "") -> str:
        rid = race_id(year, office)
        if rid is None:
            return ""
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
            return ""
        rounds = sorted({r["round"] for r in rows})
        chunks = []
        for rnd in rounds:
            subset = [r for r in rows if r["round"] == rnd]
            if len(rounds) > 1:
                chunks.append(f"<h3>Round {rnd}</h3>")
            body = ["<tr><th>Place</th><th>Candidate</th><th class='num'>Votes</th></tr>"]
            for r in subset:
                cls = "won" if r["elected"] else ""
                won = " (elected)" if r["elected"] else ""
                body.append(
                    f"<tr class='{cls}'><td class='num'>{r['place'] or ''}</td>"
                    f"<td><a href='{esc(person_href(r['slug'], prefix))}'>{esc(r['full_name'])}</a>{won}</td>"
                    f"<td class='num'>{r['votes']:,}</td></tr>"
                )
            chunks.append(f"<table>{''.join(body)}</table>")
        return "\n".join(chunks)

    def measures_for_year(year: int):
        return q(
            """SELECT m.*, mr.yes_votes, mr.no_votes, mr.passed AS result_passed
               FROM measures m
               JOIN elections e ON e.id=m.election_id
               LEFT JOIN measure_results mr ON mr.measure_id=m.id
               WHERE e.year=?
               ORDER BY m.letter IS NULL, m.letter, m.title""",
            (year,),
        ).fetchall()

    def measure_cards(year: int) -> str:
        rows = measures_for_year(year)
        if not rows:
            return '<p class="empty">No city measures recorded.</p>'
        bits = []
        for m in rows:
            letter = f"{esc(m['letter'])}: " if m["letter"] else ""
            if m["yes_votes"] is not None and m["no_votes"] is not None:
                total = m["yes_votes"] + m["no_votes"]
                pct = 100.0 * m["yes_votes"] / total if total else 0
                result = (
                    f"Passed · yes {m['yes_votes']:,} ({pct:.0f}%)"
                    if m["result_passed"]
                    else f"Failed · yes {m['yes_votes']:,} ({pct:.0f}%)"
                )
            else:
                result = m["status"]
            bits.append(
                f"<div class='card'><h3>{letter}{esc(m['title'])}</h3>"
                f"<div class='meta'>{esc(m['kind'])} · {esc(result)}</div>"
                f"<p>{esc(clip(m['summary'] or '', 220))}</p></div>"
            )
        return "\n".join(bits)

    def forums_for_year(year: int):
        return q(
            """SELECT e.*, o.name AS host,
                      (SELECT COUNT(*) FROM event_appearances a WHERE a.event_id=e.id AND a.attended=1) AS showed
               FROM events e LEFT JOIN organizations o ON o.id=e.host_org_id
               WHERE e.starts_on LIKE ?
               ORDER BY e.starts_on""",
            (f"{year}%",),
        ).fetchall()

    def issue_years(slug: str) -> list[int]:
        if slug == "other":
            rows = q("SELECT DISTINCT q.year FROM questions q WHERE q.issue_slug IS NULL AND q.year IS NOT NULL")
        else:
            rows = q("SELECT DISTINCT q.year FROM questions q WHERE q.issue_slug=? AND q.year IS NOT NULL", (slug,))
        return sorted({r[0] for r in rows.fetchall()}, reverse=True)

    def all_issues():
        issues = [(r["slug"], r["name"], r["description"]) for r in q("SELECT slug, name, description FROM issues ORDER BY name")]
        other = q("SELECT COUNT(*) FROM questions WHERE issue_slug IS NULL").fetchone()[0]
        if other:
            issues.append(("other", "This race / other", "Lived experience and one-year visions."))
        return issues

    def year_issue_answers(slug: str, year: int, ballot_person_ids: set[int]):
        """Answers on this issue from people on this year's ballot — this year first, then earlier."""
        if slug == "other":
            issue_clause = "q.issue_slug IS NULL"
            params: list = []
        else:
            issue_clause = "q.issue_slug=?"
            params = [slug]
        rows = q(
            f"""SELECT a.id, p.id AS person_id, p.slug, p.full_name, a.stance, a.verbatim,
                       a.kind, q.prompt, q.year AS q_year, s.title AS source_title, s.url AS source_url
                FROM answers a
                JOIN people p ON p.id=a.person_id
                JOIN questions q ON q.id=a.question_id
                JOIN sources s ON s.id=a.source_id
                WHERE {issue_clause}
                ORDER BY p.sort_name, q.year DESC""",
            params,
        ).fetchall()
        return [
            r for r in rows
            if r["person_id"] in ballot_person_ids and (r["q_year"] or 0) <= year
        ]

    def write_year_page(year: int, as_home: bool = False) -> None:
        mayor = candidates_for(year, "mayor")
        council = candidates_for(year, "council")
        ballot_ids = {r["person_id"] for r in list(mayor) + list(council)}
        issue_links = []
        for slug, name, _desc in all_issues():
            n = len({r["person_id"] for r in year_issue_answers(slug, year, ballot_ids)})
            if n:
                issue_links.append(
                    f"<a class='chip' href='{esc(issue_href(slug, year))}'>{esc(name)} · {n}</a>"
                )
        how = {
            2026: "Mayor is ranked-choice (one seat). Council is plurality — five highest vote-getters win. Four city measures are also on the ballot.",
            2025: "Four council seats, no mayor. Last odd-year municipal election.",
            2023: "First direct ranked-choice mayor, four council seats. 34,249 city ballots counted.",
            2021: "Five council seats, no directly elected mayor. Top four: four-year terms; fifth: two-year. 33,772 city ballots; 68,885 active city voters.",
            2019: "Six council seats after Jill Grano resigned (the vacancy added a two-year seat). No directly elected mayor. Top four: four-year; fifth and sixth: two-year. 34,971 city ballots; 68,749 active city voters.",
            2017: "Five council seats, no directly elected mayor. Top four: four-year terms; fifth: two-year. 31,765 city ballots; 72,574 active city voters.",
        }[year]
        jump = '<p class="jump"><a href="#mayor">Mayor</a>' if mayor else '<p class="jump">'
        if council:
            jump += '<a href="#council">Council</a>'
        jump += '<a href="#said">What they have said</a><a href="#measures">Measures</a>'
        if year == 2026:
            jump += '<a href="#money">Money</a>'
        jump += "</p>"
        bits = [
            f"<h1>{'Tuesday, November 3, 2026' if year == 2026 else str(year) + ' city election'}</h1>",
            f"<p class='lede'>{esc(how)}</p>",
            jump,
        ]
        if year == 2026:
            bits.append(
                "<p><a class='choice' href='find.html'>What do you care about?"
                "<span class='meta'>Two or three questions. You get their sourced answers, not a score.</span></a></p>"
            )
        if mayor:
            bits.append(f"<h2 id='mayor'>Mayor · {len(mayor)} candidates</h2>")
            if year != 2026:
                bits.append(results_table(year, "mayor"))
            for r in mayor:
                bits.append(candidate_card(r, year, "mayor"))
        if council:
            seats = {2026: 5, 2025: 4, 2023: 4, 2021: 5, 2019: 6, 2017: 5}[year]
            bits.append(f"<h2 id='council'>City council · {seats} seats · {len(council)} candidates</h2>")
            if year == 2026:
                bits.append(
                    "<p class='note'>Five seats because Wallach resigned July 23 (before Aug 1) and Adams is running for mayor. "
                    "Not on this ballot (terms through 2028): Benjamin, Speer, Kaplan. "
                    "<a href='find.html'>Answer a couple of questions</a> · "
                    "<a href='finance.html'>Money raised</a> · "
                    "<a href='print/index.html'>Print a sheet</a>.</p>"
                )
            if year == 2019:
                bits.append(
                    "<p class='note'>Six seats because Jill Grano resigned in January 2019. "
                    "Fifth place (Swetlik) and sixth place (Wallach) served two-year terms.</p>"
                )
            if year != 2026:
                bits.append(results_table(year, "council"))
            for r in council:
                bits.append(candidate_card(r, year, "council"))
            if year == 2026:
                money = q(
                    """SELECT p.full_name, p.slug, f.contributions, f.expenditures, f.matching_received, f.reported_on
                       FROM finance_snapshots f JOIN people p ON p.id=f.person_id
                       WHERE f.year=2026 ORDER BY f.contributions DESC, p.sort_name"""
                ).fetchall()
                if money:
                    bits.append("<h2 id='money'>Money so far</h2>")
                    bits.append(
                        "<p class='note'>City clerk contributions &amp; expenditures, retrieved 2026-09-01. "
                        "Not TRACER. $0 means they filed that, not that we guessed. "
                        "<a href='finance.html'>Donors, spending, and source</a>.</p>"
                    )
                    rows = ["<tr><th>Candidate</th><th class='num'>Raised</th><th class='num'>Spent</th><th class='num'>Matching</th></tr>"]
                    for m in money:
                        rows.append(
                            f"<tr><td><a href='{esc(person_href(m['slug']))}'>{esc(m['full_name'])}</a></td>"
                            f"<td class='num'>{dollars(m['contributions'])}</td>"
                            f"<td class='num'>{dollars(m['expenditures'])}</td>"
                            f"<td class='num'>{dollars(m['matching_received'])}</td></tr>"
                        )
                    bits.append(f"<table>{''.join(rows)}</table>")
        bits.append("<h2 id='said'>What this ballot’s candidates have said</h2>")
        bits.append(
            "<p>Includes what returning candidates said in earlier cycles. A blank means we do not have it — not that they are silent.</p>"
        )
        if issue_links:
            bits.append("<div class='chips'>" + "".join(issue_links) + "</div>")
        else:
            bits.append('<p class="empty">No sourced answers for this field yet.</p>')
        bits.append("<h2 id='measures'>City measures</h2>")
        bits.append(measure_cards(year))
        evs = forums_for_year(year)
        if evs:
            bits.append("<h2>Forums</h2>")
            bits.append("<ul>")
            for e in evs:
                rec = f' · <a href="{esc(e["recording_url"])}">recording</a>' if e["recording_url"] else ""
                bits.append(
                    f"<li>{esc(e['starts_on'])} {esc(e['name'])}{rec}</li>"
                )
            bits.append("</ul>")
            bits.append(f"<p class='note'><a href='forums.html'>Attendance and notes</a></p>")
        html_page = page(
            "November 2026" if as_home else f"{year} election",
            "\n".join(bits),
            year=year,
        )
        (OUT / ("index.html" if as_home else f"{year}.html")).write_text(html_page, encoding="utf-8")
        if as_home:
            (OUT / "2026.html").write_text(html_page, encoding="utf-8")

    for y in YEARS:
        write_year_page(y, as_home=(y == 2026))

    # ----- issues hub -----
    hub = [
        "<h1>Issues</h1>",
        "<p class='lede'>Pick an issue, then a year. You will see the people on that year’s ballot and what they have said — this cycle and, if they ran before, earlier.</p>",
    ]
    for slug, name, desc in all_issues():
        ys = issue_years(slug)
        if not ys:
            continue
        pills = " ".join(f"<a class='pill' href='{esc(issue_href(slug, y))}'>{y}</a>" for y in ys)
        ongoing = "ongoing" if len(ys) > 1 else f"appeared {ys[0]}"
        hub.append(
            f"<div class='card'><h3><a href='{esc(issue_href(slug))}'>{esc(name)}</a></h3>"
            f"<div class='meta'>{esc(ongoing)} · {esc(desc or '')}</div>"
            f"<div class='chips' style='margin-top:0.4rem'>{pills}</div></div>"
        )
    (OUT / "issues.html").write_text(page("Issues", "\n".join(hub)), encoding="utf-8")

    def questions_for(slug: str, year: int):
        if slug == "other":
            return q(
                "SELECT id, prompt, kind FROM questions WHERE issue_slug IS NULL AND year=? ORDER BY id",
                (year,),
            ).fetchall()
        return q(
            "SELECT id, prompt, kind FROM questions WHERE issue_slug=? AND year=? ORDER BY id",
            (slug, year),
        ).fetchall()

    def answers_for_question(qid: int, person_ids: set[int] | None = None):
        rows = q(
            """SELECT a.id, p.id AS person_id, p.slug, p.full_name, a.stance, a.verbatim,
                      s.title AS source_title, s.url AS source_url
               FROM answers a
               JOIN people p ON p.id=a.person_id
               JOIN sources s ON s.id=a.source_id
               WHERE a.question_id=?
               ORDER BY p.sort_name""",
            (qid,),
        ).fetchall()
        if person_ids is None:
            return rows
        return [r for r in rows if r["person_id"] in person_ids]

    for slug, name, desc in all_issues():
        ys = issue_years(slug)
        # hub page for the issue
        bits = [
            f"<p class='crumb'><a href='../issues.html'>Issues</a></p>",
            f"<h1>{esc(name)}</h1>",
        ]
        if desc:
            bits.append(f"<p class='lede'>{esc(desc)}</p>")
        if len(ys) > 1:
            bits.append(f"<p>Asked in {', '.join(str(y) for y in ys)}. The question wording changes; the issue persists.</p>")
        elif ys:
            bits.append(f"<p>On the record in {ys[0]} so far.</p>")
        bits.append(
            "<p>This issue in: "
            + " ".join(f"<a class='pill' href='{esc(slug)}-{y}.html'>{y}</a>" for y in ys)
            + "</p>"
        )
        (OUT / "issues" / f"{slug}.html").write_text(
            page(name, "\n".join(bits), prefix="../"), encoding="utf-8"
        )

        for year in YEARS:
            ballot = list(candidates_for(year, "mayor")) + list(candidates_for(year, "council"))
            ballot_ids = {r["person_id"] for r in ballot}
            qs_this = questions_for(slug, year)
            prior_people = year_issue_answers(slug, year, ballot_ids)
            prior_only = [r for r in prior_people if r["q_year"] != year]
            if not qs_this and not prior_only:
                continue
            year_pills = "".join(
                f"<a class='pill{' on' if y == year else ''}' href='{esc(slug)}-{y}.html'>{y}</a> "
                for y in issue_years(slug) or [year]
            )
            body = [
                f"<p class='crumb'><a href='../issues.html'>Issues</a> · <a href='{esc(slug)}.html'>{esc(name)}</a></p>",
                f"<h1>{esc(name)} · {year}</h1>",
                f"<p class='note'>This issue in: {year_pills}</p>",
                f"<p>People on the {year} ballot. Answers from this cycle first. "
                f"If a returning candidate only answered in an earlier race, that quote is labelled as earlier — not as a {year} answer.</p>",
            ]
            # compact scan table of this year's questions
            for qu in qs_this:
                ans = answers_for_question(qu["id"], ballot_ids)
                body.append(f"<h2>{esc(qu['prompt'])}</h2>")
                body.append(f"<p class='note'>{esc(kind_label(qu['kind']))}</p>")
                if ans:
                    src = ans[0]
                    body.append(f"<p class='note'><a href='{esc(src['source_url'])}'>{esc(src['source_title'])}</a></p>")
                    show_st = any(a["stance"] for a in ans)
                    head = "<tr><th>Candidate</th>"
                    if show_st:
                        head += "<th style='width:4.5rem'>Stance</th>"
                    head += "<th>What they said</th></tr>"
                    rows_html = [head]
                    for a in ans:
                        st = f"<td>{stance_html(a['stance'])}</td>" if show_st else ""
                        rows_html.append(
                            f"<tr><td><a href='{esc(person_href(a['slug'], '../'))}'>{esc(a['full_name'])}</a></td>"
                            f"{st}<td>{quote_block(a['verbatim'])}</td></tr>"
                        )
                    body.append(f"<table>{''.join(rows_html)}</table>")
                else:
                    body.append(f"<p class='empty'>No one on the {year} ballot answered this prompt.</p>")
            if prior_only:
                # unique people who have only earlier answers
                this_year_ids = set()
                for qu in qs_this:
                    this_year_ids |= {a["person_id"] for a in answers_for_question(qu["id"], ballot_ids)}
                earlier = [r for r in prior_only if r["person_id"] not in this_year_ids]
                if earlier:
                    body.append(f"<h2>Returning candidates — said this before {year}</h2>")
                    body.append("<p class='note'>They are on this ballot. The quote is from an earlier cycle. We do not treat it as a {year} answer.</p>".replace("{year}", str(year)))
                    seen = set()
                    for r in earlier:
                        key = (r["person_id"], r["q_year"], r["prompt"])
                        if key in seen:
                            continue
                        seen.add(key)
                        body.append(
                            f"<div class='card'><h3><a href='{esc(person_href(r['slug'], '../'))}'>{esc(r['full_name'])}</a> "
                            f"{stance_html(r['stance'])}</h3>"
                            f"<div class='meta'>{r['q_year']} {esc(kind_label(r['kind']))} · {esc(clip(r['prompt'], 120))}</div>"
                            f"{quote_block(r['verbatim'])}"
                            f"<p class='note'><a href='{esc(r['source_url'])}'>{esc(r['source_title'])}</a></p></div>"
                        )
            (OUT / "issues" / f"{slug}-{year}.html").write_text(
                page(f"{name} {year}", "\n".join(body), prefix="../", year=year),
                encoding="utf-8",
            )

    # rebuild issue hub pills now that slices exist — already linked

    # ----- people index -----
    people = q("SELECT * FROM people ORDER BY sort_name").fetchall()
    on_2026 = {r["person_id"] for r in candidates_for(2026, "mayor") + candidates_for(2026, "council")}
    plist = [
        "<h1>People</h1>",
        "<p class='lede'>A person lasts across years. Open a dossier to see the issue × year grid — what they said, and when they said it.</p>",
        "<h2>On the 2026 ballot</h2>",
    ]
    later = ["<h2>Earlier cycles only</h2>"]
    for p in people:
        years = q(
            """SELECT e.year, o.slug AS office, c.status
               FROM candidacies c JOIN races r ON r.id=c.race_id
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE c.person_id=? ORDER BY e.year DESC""",
            (p["id"],),
        ).fetchall()
        ytxt = ", ".join(f"{y['year']} {y['office']}" for y in years) or "no candidacy"
        n_ans = q("SELECT COUNT(*) FROM answers WHERE person_id=?", (p["id"],)).fetchone()[0]
        extra = f" · {n_ans} answers" if n_ans else ""
        snap = finance_for(p["id"], 2026) if p["id"] in on_2026 else None
        if snap:
            extra += f" · raised {dollars(snap['contributions'])}"
        li = f"<div class='card'><h3><a href='{esc(person_href(p['slug']))}'>{esc(p['full_name'])}</a></h3><div class='meta'>{esc(ytxt)}{extra}</div></div>"
        if p["id"] in on_2026:
            plist.append(li)
        else:
            later.append(li)
    plist.extend(later)
    (OUT / "people.html").write_text(page("People", "\n".join(plist)), encoding="utf-8")

    # ----- person dossiers -----
    for p in people:
        cands = q(
            """SELECT c.*, e.year, o.name AS office, o.slug AS office_slug
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
                      COALESCE(q.issue_slug,'other') AS issue_slug,
                      COALESCE(i.name,'This race / other') AS issue_name,
                      s.title AS source_title, s.url AS source_url
               FROM answers a
               JOIN questions q ON q.id=a.question_id
               JOIN sources s ON s.id=a.source_id
               LEFT JOIN issues i ON i.slug=q.issue_slug
               WHERE a.person_id=?
               ORDER BY issue_name, q.year DESC, q.id""",
            (p["id"],),
        ).fetchall()
        appearances = q(
            """SELECT e.name, e.starts_on, e.recording_url, a.attended
               FROM event_appearances a JOIN events e ON e.id=a.event_id
               WHERE a.person_id=? ORDER BY e.starts_on DESC""",
            (p["id"],),
        ).fetchall()
        res = q(
            """SELECT res.votes, res.elected, res.round, e.year, o.slug AS office
               FROM results res
               JOIN candidacies c ON c.id=res.candidacy_id
               JOIN races r ON r.id=c.race_id
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE c.person_id=?
               ORDER BY e.year, res.round""",
            (p["id"],),
        ).fetchall()

        years_in = sorted({c["year"] for c in cands} | {a["q_year"] for a in answers if a["q_year"]}, reverse=True)
        issue_rows = []
        seen_iss = []
        for a in answers:
            if a["issue_slug"] not in seen_iss:
                seen_iss.append(a["issue_slug"])
                issue_rows.append((a["issue_slug"], a["issue_name"]))

        bits = [f"<h1>{esc(p['full_name'])}</h1>"]
        if p["notes"]:
            bits.append(f"<p class='lede'>{esc(p['notes'])}</p>")

        # timeline
        bits.append("<h2>Campaigns</h2>")
        tbody = ["<tr><th>Year</th><th>Office</th><th>Outcome</th></tr>"]
        for c in cands:
            flags = []
            if c["is_incumbent"]:
                flags.append("incumbent")
            if c["matching_funds"]:
                flags.append("matching funds")
            extra = f" ({', '.join(flags)})" if flags else ""
            outcome = c["status"]
            rmatch = [r for r in res if r["year"] == c["year"] and r["office"] == c["office_slug"]]
            if rmatch:
                last = rmatch[-1]
                outcome = f"{last['votes']:,} votes" + (" · elected" if last["elected"] else "")
            site = f" · <a href='{esc(c['campaign_url'])}'>campaign</a>" if c["campaign_url"] else ""
            tbody.append(
                f"<tr><td><a href='../{c['year']}.html'>{c['year']}</a></td>"
                f"<td>{esc(c['office'])}{extra}{site}</td><td>{esc(outcome)}</td></tr>"
            )
        bits.append(f"<table>{''.join(tbody)}</table>")

        snaps = q(
            "SELECT * FROM finance_snapshots WHERE person_id=? ORDER BY year DESC",
            (p["id"],),
        ).fetchall()
        if snaps:
            bits.append("<h2>Money</h2>")
            for snap in snaps:
                n_donors = q(
                    """SELECT COUNT(*) FROM finance_line_items
                       WHERE snapshot_id=? AND direction='contribution'""",
                    (snap["id"],),
                ).fetchone()[0]
                n_exp = q(
                    """SELECT COUNT(*) FROM finance_line_items
                       WHERE snapshot_id=? AND direction='expenditure'""",
                    (snap["id"],),
                ).fetchone()[0]
                bits.append(
                    f"<p>{snap['year']}: raised {dollars(snap['contributions'])} · "
                    f"spent {dollars(snap['expenditures'])} · "
                    f"matching received {dollars(snap['matching_received'])}"
                    + (
                        f" · cash on hand {dollars(snap['cash_on_hand'])}"
                        if snap["cash_on_hand"] is not None
                        else ""
                    )
                    + f" ({esc(snap['committee_name'])}"
                    + (f", as of {esc(snap['reported_on'])}" if snap["reported_on"] else "")
                    + ").</p>"
                )
                if snap["notes"]:
                    bits.append(f"<p class='note'>{esc(snap['notes'])}</p>")
                bits.append(
                    f"<p class='note'>{n_donors} contribution line{'' if n_donors == 1 else 's'}, "
                    f"{n_exp} expenditure{'' if n_exp == 1 else 's'}. City clerk, not TRACER. "
                    f"<a href='{esc(snap['reports_url'] or '../finance.html')}'>Clerk statements</a> · "
                    f"<a href='../finance.html'>Everyone</a>.</p>"
                )
                contribs = q(
                    """SELECT display_name, item_type, occurred_on, amount, from_candidate, donor_person_id
                       FROM finance_line_items
                       WHERE snapshot_id=? AND direction='contribution'
                       ORDER BY amount DESC, last_name, first_name""",
                    (snap["id"],),
                ).fetchall()
                if contribs:
                    bits.append("<h3>Who gave</h3>")
                    body = ["<tr><th>Name</th><th>Type</th><th>Date</th><th class='num'>Amount</th></tr>"]
                    for item in contribs:
                        label = esc(item["display_name"])
                        if item["from_candidate"]:
                            label += " <span class='note'>(from candidate)</span>"
                        body.append(
                            f"<tr><td>{label}</td><td>{esc(item['item_type'] or '')}</td>"
                            f"<td>{esc(item['occurred_on'] or '—')}</td>"
                            f"<td class='num'>{dollars(item['amount'])}</td></tr>"
                        )
                    bits.append(f"<table>{''.join(body)}</table>")
                spends = q(
                    """SELECT display_name, purpose, occurred_on, amount
                       FROM finance_line_items
                       WHERE snapshot_id=? AND direction='expenditure'
                       ORDER BY amount DESC, last_name""",
                    (snap["id"],),
                ).fetchall()
                if spends:
                    bits.append("<h3>Spent on</h3>")
                    body = ["<tr><th>Payee</th><th>Purpose</th><th>Date</th><th class='num'>Amount</th></tr>"]
                    for item in spends:
                        body.append(
                            f"<tr><td>{esc(item['display_name'])}</td><td>{esc(item['purpose'] or '')}</td>"
                            f"<td>{esc(item['occurred_on'] or '—')}</td>"
                            f"<td class='num'>{dollars(item['amount'])}</td></tr>"
                        )
                    bits.append(f"<table>{''.join(body)}</table>")

        if issue_rows and years_in:
            bits.append("<h2>What they have said</h2>")
            bits.append("<p class='note'>Each cell is a source in that year. A dash means we do not have one. Click through for the quote.</p>")
            head = "<tr><th>Issue</th>" + "".join(f"<th>{y}</th>" for y in years_in) + "</tr>"
            mrows = [head]
            for slug, iname in issue_rows:
                cells = f"<td><a href='{esc(issue_href(slug, None, '../'))}'>{esc(iname)}</a></td>"
                for y in years_in:
                    hits = [a for a in answers if a["issue_slug"] == slug and a["q_year"] == y]
                    if not hits:
                        cells += "<td class='empty'>—</td>"
                    else:
                        label = hits[0]["stance"].upper() if hits[0]["stance"] else "said"
                        cells += f"<td><a href='#i-{esc(slug)}-{y}-{hits[0]['id']}'>{esc(label)}</a></td>"
                mrows.append(f"<tr>{cells}</tr>")
            bits.append(f"<table class='matrix'>{''.join(mrows)}</table>")

            current = None
            for a in answers:
                if a["issue_slug"] != current:
                    bits.append(f"<h2>{esc(a['issue_name'])}</h2>")
                    current = a["issue_slug"]
                bits.append(f"<div class='card' id='i-{esc(a['issue_slug'])}-{a['q_year']}-{a['id']}'>")
                bits.append(
                    f"<div class='meta'><a href='../{a['q_year']}.html'>{a['q_year']}</a> · "
                    f"{esc(kind_label(a['q_kind']))} {stance_html(a['stance'])}</div>"
                )
                bits.append(f"<h3>{esc(a['prompt'])}</h3>")
                bits.append(quote_block(a["verbatim"]))
                bits.append(f"<p class='note'><a href='{esc(a['source_url'])}'>{esc(a['source_title'])}</a></p>")
                bits.append("</div>")
        else:
            bits.append("<p class='empty'>No sourced answers on file yet.</p>")

        if appearances:
            bits.append("<h2>Forums</h2><ul>")
            for a in appearances:
                flag = "attended" if a["attended"] == 1 else "did not attend" if a["attended"] == 0 else "unknown"
                rec = f' · <a href="{esc(a["recording_url"])}">recording</a>' if a["recording_url"] else ""
                bits.append(f"<li>{esc(a['starts_on'])} {esc(a['name'])} — {flag}{rec}</li>")
            bits.append("</ul>")

        latest = cands[0]["year"] if cands else None
        if any(c["year"] == 2026 for c in cands):
            bits.insert(
                1,
                f"<p class='print-hint'><a href='../print/{esc(p['slug'])}.html'>Print this candidate (one letter-size sheet)</a></p>",
            )
        (OUT / "people" / f"{p['slug']}.html").write_text(
            page(p["full_name"], "\n".join(bits), prefix="../", year=latest),
            encoding="utf-8",
        )

    # forums / measures / sources / about remain available, not in primary nav
    ev_html = ["<h1>Forums</h1>", "<p>The calendar behind the year pages. Attendance only when a published source named who showed.</p>"]
    all_events = q(
        """SELECT e.*, o.name AS host FROM events e
           LEFT JOIN organizations o ON o.id=e.host_org_id ORDER BY e.starts_on DESC"""
    ).fetchall()
    cur_y = None
    for e in all_events:
        y = int(str(e["starts_on"])[:4])
        if y != cur_y:
            ev_html.append(f"<h2>{y}</h2>")
            cur_y = y
        rec = f' · <a href="{esc(e["recording_url"])}">recording</a>' if e["recording_url"] else ""
        ev_html.append(f"<h3>{esc(e['name'])}</h3>")
        ev_html.append(f"<p>{esc(e['starts_on'])} · {esc(e['venue'] or 'venue not recorded')} · {esc(e['host'] or '')}{rec}</p>")
        if e["notes"]:
            ev_html.append(f"<p class='note'>{esc(e['notes'])}</p>")
        apps = q(
            """SELECT p.full_name, p.slug, a.attended FROM event_appearances a
               JOIN people p ON p.id=a.person_id WHERE a.event_id=? ORDER BY p.sort_name""",
            (e["id"],),
        ).fetchall()
        if apps:
            ev_html.append("<ul>")
            for a in apps:
                flag = "attended" if a["attended"] == 1 else "did not attend" if a["attended"] == 0 else "unknown"
                ev_html.append(f"<li><a href='{esc(person_href(a['slug']))}'>{esc(a['full_name'])}</a> — {flag}</li>")
            ev_html.append("</ul>")
    (OUT / "forums.html").write_text(page("Forums", "\n".join(ev_html)), encoding="utf-8")

    meas_html = ["<h1>City measures</h1>"]
    for year in YEARS:
        meas_html.append(f"<h2>{year}</h2>")
        meas_html.append(measure_cards(year))
    (OUT / "measures.html").write_text(page("Measures", "\n".join(meas_html)), encoding="utf-8")

    sources = q(
        """SELECT s.*, o.name AS org FROM sources s
           LEFT JOIN organizations o ON o.id=s.org_id
           ORDER BY s.year DESC, s.published_on DESC, s.title"""
    ).fetchall()
    src_rows = ["<tr><th>Year</th><th>Kind</th><th>Source</th></tr>"]
    for s in sources:
        src_rows.append(
            f"<tr><td>{s['year'] or ''}</td><td>{esc(s['kind'])}</td>"
            f"<td><a href='{esc(s['url'])}'>{esc(s['title'])}</a></td></tr>"
        )
    (OUT / "sources.html").write_text(
        page("Sources", f"<h1>Sources</h1><p>The catalog. Quoted claims live on people and issue pages.</p><table>{''.join(src_rows)}</table>"),
        encoding="utf-8",
    )

    qn_html = [
        "<h1>Questionnaires</h1>",
        "<p class='lede'>Written candidate Q&amp;A we have located. Full verbatim is ingested only when we copied it into the database (BRL, Boulder Beat). Everything else is linked, not scored.</p>",
        "<p>The Chamber does send questions every cycle; the 2025 extended-response PDF is the one we have as a file. PLAN used a questionnaire for 2025 endorsements and did not publish the dump on the endorsement page. Open Boulder published 2025 PDFs for eight of eleven candidates. Better Boulder co-hosted the 2025 VOTES! forum with PLAN and Open Boulder (first year of that collaboration).</p>",
    ]
    qn_rows = q(
        """SELECT s.year, s.title, s.url, s.kind, s.notes, o.name AS org
           FROM sources s LEFT JOIN organizations o ON o.id=s.org_id
           WHERE s.kind='questionnaire'
           ORDER BY s.year DESC, s.title"""
    ).fetchall()
    qn_html.append("<table><tr><th>Year</th><th>Source</th></tr>")
    for s in qn_rows:
        org = f"{esc(s['org'])} · " if s["org"] else ""
        note = f"<div class='meta'>{esc(s['notes'])}</div>" if s["notes"] else ""
        qn_html.append(
            f"<tr><td>{s['year'] or ''}</td><td>{org}<a href='{esc(s['url'])}'>{esc(s['title'])}</a>{note}</td></tr>"
        )
    qn_html.append("</table>")
    qn_html.append(
        "<p class='note'>Forum videos, including YouTube, live on the <a href='forums.html'>forums</a> page. "
        "We do not invent spoken quotes from a journalist’s grouping or an auto-transcript.</p>"
    )
    (OUT / "questionnaires.html").write_text(page("Questionnaires", "\n".join(qn_html)), encoding="utf-8")

    # ----- print packet: one letter-size sheet per 2026 candidate -----
    def print_sheet(row, office: str) -> str:
        answers = q(
            """SELECT a.verbatim, a.stance, q.prompt, q.year AS q_year, q.kind AS q_kind,
                      COALESCE(q.issue_slug,'other') AS issue_slug,
                      COALESCE(i.name,'This race / other') AS issue_name,
                      s.title AS source_title, s.url AS source_url
               FROM answers a
               JOIN questions q ON q.id=a.question_id
               JOIN sources s ON s.id=a.source_id
               LEFT JOIN issues i ON i.slug=q.issue_slug
               WHERE a.person_id=?
               ORDER BY q.year DESC, a.id""",
            (row["person_id"],),
        ).fetchall()
        cands = q(
            """SELECT c.*, e.year, o.name AS office
               FROM candidacies c
               JOIN races r ON r.id=c.race_id
               JOIN elections e ON e.id=r.election_id
               JOIN offices o ON o.id=r.office_id
               WHERE c.person_id=? ORDER BY e.year DESC""",
            (row["person_id"],),
        ).fetchall()
        flags = []
        if row["is_incumbent"]:
            flags.append("incumbent")
        if row["matching_funds"]:
            flags.append("matching funds")
        flag_txt = f" · {esc(', '.join(flags))}" if flags else ""
        site = (
            f"<p><a href='{esc(row['campaign_url'])}'>{esc(row['campaign_url'])}</a></p>"
            if row["campaign_url"]
            else ""
        )
        bits = [
            f"<p class='print-hint'>File → Print. One letter-size sheet. Not an endorsement.</p>",
            f"<h1>{esc(row['full_name'])}</h1>",
            f"<p class='lede'>2026 {esc(office)}{flag_txt}</p>",
            site,
            "<h2>Campaigns</h2>",
        ]
        tbody = ["<tr><th>Year</th><th>Office</th><th>Outcome</th></tr>"]
        for c in cands:
            tbody.append(
                f"<tr><td>{c['year']}</td><td>{esc(c['office'])}</td><td>{esc(c['status'])}</td></tr>"
            )
        bits.append(f"<table>{''.join(tbody)}</table>")
        if answers:
            years_in = sorted({a["q_year"] for a in answers if a["q_year"]}, reverse=True)
            issues = []
            seen = set()
            for a in answers:
                if a["issue_slug"] not in seen and a["issue_slug"] != "other":
                    seen.add(a["issue_slug"])
                    issues.append((a["issue_slug"], a["issue_name"]))
            if issues and years_in:
                bits.append("<h2>What they have said</h2>")
                head = "<tr><th>Issue</th>" + "".join(f"<th>{y}</th>" for y in years_in) + "</tr>"
                mrows = [head]
                for slug, iname in issues:
                    cells = f"<td>{esc(iname)}</td>"
                    for y in years_in:
                        hits = [a for a in answers if a["issue_slug"] == slug and a["q_year"] == y]
                        if not hits:
                            cells += "<td class='empty'>—</td>"
                        else:
                            label = hits[0]["stance"].upper() if hits[0]["stance"] else "said"
                            cells += f"<td>{esc(label)}</td>"
                    mrows.append(f"<tr>{cells}</tr>")
                bits.append(f"<table class='matrix'>{''.join(mrows)}</table>")
            bits.append("<h2>Three quotes</h2>")
            used_issues = set()
            n = 0
            for a in answers:
                if a["issue_slug"] in used_issues:
                    continue
                used_issues.add(a["issue_slug"])
                bits.append(
                    f"<div class='card'><div class='meta'>{a['q_year']} · {esc(a['issue_name'])} "
                    f"{stance_html(a['stance'])}</div>"
                    f"<h3>{esc(a['prompt'])}</h3>{quote_block(a['verbatim'])}"
                    f"<p class='note'><a href='{esc(a['source_url'])}'>{esc(a['source_title'])}</a></p></div>"
                )
                n += 1
                if n >= 3:
                    break
            if n == 0:
                bits.append('<p class="empty">No sourced quotes on file yet.</p>')
        else:
            bits.append('<p class="empty">No sourced answers on file yet this cycle.</p>')
        money_flag = "yes" if row["matching_funds"] else "not marked on the clerk candidate list"
        snap = finance_for(row["person_id"], 2026)
        bits.append("<h2>Money</h2>")
        if snap:
            n_donors = q(
                """SELECT COUNT(*) FROM finance_line_items
                   WHERE snapshot_id=? AND direction='contribution'""",
                (snap["id"],),
            ).fetchone()[0]
            bits.append(
                f"<p>Raised {dollars(snap['contributions'])} · spent {dollars(snap['expenditures'])} · "
                f"matching received {dollars(snap['matching_received'])} · "
                f"{n_donors} contribution line{'' if n_donors == 1 else 's'} "
                f"(as of {esc(snap['reported_on'])}, {esc(snap['committee_name'])}). "
                f"Clerk matching-funds flag: {money_flag}. Not TRACER.</p>"
            )
            if snap["notes"]:
                bits.append(f"<p class='note'>{esc(snap['notes'])}</p>")
        else:
            bits.append(
                f"<p>Matching funds: {money_flag}. Filings: "
                f"<a href='https://webapps.bouldercolorado.gov/election/committeeFilings.php'>city clerk app</a>.</p>"
            )
        bits.append(
            f"<p class='note'><a href='../people/{esc(row['slug'])}.html'>Full dossier</a> · "
            f"<a href='../2026.html'>2026 ballot</a></p>"
        )
        return page(f"Print · {row['full_name']}", "\n".join(bits), prefix="../", year=2026)

    print_index = [
        "<h1>Print packet</h1>",
        "<p class='lede'>One letter-size sheet per 2026 candidate: timeline, the issue grid, three quotes, and the clerk’s raised / spent / matching totals. Print from the browser. Later in the race, forums often restrict who is invited using fundraising thresholds.</p>",
        "<p class='print-hint'>Open a sheet, then File → Print. No JavaScript.</p>",
        "<h2>Mayor</h2>",
    ]
    for r in candidates_for(2026, "mayor"):
        (OUT / "print" / f"{r['slug']}.html").write_text(print_sheet(r, "mayor"), encoding="utf-8")
        flags = []
        if r["is_incumbent"]:
            flags.append("incumbent")
        if r["matching_funds"]:
            flags.append("matching funds")
        extra = f" · {esc(', '.join(flags))}" if flags else ""
        snap = finance_for(r["person_id"], 2026)
        raised = f" · raised {dollars(snap['contributions'])}" if snap else ""
        print_index.append(
            f"<div class='card'><h3><a href='{esc(r['slug'])}.html'>{esc(r['full_name'])}</a>{extra}</h3>"
            f"<div class='meta'><a href='{esc(r['slug'])}.html'>print sheet</a>{raised}</div></div>"
        )
    print_index.append("<h2>City council</h2>")
    for r in candidates_for(2026, "council"):
        (OUT / "print" / f"{r['slug']}.html").write_text(print_sheet(r, "city council"), encoding="utf-8")
        flags = []
        if r["is_incumbent"]:
            flags.append("incumbent")
        if r["matching_funds"]:
            flags.append("matching funds")
        extra = f" · {esc(', '.join(flags))}" if flags else ""
        snap = finance_for(r["person_id"], 2026)
        raised = f" · raised {dollars(snap['contributions'])}" if snap else ""
        print_index.append(
            f"<div class='card'><h3><a href='{esc(r['slug'])}.html'>{esc(r['full_name'])}</a>{extra}</h3>"
            f"<div class='meta'><a href='{esc(r['slug'])}.html'>print sheet</a>{raised}</div></div>"
        )
    (OUT / "print" / "index.html").write_text(
        page("Print packet", "\n".join(print_index), prefix="../", year=2026),
        encoding="utf-8",
    )

    def bond_people(stance: str | None = None):
        sql = """SELECT p.full_name, p.slug, a.stance, a.verbatim, s.url AS source_url, s.title AS source_title
                 FROM answers a
                 JOIN people p ON p.id=a.person_id
                 JOIN questions q ON q.id=a.question_id
                 JOIN sources s ON s.id=a.source_id
                 WHERE q.issue_slug='bond' AND q.year=2026"""
        args: list = []
        if stance:
            sql += " AND a.stance=?"
            args.append(stance)
        sql += " ORDER BY p.sort_name"
        return q(sql, args).fetchall()

    def bond_cards(rows, prefix=""):
        if not rows:
            return '<p class="empty">No sourced bond answers yet.</p>'
        src = rows[0]
        bits = [f"<p class='note'><a href='{esc(src['source_url'])}'>{esc(src['source_title'])}</a></p>"]
        for r in rows:
            bits.append(
                f"<div class='card'><h3><a href='{esc(person_href(r['slug'], prefix))}'>{esc(r['full_name'])}</a> "
                f"{stance_html(r['stance'])}</h3></div>"
            )
        return "\n".join(bits)

    find_home = [
        "<h1>What do you care about?</h1>",
        "<p class='lede'>Answer one or two questions. You get the candidates’ sourced answers — not a score, not an endorsement.</p>",
        "<h2>1. The $400 million rec and safety bond</h2>",
        "<p>This is the clearest divide in the 2026 field so far (BRL, Aug 30).</p>",
        "<a class='choice' href='find/bond-yes.html'>I support the bond<span class='meta'>See who is with you</span></a>",
        "<a class='choice' href='find/bond-no.html'>I oppose the bond<span class='meta'>See who is with you</span></a>",
        "<a class='choice' href='find/bond.html'>Show everyone<span class='meta'>Yes, no, and who has not been quoted</span></a>",
        "<h2>2. Housing</h2>",
        "<a class='choice' href='issues/housing-2026.html'>What have they said about housing?<span class='meta'>This year’s field, plus earlier answers from people who ran before</span></a>",
        "<h2>3. Homelessness</h2>",
        "<a class='choice' href='issues/homelessness-2026.html'>Camping, shelter, and services</a>",
        "<h2>4. The airport</h2>",
        "<a class='choice' href='issues/airport-2026.html'>FAA grants that could lock the airport open</a>",
        "<h2>Or skip the questions</h2>",
        "<p><a href='2026.html'>The 2026 ballot</a> · <a href='people.html'>A person</a> · "
        "<a href='print/index.html'>Print a sheet</a> · <a href='finance.html'>Who has raised money</a></p>",
        "<p class='note'>No JavaScript. Large type. A dash means we do not have it.</p>",
    ]
    (OUT / "find.html").write_text(page("Find", "\n".join(find_home), year=2026), encoding="utf-8")

    yes_rows = bond_people("yes")
    no_rows = bond_people("no")
    named = {r["person_id"] if "person_id" in r.keys() else None for r in []}
    named_slugs = {r["slug"] for r in yes_rows} | {r["slug"] for r in no_rows}
    ballot_2026 = list(candidates_for(2026, "mayor")) + list(candidates_for(2026, "council"))
    silent = [r for r in ballot_2026 if r["slug"] not in named_slugs]

    (OUT / "find" / "bond-yes.html").write_text(
        page(
            "Support the bond",
            "<p class='crumb'><a href='../find.html'>Find</a></p>"
            "<h1>They support the $400 million bond</h1>"
            "<p class='lede'>BRL grouped these names as supporting the rec/safety bond. Not a score.</p>"
            + bond_cards(yes_rows, "../")
            + "<p><a class='choice' href='bond-no.html'>See who opposes it</a>"
            "<a class='choice' href='../issues/housing-2026.html'>Also: housing</a></p>",
            prefix="../",
            year=2026,
        ),
        encoding="utf-8",
    )
    (OUT / "find" / "bond-no.html").write_text(
        page(
            "Oppose the bond",
            "<p class='crumb'><a href='../find.html'>Find</a></p>"
            "<h1>They oppose the $400 million bond</h1>"
            "<p class='lede'>BRL grouped these names as opposing the rec/safety bond, arguing voters lack enough information on how the money would be spent.</p>"
            + bond_cards(no_rows, "../")
            + "<p><a class='choice' href='bond-yes.html'>See who supports it</a>"
            "<a class='choice' href='../issues/housing-2026.html'>Also: housing</a></p>",
            prefix="../",
            year=2026,
        ),
        encoding="utf-8",
    )
    silent_html = ""
    if silent:
        silent_html = "<h2>Not named on either list</h2><p class='note'>BRL did not put these names on the yes or no side. We do not invent a stance.</p>" + "".join(
            f"<div class='card'><h3><a href='{esc(person_href(r['slug'], '../'))}'>{esc(r['full_name'])}</a></h3><div class='meta'>—</div></div>"
            for r in silent
        )
    (OUT / "find" / "bond.html").write_text(
        page(
            "The $400 million bond",
            "<p class='crumb'><a href='../find.html'>Find</a></p>"
            "<h1>The $400 million rec and safety bond</h1>"
            "<p class='lede'>Clearest divide in the 2026 field so far. Source: BRL, Aug 30 2026.</p>"
            "<h2>Support</h2>" + bond_cards(yes_rows, "../")
            + "<h2>Oppose</h2>" + bond_cards(no_rows, "../")
            + silent_html,
            prefix="../",
            year=2026,
        ),
        encoding="utf-8",
    )

    fin_rows = q(
        """SELECT f.id, p.full_name, p.slug, f.committee_name, f.committee_kind, f.contributions,
                  f.expenditures, f.matching_received, f.cash_on_hand, f.reported_on, f.notes,
                  f.reports_url, f.person_id, s.url AS source_url, s.title AS source_title
           FROM finance_snapshots f
           LEFT JOIN people p ON p.id=f.person_id
           JOIN sources s ON s.id=f.source_id
           WHERE f.year=2026
           ORDER BY f.contributions DESC, COALESCE(p.sort_name, f.committee_name)"""
    ).fetchall()
    fin_html = [
        "<h1>Campaign money — 2026</h1>",
        "<p class='lede'>City of Boulder committee filings, not TRACER. Retrieved 2026-09-01 from the live clerk app. $0 is a filed zero, not a missing record. Cents come from the latest CandE statement; the clerk’s summary table rounds to dollars.</p>",
        "<p class='note'>Past-year dollars: the live app only serves 2026. Historical filings sit in the city’s "
        "<a href='https://documents.bouldercolorado.gov/WebLink/Browse.aspx?id=59131'>Laserfiche archive</a> "
        "(cookie/JS). This pass could not list that folder. Matching-funds asterisks on the clerk candidate list are separate from the matching-received column here.</p>",
    ]
    candidates = [r for r in fin_rows if r["committee_kind"] == "official_candidate" and r["person_id"]]
    cand_ids = {r["id"] for r in candidates}
    other = [r for r in fin_rows if r["id"] not in cand_ids]
    if candidates:
        fin_html.append(f"<p class='note'><a href='{esc(candidates[0]['source_url'])}'>{esc(candidates[0]['source_title'])}</a></p>")
        body = [
            "<tr><th>Candidate</th><th>Committee</th><th class='num'>Raised</th>"
            "<th class='num'>Spent</th><th class='num'>Matching</th>"
            "<th class='num'>Donors</th><th>As of</th></tr>"
        ]
        for r in candidates:
            n_donors = q(
                """SELECT COUNT(*) FROM finance_line_items
                   WHERE snapshot_id=? AND direction='contribution'""",
                (r["id"],),
            ).fetchone()[0]
            body.append(
                f"<tr><td><a href='{esc(person_href(r['slug']))}'>{esc(r['full_name'])}</a></td>"
                f"<td>{esc(r['committee_name'])}</td>"
                f"<td class='num'>{dollars(r['contributions'])}</td>"
                f"<td class='num'>{dollars(r['expenditures'])}</td>"
                f"<td class='num'>{dollars(r['matching_received'])}</td>"
                f"<td class='num'>{n_donors}</td>"
                f"<td>{esc(r['reported_on'] or '—')}</td></tr>"
            )
        fin_html.append(f"<table>{''.join(body)}</table>")
        noted = [r for r in candidates if r["notes"]]
        if noted:
            fin_html.append("<ul class='note'>")
            for r in noted:
                fin_html.append(f"<li><a href='{esc(person_href(r['slug']))}'>{esc(r['full_name'])}</a> — {esc(r['notes'])}</li>")
            fin_html.append("</ul>")

    cross = q(
        """SELECT giver.full_name AS giver, giver.slug AS giver_slug,
                  recv.full_name AS recv, recv.slug AS recv_slug,
                  li.amount, li.occurred_on, li.item_type
           FROM finance_line_items li
           JOIN people giver ON giver.id=li.donor_person_id
           JOIN finance_snapshots fs ON fs.id=li.snapshot_id
           JOIN people recv ON recv.id=fs.person_id
           WHERE li.direction='contribution' AND li.year=2026
             AND li.donor_person_id IS NOT NULL
             AND li.donor_person_id != fs.person_id
           ORDER BY recv.sort_name, giver.sort_name"""
    ).fetchall()
    if cross:
        fin_html.append("<h2>People in this database who gave to a 2026 candidate</h2>")
        fin_html.append(
            "<p class='note'>Only names that already exist as people in this map (candidates, officeholders). "
            "Everyone else is on the candidate’s dossier. Not a complete donor graph.</p>"
        )
        body = ["<tr><th>Gave</th><th>To</th><th>Type</th><th>Date</th><th class='num'>Amount</th></tr>"]
        for r in cross:
            body.append(
                f"<tr><td><a href='{esc(person_href(r['giver_slug']))}'>{esc(r['giver'])}</a></td>"
                f"<td><a href='{esc(person_href(r['recv_slug']))}'>{esc(r['recv'])}</a></td>"
                f"<td>{esc(r['item_type'] or '')}</td>"
                f"<td>{esc(r['occurred_on'] or '—')}</td>"
                f"<td class='num'>{dollars(r['amount'])}</td></tr>"
            )
        fin_html.append(f"<table>{''.join(body)}</table>")

    if other:
        fin_html.append("<h2>Other 2026 committees</h2>")
        fin_html.append(
            "<p class='note'>Ballot-measure and unofficial committees, plus any official committee whose candidate is not on the certified clerk list.</p>"
        )
        body = ["<tr><th>Committee</th><th>Kind</th><th class='num'>Raised</th><th class='num'>Spent</th><th>As of</th></tr>"]
        for r in other:
            kind = (r["committee_kind"] or "").replace("_", " ")
            body.append(
                f"<tr><td>{esc(r['committee_name'])}</td><td>{esc(kind)}</td>"
                f"<td class='num'>{dollars(r['contributions'])}</td>"
                f"<td class='num'>{dollars(r['expenditures'])}</td>"
                f"<td>{esc(r['reported_on'] or '—')}</td></tr>"
            )
        fin_html.append(f"<table>{''.join(body)}</table>")
    fin_html.append("<p><a href='https://webapps.bouldercolorado.gov/election/committeeFilings.php'>Open the clerk app</a> to read each statement.</p>")
    (OUT / "finance.html").write_text(page("Money", "\n".join(fin_html), year=2026), encoding="utf-8")

    about = """
    <h1>About</h1>
    <p>Boulder Votes is a map of City of Boulder elections for people who have to mark a ballot, especially older voters. It is not a feed and not a scorecard.</p>
    <h2>How to use it</h2>
    <ul>
      <li><strong>Zoom a year</strong> — the year rail. You see that year’s ballot: people as cards, measures, the issues they have actually answered.</li>
      <li><strong>Zoom a person</strong> — the dossier. A grid of issues across the years they ran. Returning candidates keep one page.</li>
      <li><strong>Zoom an issue</strong> — pick the year. You see the people on that ballot. Earlier answers from returning candidates are labelled as earlier.</li>
      <li><strong>Find</strong> — two or three questions. You land on sourced answers, not a score.</li>
      <li><strong>Print</strong> — one letter-size sheet per 2026 candidate. File → Print.</li>
    </ul>
    <p>Years on the rail now run 2017–2026. 2015 and earlier are out of scope for now.</p>
    <p>A number without a source is not published. Two quotes are never averaged. A dash is a dash. We do not score candidates.</p>
    <p>Municipal campaign-finance filings are with the <a href="https://bouldercolorado.gov/elections/election-committee-filings">city clerk</a>, not TRACER. 2026 raised / spent / matching totals and itemized donors live on each candidate’s page and on <a href="finance.html">Money</a>. $0 is a filed zero. Past-year dollars are not copied (the live clerk app only serves 2026; Laserfiche is a JS archive).</p>
    <p>No JavaScript. Large type. Print unfolds the folded answers.</p>
    """
    (OUT / "about.html").write_text(page("About", about), encoding="utf-8")

    # keep old race URLs from breaking
    (OUT / "2026-mayor.html").write_text(
        page("2026 mayor", "<h1>2026 mayor</h1><p>Moved onto the <a href='2026.html'>2026 ballot</a>.</p>", year=2026),
        encoding="utf-8",
    )
    (OUT / "2026-council.html").write_text(
        page("2026 council", "<h1>2026 council</h1><p>Moved onto the <a href='2026.html'>2026 ballot</a>.</p>", year=2026),
        encoding="utf-8",
    )

    print(f"wrote {len(list(OUT.rglob('*.html')))} html files into {OUT}")
    con.close()


if __name__ == "__main__":
    main()
