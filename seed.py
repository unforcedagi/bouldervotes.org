#!/usr/bin/env python3
"""Load verified seed data into data/bouldervotes.db.

Claims here are sourced. If a field is missing, it is missing — not guessed.
Re-run anytime: this rebuilds the database from scratch.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "bouldervotes.db"
SCHEMA = ROOT / "schema.sql"


def slug(name: str) -> str:
    return (
        name.lower()
        .replace(".", "")
        .replace("'", "")
        .replace("—", "-")
        .replace(" ", "-")
    )


def sort_name(full: str) -> str:
    parts = full.split()
    if len(parts) == 1:
        return full
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def main() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA.read_text())
    cur = con.cursor()

    def add_person(full: str, notes: str | None = None) -> int:
        cur.execute(
            "INSERT INTO people (slug, full_name, sort_name, notes) VALUES (?,?,?,?)",
            (slug(full), full, sort_name(full), notes),
        )
        return cur.lastrowid  # type: ignore[return-value]

    def add_org(name: str, kind: str, website: str | None = None, notes: str | None = None) -> int:
        cur.execute(
            "INSERT INTO organizations (slug, name, kind, website, notes) VALUES (?,?,?,?,?)",
            (slug(name), name, kind, website, notes),
        )
        return cur.lastrowid  # type: ignore[return-value]

    def add_source(url: str, title: str, kind: str, year: int | None = None,
                   org_id: int | None = None, published_on: str | None = None,
                   notes: str | None = None) -> int:
        cur.execute(
            """INSERT INTO sources (url, title, published_on, org_id, kind, year, notes)
               VALUES (?,?,?,?,?,?,?)""",
            (url, title, published_on, org_id, kind, year, notes),
        )
        return cur.lastrowid  # type: ignore[return-value]

    # --- organizations ---
    org_city = add_org("City of Boulder", "government", "https://bouldercolorado.gov")
    org_county = add_org("Boulder County Clerk and Recorder", "government", "https://bouldercounty.gov/elections")
    org_brl = add_org("Boulder Reporting Lab", "newspaper", "https://boulderreportinglab.org")
    org_camera = add_org("Daily Camera", "newspaper", "https://www.dailycamera.com")
    org_weekly = add_org("Boulder Weekly", "newspaper", "https://www.boulderweekly.com")
    org_chamber = add_org("Boulder Chamber", "forum_host", "https://www.boulderchamber.com")
    org_lwv = add_org("League of Women Voters of Boulder County", "civic", "https://www.lwvbc.org")
    org_progressives = add_org("Boulder Progressives", "advocacy", None)
    org_plan = add_org("PLAN-Boulder County", "advocacy", None)
    org_open = add_org("Open Boulder", "advocacy", None)
    org_elevated = add_org("Boulder Elevated", "advocacy", None)
    org_axios = add_org("Axios Boulder", "newspaper", "https://www.axios.com/local/boulder")
    add_org("Boulder Weekly archives", "newspaper", "https://archives.boulderweekly.com")

    # --- offices ---
    cur.execute(
        "INSERT INTO offices (slug, name, jurisdiction, typical_seats, term_years, notes) VALUES (?,?,?,?,?,?)",
        (
            "mayor",
            "Mayor of Boulder",
            "City of Boulder",
            1,
            4,
            "Directly elected by ranked-choice voting since 2023. Charter amendment passed 2020 (~78%). 2023 and 2025 municipal winners serve three-year terms while the city moves to even-year elections; 2026 mayor is a two-year term (Brockett to Daily Camera, Aug 19 2026).",
        ),
    )
    mayor_office = cur.lastrowid
    cur.execute(
        "INSERT INTO offices (slug, name, jurisdiction, typical_seats, term_years, notes) VALUES (?,?,?,?,?,?)",
        (
            "council",
            "Boulder City Council",
            "City of Boulder",
            8,
            4,
            "Nine-member council including the mayor, all at-large. Council seats (not mayor) are plurality: top N vote-getters win. RCV applies only to mayor.",
        ),
    )
    council_office = cur.lastrowid

    # --- elections / races ---
    def add_election(year: int, date: str, notes: str) -> int:
        cur.execute(
            "INSERT INTO elections (year, date, jurisdiction, kind, notes) VALUES (?,?,?,?,?)",
            (year, date, "City of Boulder", "municipal_coordinated", notes),
        )
        return cur.lastrowid  # type: ignore[return-value]

    e2023 = add_election(
        2023, "2023-11-07",
        "First direct mayoral election under ranked-choice voting. Four council seats. Odd-year cycle.",
    )
    e2025 = add_election(
        2025, "2025-11-04",
        "Four council seats, no mayoral race. Last odd-year municipal election before the even-year switch. Winners serve three-year terms.",
    )
    e2026 = add_election(
        2026, "2026-11-03",
        "First even-year municipal election. One mayor (RCV) and five council seats (plurality). Fifth council seat is the vacancy from Mark Wallach's July 23 2026 resignation (charter: resignation before Aug 1 puts the seat on the November ballot).",
    )

    def add_race(election_id: int, office_id: int, seats: int, method: str, notes: str) -> int:
        cur.execute(
            "INSERT INTO races (election_id, office_id, seats_open, voting_method, notes) VALUES (?,?,?,?,?)",
            (election_id, office_id, seats, method, notes),
        )
        return cur.lastrowid  # type: ignore[return-value]

    r2023_mayor = add_race(e2023, mayor_office, 1, "ranked_choice", "Instant runoff. Four candidates.")
    r2023_council = add_race(e2023, council_office, 4, "plurality", "Ten candidates. Automatic recount for 4th/5th.")
    r2025_council = add_race(e2025, council_office, 4, "plurality", "Eleven candidates.")
    r2026_mayor = add_race(e2026, mayor_office, 1, "ranked_choice", "Second RCV mayoral election. Ballot order drawn Aug 25 2026.")
    r2026_council = add_race(e2026, council_office, 5, "plurality", "Thirteen certified candidates for five seats as of the city clerk list dated Aug 26 2026.")

    # --- people ---
    names = [
        "Aaron Brockett",
        "Taishya Adams",
        "Tara Winer",
        "Tina Marquis",
        "Ryan Schuchard",
        "Matt Benjamin",
        "Nicole Speer",
        "Rob Kaplan",
        "Mark Wallach",
        "Lauren Folkerts",
        "Jill Grano",
        "Rachel Rose Isaacson",
        "Benita Duran",
        "Aquiles La Grave",
        "Fred Smith",
        "Jameson Goldstein",
        "Lisa Ann Jacobs",
        "Ryan Jamieson",
        "Lee Gilbert",
        "Jamillah Richmond",
        "Sam Fuqua",
        "Lynn Segal",
        "David Martus",
        "Scott Rendleman",
        "Jennifer Robins",
        "Terri Brncic",
        "Bob Yates",
        "Paul Tweedlie",
        "Waylon Lewis",
        "Silas Atkins",
        "Aaron Gabriel Neyer",
        "Jacques Decalo",
        "Montserrat Palacios",
        "Maxwell Lord",
        "Aaron Stone",
        "Rob Smoke",
    ]
    pid: dict[str, int] = {}
    notes_by_name = {
        "Jennifer Robins": "Appears as Jenny Robins in some 2023/2025 coverage; Jennifer Robins on the 2025 certified results.",
        "Montserrat Palacios": "BRL 2025 questionnaire listed Montserrat Palacios Rodarte; 2025 certified results list Montserrat Palacios.",
        "Maxwell Lord": "BRL listed Max Lord; certified results list Maxwell Lord.",
        "Jill Grano": "Elected 2017; resigned 2019 to become community affairs director for Rep. Joe Neguse. Running again 2026.",
        "Mark Wallach": "Resigned July 23 2026 immediately after the 8-1 airport/FAA-grant vote. Seat vacant until Nov 3 2026.",
        "Aaron Brockett": "Appointed mayor by council 2021; won the first direct RCV mayoral election 2023.",
        "Taishya Adams": "Elected to council 2023; entered the 2026 mayoral race (cannot also run for her council seat).",
        "Sam Fuqua": "Name as certified by the city clerk Aug 2026. Not yet independently biographed in this seed.",
    }
    for n in names:
        pid[n] = add_person(n, notes_by_name.get(n))

    def cand(person: str, race: int, status: str, incumbent: int = 0,
             certified_on: str | None = None, matching: int = 0,
             campaign_url: str | None = None, notes: str | None = None) -> int:
        cur.execute(
            """INSERT INTO candidacies
               (person_id, race_id, status, is_incumbent, certified_on, matching_funds, campaign_url, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (pid[person], race, status, incumbent, certified_on, matching, campaign_url, notes),
        )
        return cur.lastrowid  # type: ignore[return-value]

    # 2023 mayor
    c2023_brockett = cand("Aaron Brockett", r2023_mayor, "elected", 1)
    c2023_yates = cand("Bob Yates", r2023_mayor, "lost", 0, notes="Incumbent councilmember running for mayor.")
    c2023_speer_m = cand("Nicole Speer", r2023_mayor, "lost")
    c2023_tweedlie = cand("Paul Tweedlie", r2023_mayor, "lost")

    # 2023 council
    c2023_winer = cand("Tara Winer", r2023_council, "elected", 1)
    c2023_marquis = cand("Tina Marquis", r2023_council, "elected")
    c2023_adams = cand("Taishya Adams", r2023_council, "elected")
    c2023_schuchard = cand("Ryan Schuchard", r2023_council, "elected")
    c2023_brncic = cand("Terri Brncic", r2023_council, "lost")
    cand("Jennifer Robins", r2023_council, "lost")
    cand("Waylon Lewis", r2023_council, "lost")
    cand("Silas Atkins", r2023_council, "lost")
    cand("Aaron Gabriel Neyer", r2023_council, "lost")
    cand("Jacques Decalo", r2023_council, "lost")

    # 2025 council
    c2025_benjamin = cand("Matt Benjamin", r2025_council, "elected", 1)
    c2025_wallach = cand("Mark Wallach", r2025_council, "elected", 1)
    c2025_speer = cand("Nicole Speer", r2025_council, "elected", 1)
    c2025_kaplan = cand("Rob Kaplan", r2025_council, "elected")
    c2025_robins = cand("Jennifer Robins", r2025_council, "lost")
    c2025_folkerts = cand("Lauren Folkerts", r2025_council, "lost", 1)
    c2025_isaacson = cand("Rachel Rose Isaacson", r2025_council, "lost")
    cand("Montserrat Palacios", r2025_council, "lost")
    cand("Maxwell Lord", r2025_council, "lost")
    cand("Aaron Stone", r2025_council, "lost")
    cand("Rob Smoke", r2025_council, "lost")

    # 2026 mayor — clerk list retrieved 2026-08-26
    c2026_adams_m = cand(
        "Taishya Adams", r2026_mayor, "certified", 0, "2026-08-05",
        campaign_url="https://www.adamsforboulder.com/",
    )
    cand("Fred Smith", r2026_mayor, "certified", 0, "2026-08-10")
    c2026_brockett = cand(
        "Aaron Brockett", r2026_mayor, "certified", 1, "2026-08-11", 1,
        campaign_url="https://brockett4mayor.org/",
        notes="Site is live; copy may still read like the 2023 cycle in places.",
    )
    cand("Jameson Goldstein", r2026_mayor, "certified", 0, "2026-08-24")
    cand("Lisa Ann Jacobs", r2026_mayor, "certified", 0, "2026-08-24")
    c2026_lagrave = cand("Aquiles La Grave", r2026_mayor, "certified", 0, "2026-08-24")

    # 2026 council
    c2026_isaacson = cand(
        "Rachel Rose Isaacson", r2026_council, "certified", 0, "2026-08-04", 1,
        campaign_url="https://www.rachelrose4boulder.com/",
    )
    c2026_winer = cand(
        "Tara Winer", r2026_council, "certified", 1, "2026-08-05", 1,
        campaign_url="https://www.taraforboulder.com/",
    )
    c2026_schuchard = cand("Ryan Schuchard", r2026_council, "certified", 1, "2026-08-06")
    c2026_grano = cand(
        "Jill Grano", r2026_council, "certified", 0, "2026-08-06",
        campaign_url="https://www.jillforcouncil.com/",
    )
    c2026_duran = cand("Benita Duran", r2026_council, "certified", 0, "2026-08-07")
    cand("Ryan Jamieson", r2026_council, "certified", 0, "2026-08-10")
    cand("Lee Gilbert", r2026_council, "certified", 0, "2026-08-17")
    c2026_marquis = cand("Tina Marquis", r2026_council, "certified", 1, "2026-08-17", 1)
    cand("Jamillah Richmond", r2026_council, "certified", 0, "2026-08-17")
    cand("Sam Fuqua", r2026_council, "certified", 0, "2026-08-18")
    cand("Lynn Segal", r2026_council, "certified", 0, "2026-08-20")
    cand("David Martus", r2026_council, "certified", 0, "2026-08-24")
    cand("Scott Rendleman", r2026_council, "certified", 0, "2026-08-24")

    cid = {
        "2023_brockett": c2023_brockett,
        "2023_yates": c2023_yates,
        "2023_speer_m": c2023_speer_m,
        "2023_tweedlie": c2023_tweedlie,
        "2023_winer": c2023_winer,
        "2023_marquis": c2023_marquis,
        "2023_adams": c2023_adams,
        "2023_schuchard": c2023_schuchard,
        "2023_brncic": c2023_brncic,
        "2025_benjamin": c2025_benjamin,
        "2025_wallach": c2025_wallach,
        "2025_speer": c2025_speer,
        "2025_kaplan": c2025_kaplan,
        "2025_robins": c2025_robins,
        "2025_folkerts": c2025_folkerts,
        "2025_isaacson": c2025_isaacson,
        "2026_adams_m": c2026_adams_m,
        "2026_brockett": c2026_brockett,
        "2026_lagrave": c2026_lagrave,
        "2026_isaacson": c2026_isaacson,
        "2026_winer": c2026_winer,
        "2026_schuchard": c2026_schuchard,
        "2026_grano": c2026_grano,
        "2026_duran": c2026_duran,
        "2026_marquis": c2026_marquis,
    }

    # --- officeholders (2023 seating onward; not a full historical roster) ---
    holders = [
        ("Aaron Brockett", "mayor", "2023-12-07", None, None, "Directly elected 2023. Previously appointed mayor 2021."),
        ("Taishya Adams", "councilmember", "2023-12-07", "2026-12", None, "Seat on 2026 ballot because she is running for mayor."),
        ("Tara Winer", "councilmember", "2023-12-07", None, None, "Named mayor pro tem Dec 4 2025."),
        ("Tina Marquis", "councilmember", "2023-12-07", None, None, None),
        ("Ryan Schuchard", "councilmember", "2023-12-07", None, None, "Won 4th seat after automatic recount."),
        ("Matt Benjamin", "councilmember", "2021-12", None, None, "Reelected 2025; term runs through 2028. Not on 2026 ballot."),
        ("Nicole Speer", "councilmember", "2021-12", None, None, "Reelected 2025; term runs through 2028. Ran for mayor 2023 (3rd). Not on 2026 ballot."),
        ("Lauren Folkerts", "mayor_pro_tem", "2023-12-07", "2025-12-04", "term_ended", "Lost reelection 2025 (6th). Had been mayor pro tem."),
        ("Mark Wallach", "councilmember", "2019-12", "2026-07-23", "resigned", "Reelected 2025. Resigned July 23 2026 after 8-1 airport vote."),
        ("Rob Kaplan", "councilmember", "2025-12-04", None, None, "Elected 2025. Term through 2028. Not on 2026 ballot."),
    ]
    for person, role, start, end, how, notes in holders:
        office = mayor_office if role == "mayor" else council_office
        cur.execute(
            """INSERT INTO officeholders
               (person_id, office_id, role, term_start, term_end, how_ended, notes)
               VALUES (?,?,?,?,?,?,?)""",
            (pid[person], office, role, start, end, how, notes),
        )

    # --- sources ---
    s_clerk_2026 = add_source(
        "https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates",
        "2026 City of Boulder Mayoral and City Council Candidates",
        "official", 2026, org_city, "2026-08-26",
        "Official certified-candidate list. Matching-funds flags as marked on this page.",
    )
    s_vote_info = add_source(
        "https://bouldercolorado.gov/services/voting-and-election-information",
        "Voting and Election Information | City of Boulder",
        "official", 2026, org_city, None,
        "Election day Nov 3 2026. Filing window Aug 4–24 2026. Links to campaign-finance filings.",
    )
    s_rcv = add_source(
        "https://bouldercolorado.gov/guide/ranked-choice-voting-guide",
        "Ranked Choice Voting Guide | City of Boulder",
        "official", 2026, org_city, None,
        "Nov 3 2026 is the second RCV mayoral election.",
    )
    s_council_page = add_source(
        "https://bouldercolorado.gov/government/city-council",
        "City Council | City of Boulder",
        "official", 2026, org_city, "2026-08-27",
        "Sitting members as of Aug 27 2026. Wallach absent (resigned). Eight names listed.",
    )
    s_2023_results_page = add_source(
        "https://bouldercounty.gov/elections/by-year/2023-election/",
        "2023 Election Results and Information - Boulder County",
        "results", 2023, org_county, None,
        "Recount: Schuchard 14,412 vs Brncic 14,365 originally (47 votes); recount Dec 5–6.",
    )
    s_2023_summary = add_source(
        "https://assets.bouldercounty.gov/wp-content/uploads/2023/12/2023C-Boulder-County-Official-Summary-of-Votes-Recount.pdf",
        "2023 Coordinated Election — Amended Summary of Votes (City of Boulder Council, recount)",
        "results", 2023, org_county, "2023-12-06",
        "Certified council totals used in this database.",
    )
    s_2023_rcv = add_source(
        "https://assets.bouldercounty.gov/wp-content/uploads/2023/11/2023C-Boulder-County-Official-Summary-of-Votes.pdf",
        "2023 Coordinated Election — Official Summary of Votes (RCV mayor)",
        "results", 2023, org_county, "2023-11-29",
        "Certified RCV rounds for mayor.",
    )
    s_2023_enr = add_source(
        "https://electionresults.bouldercounty.gov/ElectionResults2023C/Home/IndexCategory/39.html",
        "Boulder County 2023 Coordinated Election official results (ENR)",
        "results", 2023, org_county, "2023-12-06",
        "Updated after the council recount.",
    )
    s_2025_camera = add_source(
        "https://www.dailycamera.com/2025/12/05/new-boulder-city-council-sworn-in-2/",
        "New Boulder City Council sworn in (Daily Camera)",
        "article", 2025, org_camera, "2025-12-05",
        "Certified vote totals read at Dec 4 2025 seating: Benjamin 20,276; Wallach 17,476; Speer 16,165; Kaplan 15,867. More than 34,000 city ballots.",
    )
    s_2025_clarity = add_source(
        "https://results.enr.clarityelections.com/CO/Boulder/124417/",
        "Boulder County 2025 Coordinated Election results (Clarity ENR)",
        "results", 2025, org_county, "2025-11-26",
        "Full 11-candidate city council totals used in this database.",
    )
    s_2025_guide = add_source(
        "https://boulderreportinglab.org/2025/10/05/boulder-2025-voter-guide-what-to-know-before-election-day-nov-4/",
        "Boulder 2025 Election Guide (Boulder Reporting Lab)",
        "questionnaire", 2025, org_brl, "2025-10-05",
        "All 11 council candidates answered. Six questions. Gold dataset for 2025; several 2026 candidates overlap.",
    )
    s_2025_results_brl = add_source(
        "https://boulderreportinglab.org/2025/11/06/boulder-2025-election-results-voters-reelect-three-incumbents-to-council-and-pass-all-tax-measures/",
        "Boulder 2025 election results (BRL)",
        "article", 2025, org_brl, "2025-11-06",
        "Folkerts 6th, Robins 5th. Progressive vs moderate slate framing.",
    )
    s_2026_brl_caucus = add_source(
        "https://boulderreportinglab.org/2026/06/07/boulder-city-council-candidates-preview-election-year-debates-over-housing-airport-and-wages/",
        "Boulder City Council candidates preview election-year battles over housing, airport and wages",
        "article", 2026, org_brl, "2026-06-07",
        "Raucous Caucus, June 6 2026. Includes binary airport-grant answers for seven then-declared candidates.",
    )
    s_2026_adams = add_source(
        "https://boulderreportinglab.org/2026/08/05/boulder-city-councilmember-taishya-adams-announces-run-for-mayor/",
        "Taishya Adams enters 2026 Boulder mayor’s race (BRL)",
        "article", 2026, org_brl, "2026-08-05",
        "Cannot run for council and mayor in the same election.",
    )
    s_2026_brockett_brl = add_source(
        "https://boulderreportinglab.org/2026/07/28/aaron-brockett-seeks-reelection-as-boulder-mayor-after-turbulent-council-term/",
        "Aaron Brockett seeks reelection as Boulder mayor (BRL)",
        "article", 2026, org_brl, "2026-07-28",
    )
    s_2026_brockett_camera = add_source(
        "https://www.dailycamera.com/2026/08/19/aaron-brockett-boulder-mayor-reelection/",
        "Mayor Aaron Brockett running for re-election (Daily Camera)",
        "article", 2026, org_camera, "2026-08-19",
        "Brockett: 'the final two-year term' — confirms 2026 mayor is a two-year term during the even-year transition.",
    )
    s_2026_isaacson_camera = add_source(
        "https://www.dailycamera.com/2026/08/13/rachel-isaacson-boulder-city-council/",
        "Rachel Rose Isaacson running for Boulder City Council (Daily Camera)",
        "article", 2026, org_camera, "2026-08-13",
    )
    s_wallach_resign_brl = add_source(
        "https://boulderreportinglab.org/2026/07/23/boulder-city-councilmember-mark-wallach-resigns-after-vote-to-keep-municipal-airport-open-indefinitely/",
        "Mark Wallach resigns after airport vote (BRL)",
        "article", 2026, org_brl, "2026-07-23",
    )
    s_wallach_axios = add_source(
        "https://www.axios.com/local/boulder/2026/07/24/boulder-city-council-mark-wallach-resigns",
        "Wallach abruptly resigns from Boulder City Council (Axios)",
        "article", 2026, org_axios, "2026-07-24",
        "Resignation before Aug 1 → seat stays vacant until Nov 3 (city spokesperson Sarah Huntley).",
    )
    s_chamber_forum = add_source(
        "https://business.boulderchamber.com/events-calendar/Details/city-council-candidate-forum-2026-1693343?sourceTypeId=Website",
        "City Council Candidate Forum 2026 — Boulder Chamber",
        "official", 2026, org_chamber, None,
        "Wed Aug 26 2026, 5–8pm, eTown, 1535 Spruce St. First all-qualified-candidates forum of the cycle.",
    )
    s_lwv_2026 = add_source(
        "https://www.lwvbc.org/content.aspx?page_id=22&club_id=629866&module_id=753738",
        "2026 Election — League of Women Voters of Boulder County",
        "official", 2026, org_lwv, None,
        "Points to Vote411.org. Forums TBD as of this seed.",
    )
    s_tara = add_source(
        "https://www.taraforboulder.com/",
        "Tara for Boulder — campaign site",
        "campaign_site", 2026, None, None,
    )
    add_source("https://www.adamsforboulder.com/", "Adams for Boulder — campaign site", "campaign_site", 2026)
    add_source("https://brockett4mayor.org/", "Brockett for Mayor — campaign site", "campaign_site", 2026)
    add_source("https://www.jillforcouncil.com/", "Jill Grano for Council — campaign site", "campaign_site", 2026)
    add_source("https://www.rachelrose4boulder.com/", "Rachel Rose Isaacson — campaign site", "campaign_site", 2026)
    s_brl_votes = add_source(
        "https://boulderreportinglab.org/2026/01/04/boulder-city-council-voting-records-reveal-a-complicated-majority/",
        "Boulder City Council voting records reveal a complicated majority (BRL)",
        "article", 2026, org_brl, "2026-01-04",
        "Vote-tracker analysis of Dec 2023–late 2025. Five-member bloc ~63% of nonunanimous votes.",
    )
    s_cuind = add_source(
        "https://cuindependent.org/2025/11/09/boulders-2025-election-results/",
        "Boulder's 2025 election results (CU Independent)",
        "article", 2025, None, "2025-11-09",
        "Notes the even-year switch: 2023 and 2025 winners serve three-year terms.",
    )
    s_denverpost_rcv = add_source(
        "https://www.denverpost.com/2023/11/09/boulder-mayoral-race-yates-brockett-ranked-choice-voting/",
        "Incumbent pulls ahead of challenger in Boulder mayor’s race (Denver Post)",
        "article", 2023, None, "2023-11-09",
    )

    # --- events ---
    cur.execute(
        """INSERT INTO events (slug, name, starts_on, venue, host_org_id, kind, recording_url, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            "2026-raucous-caucus",
            "Boulder Progressives Raucous Caucus",
            "2026-06-06",
            "Twisted Pine Brewing Company, Boulder",
            org_progressives,
            "caucus",
            None,
            "Unofficial kickoff of the 2026 cycle. Attendees reported by BRL: Tara Winer, Tina Marquis, Benita Duran, Rachel Rose Isaacson, Ryan Schuchard, Jill Grano, Aaron Brockett. Adams did not attend.",
        ),
    )
    ev_caucus = cur.lastrowid
    cur.execute(
        """INSERT INTO events (slug, name, starts_on, venue, host_org_id, kind, recording_url, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            "2026-chamber-forum",
            "Boulder Chamber City Council Candidate Forum",
            "2026-08-26",
            "eTown, 1535 Spruce St., Boulder",
            org_chamber,
            "forum",
            None,
            "Annual season-opener. 5–8pm. First forum to which all qualified candidates were invited. Topics listed by Chamber: affordable housing, transportation, public safety. Attendance not independently verified in this seed — Aaron and Benjamin were there.",
        ),
    )
    ev_chamber = cur.lastrowid
    cur.execute(
        """INSERT INTO events (slug, name, starts_on, venue, host_org_id, kind, recording_url, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            "2025-chamber-forum",
            "Boulder Chamber candidate forum (2025 cycle)",
            "2025-08-26",
            None,
            org_chamber,
            "forum",
            None,
            "BRL photo caption (Wallach resignation story) places Mark Wallach at a Chamber forum on Aug 26 2025. Full 2025 forum calendar not yet harvested.",
        ),
    )

    # Appearances at Raucous Caucus (from BRL photo/caption + body)
    for person, candidacy, attended in [
        ("Tara Winer", c2026_winer, 1),
        ("Tina Marquis", c2026_marquis, 1),
        ("Benita Duran", c2026_duran, 1),
        ("Rachel Rose Isaacson", c2026_isaacson, 1),
        ("Ryan Schuchard", c2026_schuchard, 1),
        ("Jill Grano", c2026_grano, 1),
        ("Aaron Brockett", c2026_brockett, 1),
        ("Taishya Adams", None, 0),
    ]:
        cur.execute(
            """INSERT INTO event_appearances (event_id, candidacy_id, person_id, attended, notes)
               VALUES (?,?,?,?,?)""",
            (ev_caucus, candidacy, pid[person], attended,
             "From BRL June 7 2026 reporting. Adams declined to comment on a run at the time."),
        )

    # Chamber 2026: Aaron and Benjamin attended (channel report). Full candidate
    # roster not independently recorded in this seed — do not invent appearances.

    # --- issues / one harvested question ---
    for slug_, name, desc in [
        ("housing", "Housing", "Supply, middle-income housing, Area III, ADUs, duplex/triplex, vacancy tax."),
        ("airport", "Municipal airport", "Whether to accept FAA grants that lock the airport open; housing-on-airport-land argument."),
        ("wages", "Wages and tipped workers", "City minimum wage vs. tipped-credit / slower base-pay increases."),
        ("budget", "City budget", "Sales-tax slowdown, maintenance backlog, rec-center bonds."),
        ("wildfire", "Wildfire resilience", "Hardening existing homes, defensible space."),
        ("homelessness", "Homelessness", "Camping ban when shelter is full; services vs. enforcement."),
        ("transportation", "Transportation", "Iris Ave, 30th St, bike infrastructure."),
        ("foreign-affairs", "Foreign affairs at council", "Gaza comment, divestment, whether council weighs in."),
    ]:
        cur.execute("INSERT INTO issues (slug, name, description) VALUES (?,?,?)", (slug_, name, desc))

    cur.execute(
        "INSERT INTO questions (prompt, issue_slug, is_canonical) VALUES (?,?,1)",
        (
            "Would you support accepting federal FAA grants that could require Boulder to keep the municipal airport open in perpetuity?",
            "airport",
        ),
    )
    q_airport = cur.lastrowid

    # BRL June 7 2026: Brockett, Duran, Winer yes; Marquis, Schuchard, Grano, Isaacson no.
    airport_answers = [
        ("Aaron Brockett", c2026_brockett, "yes"),
        ("Benita Duran", c2026_duran, "yes"),
        ("Tara Winer", c2026_winer, "yes"),
        ("Tina Marquis", c2026_marquis, "no"),
        ("Ryan Schuchard", c2026_schuchard, "no"),
        ("Jill Grano", c2026_grano, "no"),
        ("Rachel Rose Isaacson", c2026_isaacson, "no"),
    ]
    for person, candidacy, stance in airport_answers:
        cur.execute(
            """INSERT INTO answers
               (candidacy_id, person_id, question_id, source_id, stance, verbatim, answered_on, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                candidacy, pid[person], q_airport, s_2026_brl_caucus, stance,
                "Reported by Boulder Reporting Lab from the June 6 2026 Raucous Caucus. Not a written questionnaire; a journalist's grouping of spoken answers.",
                "2026-06-06",
                "Harvested as a first proof that answers can hang off sources. Re-verify against video/transcript when one exists.",
            ),
        )

    # --- results ---
    # 2023 mayor RCV (official summary of votes)
    def add_result(c_id: int, round_: int, votes: int, share: float | None, place: int | None,
                   elected: int, source: int, notes: str | None = None) -> None:
        cur.execute(
            """INSERT INTO results
               (candidacy_id, round, votes, vote_share, place, elected, source_id, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (c_id, round_, votes, share, place, elected, source, notes),
        )

    add_result(c2023_brockett, 1, 11504, None, 2, 0, s_2023_rcv, "First-choice.")
    add_result(c2023_yates, 1, 14271, None, 1, 0, s_2023_rcv, "First-choice. Led after round 1.")
    add_result(c2023_speer_m, 1, 6369, None, 3, 0, s_2023_rcv, "Eliminated after round 1.")
    add_result(c2023_tweedlie, 1, 749, None, 4, 0, s_2023_rcv, "Eliminated after round 1.")
    add_result(c2023_brockett, 2, 16823, 51.9, 1, 1, s_2023_rcv, "Final after transfers (+5,319).")
    add_result(c2023_yates, 2, 15592, 48.1, 2, 0, s_2023_rcv, "Final after transfers (+1,321).")

    # 2023 council (amended recount summary)
    council_2023 = [
        (c2023_winer, 21255, 1, 1),
        (c2023_marquis, 14958, 2, 1),
        (c2023_adams, 14633, 3, 1),
        (c2023_schuchard, 14411, 4, 1),
        (c2023_brncic, 14365, 5, 0),
    ]
    for c_id, votes, place, elected in council_2023:
        add_result(c_id, 1, votes, None, place, elected, s_2023_summary, "Recount-certified.")

    # remaining 2023 council from same amended PDF
    for person, votes, place in [
        ("Jennifer Robins", 11249, 6),
        ("Waylon Lewis", 8862, 7),
        ("Silas Atkins", 6829, 8),
        ("Aaron Gabriel Neyer", 3483, 9),
        ("Jacques Decalo", 3329, 10),
    ]:
        cur.execute("SELECT id FROM candidacies WHERE person_id=? AND race_id=?", (pid[person], r2023_council))
        c_id = cur.fetchone()[0]
        add_result(c_id, 1, votes, None, place, 0, s_2023_summary, "Recount-certified.")

    # 2025 council — Clarity ENR, matches Daily Camera certified seating totals for top 4
    council_2025 = [
        ("Matt Benjamin", 20276, 17.80, 1, 1),
        ("Mark Wallach", 17476, 15.34, 2, 1),
        ("Nicole Speer", 16165, 14.19, 3, 1),
        ("Rob Kaplan", 15867, 13.93, 4, 1),
        ("Jennifer Robins", 14781, 12.98, 5, 0),
        ("Lauren Folkerts", 14222, 12.49, 6, 0),
        ("Rachel Rose Isaacson", 5085, 4.46, 7, 0),
        ("Montserrat Palacios", 2957, 2.60, 8, 0),
        ("Maxwell Lord", 2853, 2.51, 9, 0),
        ("Aaron Stone", 2707, 2.38, 10, 0),
        ("Rob Smoke", 1499, 1.32, 11, 0),
    ]
    for person, votes, share, place, elected in council_2025:
        cur.execute("SELECT id FROM candidacies WHERE person_id=? AND race_id=?", (pid[person], r2025_council))
        c_id = cur.fetchone()[0]
        add_result(c_id, 1, votes, share, place, elected, s_2025_clarity, "Clarity ENR; top four match Daily Camera seating story.")

    # --- meta ---
    cur.executemany(
        "INSERT INTO meta (key, value) VALUES (?,?)",
        [
            ("built_at", "2026-08-27"),
            ("builder", "GrokJi"),
            ("scope", "City of Boulder mayor + city council, 2023–2026. Not county, not BVSD, not ballot measures — yet."),
            ("editorial", "No endorsements. Quotes and vote totals are sourced. Synthesized 'positions' are out of scope until we have a reviewable method."),
            ("next_harvest", "BRL 2025 questionnaire answers; city campaign-finance filings; 2026 Chamber forum notes/recording; remaining campaign sites; Vote411 when it opens."),
        ],
    )

    con.commit()
    n_people = cur.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    n_cand = cur.execute("SELECT COUNT(*) FROM candidacies").fetchone()[0]
    n_src = cur.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    n_ans = cur.execute("SELECT COUNT(*) FROM answers").fetchone()[0]
    n_res = cur.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    con.close()
    print(f"wrote {DB}")
    print(f"people={n_people} candidacies={n_cand} sources={n_src} answers={n_ans} results={n_res}")


if __name__ == "__main__":
    main()
