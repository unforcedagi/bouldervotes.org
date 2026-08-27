"""Extra seed: BRL questionnaires, forum calendar, city ballot measures."""
from __future__ import annotations

import json
from pathlib import Path

HARVEST = Path(__file__).resolve().parent / "data" / "harvest" / "brl_questionnaires.json"


def _ensure_source(cur, add_source, url, *args):
    cur.execute("SELECT id FROM sources WHERE url=?", (url,))
    row = cur.fetchone()
    if row:
        return row[0]
    return add_source(url, *args)


def _cid(cur, person: str, year: int) -> int | None:
    cur.execute(
        """SELECT c.id FROM candidacies c
           JOIN people p ON p.id=c.person_id
           JOIN races r ON r.id=c.race_id
           JOIN elections e ON e.id=r.election_id
           WHERE p.full_name=? AND e.year=?""",
        (person, year),
    )
    row = cur.fetchone()
    return row[0] if row else None


def ingest_questionnaires(cur, *, pid: dict, add_source, org_brl: int) -> None:
    data = json.loads(HARVEST.read_text(encoding="utf-8"))
    for post in data["posts"]:
        src_id = _ensure_source(
            cur,
            add_source,
            post["url"],
            post["title"],
            "questionnaire",
            post["year"],
            org_brl,
            post["published_on"],
            "BRL candidate questionnaire. Verbatim answers harvested 2026-08-27.",
        )
        cur.execute(
            """INSERT INTO questions (prompt, issue_slug, year, kind, is_canonical)
               VALUES (?,?,?,?,1)""",
            (post["prompt"], post["issue"], post["year"], "questionnaire"),
        )
        qid = cur.lastrowid
        for ans in post["answers"]:
            person = ans["person"]
            if person not in pid:
                raise SystemExit(f"harvest person not in seed: {person}")
            cur.execute(
                """INSERT INTO answers
                   (candidacy_id, person_id, question_id, source_id, event_id, kind,
                    stance, verbatim, answered_on, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    _cid(cur, person, post["year"]),
                    pid[person],
                    qid,
                    src_id,
                    None,
                    "questionnaire",
                    ans["stance"],
                    ans["verbatim"],
                    post["published_on"],
                    "Candidate's written answer to BRL, as published.",
                ),
            )


def ingest_forums(cur, *, pid: dict, add_source, orgs: dict) -> None:
    """Forum calendar. Appearances only when a published source names who showed."""

    def add_event(slug, name, date, venue, host, kind, recording, notes, source_url=None, source_title=None, year=None):
        src_id = None
        if source_url:
            src_id = _ensure_source(
                cur, add_source, source_url, source_title or name, "article", year, None, None, None
            )
        cur.execute(
            """INSERT INTO events (slug, name, starts_on, venue, host_org_id, kind, recording_url, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (slug, name, date, venue, host, kind, recording, notes),
        )
        return cur.lastrowid, src_id

    def appear(event_id, year, people_attended, people_absent=(), note=None):
        for person in people_attended:
            cur.execute(
                """INSERT INTO event_appearances (event_id, candidacy_id, person_id, attended, notes)
                   VALUES (?,?,?,?,?)""",
                (event_id, _cid(cur, person, year), pid[person], 1, note),
            )
        for person in people_absent:
            cur.execute(
                """INSERT INTO event_appearances (event_id, candidacy_id, person_id, attended, notes)
                   VALUES (?,?,?,?,?)""",
                (event_id, _cid(cur, person, year), pid[person], 0, note),
            )

    # Existing 2025 chamber row was a stub. Replace notes/venue.
    cur.execute("SELECT id FROM events WHERE slug='2025-chamber-forum'")
    row = cur.fetchone()
    if row:
        cur.execute(
            """UPDATE events SET venue=?, recording_url=?, notes=? WHERE id=?""",
            (
                "New Vista High School, 700 20th St., Boulder",
                "https://www.youtube.com/watch?v=a-6Mso1bNhA",
                "Season-opener. Ten of eleven certified candidates spoke. Palacios is not named in the Daily Camera writeup of attendees. Recording: Boulder Chamber YouTube, '2025 City Council Candidate Forum' (2h05).",
                row[0],
            ),
        )
        ev_2025_chamber = row[0]
    else:
        ev_2025_chamber, _ = add_event(
            "2025-chamber-forum",
            "Boulder Chamber candidate forum (2025 cycle)",
            "2025-08-26",
            "New Vista High School, 700 20th St., Boulder",
            orgs["chamber"],
            "forum",
            "https://www.youtube.com/watch?v=a-6Mso1bNhA",
            "Season-opener.",
        )

    add_source(
        "https://www.dailycamera.com/2025/09/04/where-boulder-city-council-candidates-key-issues/",
        "Where Boulder City Council candidates stand on key issues (Daily Camera)",
        "article",
        2025,
        orgs["camera"],
        "2025-09-04",
        "Writeup of the Aug 26 2025 Chamber forum at New Vista. Names ten speakers.",
    )
    chamber_2025_present = [
        "Lauren Folkerts",
        "Rachel Rose Isaacson",
        "Matt Benjamin",
        "Mark Wallach",
        "Aaron Stone",
        "Rob Kaplan",
        "Jennifer Robins",
        "Nicole Speer",
        "Rob Smoke",
        "Maxwell Lord",
    ]
    appear(
        ev_2025_chamber,
        2025,
        chamber_2025_present,
        ["Montserrat Palacios"],
        "Daily Camera Sept 4 2025 photo/caption + body. Palacios not listed among the ten.",
    )

    # 2025 collaborative forum
    ev, _ = add_event(
        "2025-votes-forum",
        "Boulder VOTES! Collaborative Candidate Forum",
        "2025-09-08",
        "Nomad Playhouse, 1410 Quince Ave., Boulder",
        orgs["plan"],
        "forum",
        None,
        "Hosted by Open Boulder, Better Boulder, and PLAN-Boulder County. 5–7:30pm. Questions not taken from the audience. Daily Camera (Sept 6) said a recording would be posted; not independently located in this pass.",
        "https://www.dailycamera.com/2025/09/06/boulder-groups-host-city-council-candidate-forum-next-week/",
        "Boulder groups host City Council candidate forum next week (Daily Camera)",
        2025,
    )
    appear(
        ev,
        2025,
        [
            "Mark Wallach",
            "Matt Benjamin",
            "Nicole Speer",
            "Lauren Folkerts",
            "Jennifer Robins",
            "Rob Kaplan",
            "Rachel Rose Isaacson",
            "Maxwell Lord",
        ],
        ["Montserrat Palacios", "Rob Smoke", "Aaron Stone"],
        "Daily Camera Sept 6 2025: eight of eleven present; Palacios, Smoke, Stone will not be present.",
    )

    # 2023 Chamber — all 14, Speer virtual. Recording exists.
    add_source(
        "https://www.dailycamera.com/2023/08/29/boulder-city-council-and-mayoral-candidates-face-off-at-candidate-forum/",
        "Boulder City Council and mayoral candidates face off at candidate forum (Daily Camera)",
        "article",
        2023,
        orgs["camera"],
        "2023-08-29",
        "All fourteen certified candidates. Speer participated virtually.",
    )
    ev, _ = add_event(
        "2023-chamber-forum",
        "Boulder Chamber City Council and Mayoral Candidate Forum",
        "2023-08-29",
        "Boulder JCC",
        orgs["chamber"],
        "forum",
        "https://www.youtube.com/watch?v=AEkK1eSLmNk",
        "Season-opener. All 14 certified candidates. Speer virtual. Questions from Chamber, Latino Chamber, Community Cycles: public safety, rent control, transportation, business support, labor shortages, minimum wage.",
    )
    chamber_2023 = [
        "Taishya Adams",
        "Silas Atkins",
        "Terri Brncic",
        "Jacques Decalo",
        "Waylon Lewis",
        "Tina Marquis",
        "Aaron Gabriel Neyer",
        "Jennifer Robins",
        "Ryan Schuchard",
        "Tara Winer",
        "Paul Tweedlie",
        "Nicole Speer",
        "Bob Yates",
        "Aaron Brockett",
    ]
    appear(
        ev,
        2023,
        chamber_2023,
        (),
        "Daily Camera Aug 29 2023. Speer virtual. YouTube recording linked from r/boulder the next day.",
    )
    cur.execute(
        "UPDATE event_appearances SET notes=? WHERE event_id=? AND person_id=?",
        (
            "Participated virtually (Daily Camera Aug 29 2023).",
            ev,
            pid["Nicole Speer"],
        ),
    )

    add_event(
        "2023-progressives-forum",
        "Boulder Progressives candidate forum",
        "2023-06-21",
        "Elks Lodge, Boulder",
        orgs["progressives"],
        "caucus",
        None,
        "Unofficial kickoff. BRL: eight council candidates and three mayoral candidates. Housing and homelessness dominated. Full attendance list not copied into this seed beyond the article.",
        "https://boulderreportinglab.org/2023/06/23/boulder-election-forum-puts-candidates-progressive-politics-to-the-test/",
        "Boulder election forum puts candidates’ progressive politics to the test (BRL)",
        2023,
    )
    add_source(
        "https://www.planboulder.org/boulder-election-2023",
        "Boulder Election 2023 — PLAN-Boulder County",
        "official",
        2023,
        orgs["plan"],
        None,
        "PLAN's own 2023 page lists two candidate forums (Aug 23 and Aug 29) with named attendees, plus endorsements. Venue not stated on that page.",
    )
    ev, _ = add_event(
        "2023-plan-mayor-forum",
        "PLAN-Boulder County candidate forum (mayor + two council)",
        "2023-08-23",
        None,
        orgs["plan"],
        "forum",
        None,
        "PLAN-Boulder County's own page: four mayoral candidates plus council candidates Taishya Adams and Jacques Decalo. Moderator Bill Briggs. Venue not stated.",
        "https://www.planboulder.org/boulder-election-2023",
        "Boulder Election 2023 — PLAN-Boulder County",
        2023,
    )
    appear(
        ev,
        2023,
        ["Nicole Speer", "Bob Yates", "Aaron Brockett", "Paul Tweedlie", "Taishya Adams", "Jacques Decalo"],
        (),
        "Named on PLAN-Boulder County's 2023 election page as Aug 23 attendees.",
    )
    ev, _ = add_event(
        "2023-plan-council-forum",
        "PLAN-Boulder County city council forum",
        "2023-08-29",
        None,
        orgs["plan"],
        "forum",
        None,
        "Same calendar night as the Chamber forum. PLAN's page names seven council candidates. Moderator Bill Briggs. Venue not stated. Silas Atkins is not named on either PLAN forum list — absence not independently confirmed.",
        "https://www.planboulder.org/boulder-election-2023",
        "Boulder Election 2023 — PLAN-Boulder County",
        2023,
    )
    appear(
        ev,
        2023,
        [
            "Tara Winer",
            "Terri Brncic",
            "Waylon Lewis",
            "Tina Marquis",
            "Ryan Schuchard",
            "Aaron Gabriel Neyer",
            "Jennifer Robins",
        ],
        (),
        "Named on PLAN-Boulder County's 2023 election page as Aug 29 attendees.",
    )
    add_event(
        "2023-kgnu-mayor-debate",
        "BRL–KGNU mayoral debate",
        "2023-10-18",
        None,
        orgs["brl"],
        "debate",
        None,
        "All four mayoral candidates. Mentioned in BRL's Oct 27 2023 'who’s running' photo caption. Recording not independently located in this pass.",
        "https://boulderreportinglab.org/2023/10/27/whos-running-for-boulder-mayor-city-council-in-the-2023-election/",
        "Who’s running for Boulder mayor, City Council in the 2023 election (BRL)",
        2023,
    )
    add_event(
        "2023-climate-mayor-forum",
        "Climate-focused Boulder mayoral forum",
        "2023-10-05",
        None,
        None,
        "forum",
        None,
        "BRL Oct 6 2023: Xcel Energy was a central subject. Date is the day before the article.",
        "https://boulderreportinglab.org/2023/10/06/climate-focused-boulder-mayoral-forum-puts-the-heat-on-xcel-energy/",
        "Climate-focused Boulder mayoral forum puts the heat on Xcel Energy (BRL)",
        2023,
    )

    # LWV forums — City of Boulder Channel 8 recorded them; YouTube is the record.
    add_source(
        "https://www.youtube.com/watch?v=Xb83hgpphXo",
        "2023 League of Women Voters Candidate Forum (City of Boulder / Channel 8)",
        "video",
        2023,
        orgs["lwv"] if "lwv" in orgs else None,
        "2023-10-15",
        "Live recording. Council race. Co-sponsored with EFAA. Published Oct 15 2023 on the city's YouTube.",
    )
    add_event(
        "2023-lwv-council-forum",
        "League of Women Voters city council candidate forum",
        "2023-10-15",
        "City Council Chambers, Penfield Tate II Municipal Building",
        orgs["lwv"] if "lwv" in orgs else None,
        "forum",
        "https://www.youtube.com/watch?v=Xb83hgpphXo",
        "Co-sponsored with EFAA. City Channel 8 recording, 1h35. Attendance not copied name-by-name in this pass — the video is the source.",
        "https://www.youtube.com/watch?v=Xb83hgpphXo",
        "2023 League of Women Voters Candidate Forum",
        2023,
    )
    add_source(
        "https://www.youtube.com/watch?v=n89j6Wk-qc8",
        "2023 League of Women Voters Mayoral Candidate Forum (City of Boulder / Channel 8)",
        "video",
        2023,
        orgs["lwv"] if "lwv" in orgs else None,
        "2023-10-22",
        "Live recording of the mayoral forum. All four 2023 mayoral candidates appear in the transcript.",
    )
    ev, _ = add_event(
        "2023-lwv-mayor-forum",
        "League of Women Voters mayoral candidate forum",
        "2023-10-22",
        "City Council Chambers, Penfield Tate II Municipal Building",
        orgs["lwv"] if "lwv" in orgs else None,
        "forum",
        "https://www.youtube.com/watch?v=n89j6Wk-qc8",
        "Co-sponsored with EFAA. City Channel 8 recording. Transcript names Brockett, Speer, Tweedlie, and Yates.",
        "https://www.youtube.com/watch?v=n89j6Wk-qc8",
        "2023 League of Women Voters Mayoral Candidate Forum",
        2023,
    )
    appear(
        ev,
        2023,
        ["Aaron Brockett", "Nicole Speer", "Paul Tweedlie", "Bob Yates"],
        (),
        "Named in the City of Boulder YouTube auto-transcript of the Oct 22 2023 LWV mayoral forum.",
    )

    add_source(
        "https://lwvbc.clubexpress.com/content.aspx?page_id=4091&club_id=629866&item_id=2716057",
        "Boulder City Council Candidate Forum — League of Women Voters of Boulder County (event page)",
        "official",
        2025,
        orgs["lwv"] if "lwv" in orgs else None,
        "2025-09-27",
        "Sat Sept 27 2025, 10:00–11:30am, Council Chambers. Co-sponsor EFAA. Live on Boulder 8 / Comcast 880.",
    )
    add_source(
        "https://www.youtube.com/watch?v=JcJu9nd5mQk",
        "2025 League of Women Voters of Boulder County Council Candidate Forum (City of Boulder / Channel 8)",
        "video",
        2025,
        orgs["lwv"] if "lwv" in orgs else None,
        "2025-09-29",
        "Recording of the Sept 27 forum. Moderator states 8 of 11 certified candidates participated; all were invited. Name-by-name attendance not copied in this pass.",
    )
    add_event(
        "2025-lwv-council-forum",
        "League of Women Voters city council candidate forum",
        "2025-09-27",
        "City Council Chambers, Penfield Tate II Municipal Building, 1777 Broadway",
        orgs["lwv"] if "lwv" in orgs else None,
        "forum",
        "https://www.youtube.com/watch?v=JcJu9nd5mQk",
        "Co-sponsored with EFAA. 10:00–11:30am. Moderator (Josephine Porter, on the recording): 11 on the ballot, 8 able to participate, all invited. Questions from audience cards plus electronic submissions. Name-by-name list not copied here; watch the video.",
        "https://lwvbc.clubexpress.com/content.aspx?page_id=4091&club_id=629866&item_id=2716057",
        "Boulder City Council Candidate Forum — LWVBC event page",
        2025,
    )

def ingest_measures(cur, *, add_source, org_city: int, org_brl: int, org_camera: int, e2023: int, e2025: int, e2026: int) -> None:
    s_city_2026 = _ensure_source(
        cur,
        add_source,
        "https://bouldercolorado.gov/2026-city-boulder-ballot-measures",
        "2026 City of Boulder Ballot Measures",
        "official",
        2026,
        org_city,
        "2026-08-21",
        "City guide. Ballot letters not yet assigned. TABOR pro/con deadline Sept 18 2026.",
    )
    s_brl_ref = add_source(
        "https://boulderreportinglab.org/2026/08/06/boulder-city-council-sends-vacancy-tax-and-400-million-bond-to-november-ballot-rejects-downtown-development-authority/",
        "Council sends vacancy tax and $400 million bond to November ballot, rejects DDA (BRL)",
        "article",
        2026,
        org_brl,
        "2026-08-06",
        "Referral night. DDA 4–4 fail. Bond unanimous. Vacancy tax 7–1 (Speer no). Companion debt-limit charter referred. Firefighters CBA also referred.",
    )
    add_source(
        "https://www.dailycamera.com/2026/08/07/boulder-tax-measures-ballot/",
        "Boulder voters to decide on vacancy tax, $400 million infrastructure bond (Daily Camera)",
        "article",
        2026,
        org_camera,
        "2026-08-07",
        "Vacancy tax 7–1 Speer dissenting (wanted a fee). Bond unanimous.",
    )
    add_source(
        "https://www.dailycamera.com/2026/08/11/boulder-firefighters-union-ballot/",
        "Boulder firefighters could have their collective bargaining rights secured in November (Daily Camera)",
        "article",
        2026,
        org_camera,
        "2026-08-11",
        "Unanimous referral of charter Sec. 73. Impasse: non-binding factfinding then city vote. No strike.",
    )

    measures = [
        (
            "2026-rec-safety-bond",
            e2026,
            None,
            "Building Boulder Together: Recreation and Safety Bond",
            "bond",
            "referred",
            "Authorizes up to $400 million of general-obligation debt (maximum repayment cost $650 million) repaid by a new property tax, up to $32.5 million a year. City example: about $400 a year on a $1 million home if the full amount is bonded. Intended projects: South Boulder Rec Center (incl. lap pool), North Boulder Rec Center + West Age Well, Fire Stations 1 and 5, Public Safety Building / 911, Penfield Tate II, Municipal Services Center. When the debt is paid, the extra tax ends.",
            "Shall City of Boulder debt be increased up to $400,000,000, with a maximum repayment cost up to $650,000,000, and shall city taxes be increased up to $32,500,000 annually … (full TABOR language on the city page).",
            s_city_2026,
            "Referred unanimously Aug 6 2026. Project list is what the city intends; BRL notes the list is not binding.",
        ),
        (
            "2026-debt-limit-charter",
            e2026,
            None,
            "Charter debt-limit calculation (actual vs. assessed value)",
            "charter",
            "referred",
            "Amends Charter §97 so the city’s debt limit is 3% of the actual value of taxable property, not the assessed value. City says this matches how most Colorado municipalities and the state calculate the cap, and would allow more debt than the current formula.",
            "Shall Section 97 of the Boulder Home Rule Charter be amended pursuant to Ordinance 8762 to modify the City’s debt limitation to be not more than three percent of the actual value of the taxable property within the City?",
            s_city_2026,
            "Companion to the rec/safety bond. Referred Aug 6 2026 (BRL).",
        ),
        (
            "2026-vacancy-excise-tax",
            e2026,
            None,
            "Vacancy excise tax",
            "tax",
            "referred",
            "About $4,000 a year on a residential property occupied 183 days or fewer, CPI-adjusted, never below $4,000, never above $7,000. Estimated $6 million in 2028, the first full collection year. Revenue is general city services (police, fire, parks, transportation), not a dedicated housing fund. Goal stated by proponents: push empty second homes onto the rental or sale market.",
            "Shall the City of Boulder taxes be increased $6,000,000 annually … by imposing a $4,000 tax on vacant homes that are occupied for 183 days or less per year …",
            s_city_2026,
            "Referred 7–1 Aug 6 2026. Speer voted no; she wanted a fee rather than a tax (Daily Camera Aug 7).",
        ),
        (
            "2026-firefighter-cba-charter",
            e2026,
            None,
            "Collective bargaining for firefighters (new Charter §73)",
            "charter",
            "referred",
            "Moves full-time firefighters’ collective-bargaining rights from contract/ordinance into the charter. Bargain over safety, wages, benefits, and terms of employment except reserved management rights. Impasse: non-binding factfinding, then if needed a vote of city electors. Strikes / work stoppages prohibited. Current CBA runs through 2027.",
            "Shall the city amend its charter by the addition of a new Sec. 73, “Collective Bargaining for Firefighters,” as described in Ordinance 8761 …",
            s_city_2026,
            "Referred unanimously (Daily Camera Aug 11 2026).",
        ),
        (
            "2026-dda",
            e2026,
            None,
            "Downtown Development Authority referral",
            "other",
            "not_referred",
            "Would have asked district electors (residents, property owners, qualified business tenants inside a downtown / Civic Area / University Hill boundary — city estimated ~2,500 electors) to form a 30-year DDA with tax-increment financing. Not a citywide vote.",
            None,
            s_brl_ref,
            "Failed 4–4 Aug 6 2026; a tie cannot refer. BRL named the four no votes: Adams, Marquis, Schuchard, Speer. The four yes votes are the other sitting members that night (Brockett, Winer, Benjamin, Kaplan) — inferred from the eight-member dais after Wallach’s resignation, not from a roll-call PDF. Staff directed to keep exploring a DDA.",
        ),
    ]
    for slug, eid, letter, title, kind, status, summary, language, src, notes in measures:
        cur.execute(
            """INSERT INTO measures
               (slug, election_id, letter, title, kind, status, summary, ballot_language, source_id, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (slug, eid, letter, title, kind, status, summary, language, src, notes),
        )

    s_2023_sov = _ensure_source(
        cur,
        add_source,
        "https://assets.bouldercounty.gov/wp-content/uploads/2023/11/2023C-Boulder-County-Official-Summary-of-Votes.pdf",
        "2023 Coordinated Election — Official Summary of Votes",
        "results",
        2023,
        None,
        "2023-11-29",
        "Certified city measure totals used here (2A, 2B, 302).",
    )
    s_2023_302 = _ensure_source(
        cur,
        add_source,
        "https://boulderreportinglab.org/2023/11/08/city-of-boulder-votes-to-pass-safe-zones-4-kids-ballot-measure/",
        "City of Boulder votes to pass Safe Zones 4 Kids ballot measure (BRL)",
        "article",
        2023,
        org_brl,
        "2023-11-08",
        "Question 302. Citizen initiative. ~61% yes.",
    )
    for slug, letter, title, kind, summary, language, yes, no, notes in [
        (
            "2023-2a-sales-tax-extension",
            "2A",
            "City sales and use tax extension",
            "tax",
            "Extends the existing 0.15% city sales and use tax from Dec 31 2024 to Dec 31 2044 without raising the rate. 50% general fund (fire, public safety, homeless services, etc.), 50% arts, culture, and heritage.",
            "WITHOUT RAISING ADDITIONAL TAXES, SHALL THE EXISTING 0.15 CENT CITY SALES AND USE TAX FOR GENERAL FUND PURPOSES … BE EXTENDED … UNTIL DECEMBER 31, 2044 …",
            24810,
            8473,
            "Certified official summary of votes. 74.54% yes.",
        ),
        (
            "2023-2b-charter-elections",
            "2B",
            "Elections administrative charter cleanup",
            "charter",
            "Amends charter sections 27, 37, 39, 46 and 57 on election administration: mayor/council petitions carried outside the municipal building, extra clerk processing time, and a clarification that state law governs charter amendments (PLAN-Boulder 2023 page).",
            None,
            26137,
            4153,
            "Certified official summary of votes. 86.29% yes (26,137 / 30,290).",
        ),
        (
            "2023-302-safe-zones-4-kids",
            "302",
            "Safe Zones 4 Kids",
            "other",
            "Citizen initiative. Amends city code §8-3-21 to prioritize removal of already-prohibited tents, temporary structures, and propane tanks within 500 feet of a school or 50 feet of a multi-use path or sidewalk.",
            "Shall Section 8-3-21, B.R.C. 1981, be amended to add a provision to prioritize removal of prohibited items, such as tents, temporary structures, or propane tanks, within five hundred feet of a school or fifty feet of any multi-use path or sidewalk pursuant to Ordinance 8586?",
            20261,
            12973,
            "Certified official summary of votes. 60.96% yes. Litmus-test issue of the 2023 council race (BRL).",
        ),
    ]:
        src = s_2023_302 if slug.endswith("302-safe-zones-4-kids") else s_2023_sov
        cur.execute(
            """INSERT INTO measures
               (slug, election_id, letter, title, kind, status, summary, ballot_language, source_id, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (slug, e2023, letter, title, kind, "passed", summary, language, src, notes),
        )
        mid = cur.lastrowid
        cur.execute(
            """INSERT INTO measure_results (measure_id, yes_votes, no_votes, passed, source_id, notes)
               VALUES (?,?,?,?,?,?)""",
            (mid, yes, no, 1, s_2023_sov, "Official Summary of Votes, Boulder County Clerk."),
        )

    s_2025_results = _ensure_source(
        cur,
        add_source,
        "https://boulderreportinglab.org/2025/11/06/boulder-2025-election-results-voters-reelect-three-incumbents-to-council-and-pass-all-tax-measures/",
        "Boulder 2025 election results (BRL)",
        "article",
        2025,
        org_brl,
        "2025-11-06",
        "2A CCRS extension and 2B CCRS debt both passed. County 1A/1B also passed.",
    )

    for slug, letter, title, kind, summary in [
        (
            "2025-2a-ccrs-extension",
            "2A",
            "Community, Culture, Resilience, and Safety (CCRS) tax extension",
            "tax",
            "Extends the existing 0.3% CCRS sales and use tax in perpetuity (it had been set to expire Dec 31 2036) without raising the rate. Funds capital work: rec centers, fire/police stations, paths, bridges, open space trailheads, etc.",
        ),
        (
            "2025-2b-ccrs-debt",
            "2B",
            "CCRS tax debt authorization",
            "bond",
            "Authorizes up to $262 million principal ($350 million maximum repayment) payable solely from the CCRS tax extension, if 2A also passed. Companion to 2A.",
        ),
    ]:
        cur.execute(
            """INSERT INTO measures
               (slug, election_id, letter, title, kind, status, summary, ballot_language, source_id, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (slug, e2025, letter, title, kind, "passed", summary, None, s_2025_results,
             "Passed Nov 4 2025 (BRL Nov 6). Yes/no vote totals not copied from the SOV in this pass."),
        )
        mid = cur.lastrowid
        cur.execute(
            """INSERT INTO measure_results (measure_id, yes_votes, no_votes, passed, source_id, notes)
               VALUES (?,?,?,?,?,?)""",
            (mid, None, None, 1, s_2025_results, "Certified as passed; raw yes/no not yet harvested from the county SOV."),
        )
