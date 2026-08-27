# Source map — City of Boulder elections 2023–2026

Harvested 2026-08-27 by GrokJi. Negative claims are scoped to what was actually searched.

`bouldervotes.org` is live on GitHub Pages as of 2026-08-27: DNS A records point at `185.199.108–111.153`, Pages custom domain + Let’s Encrypt cert approved, `https_enforced`. From this box, `dig` sees the records; the system resolver does not — curl with `--resolve` to a GitHub IP returns 200 and the site. `www` has no record.

WovenBoulder is a retired experiment (Aaron, 2026-08-27). Do not spend cycles on it.

---

## Official

| Source | URL | Years | Shape | Notes |
|---|---|---|---|---|
| City clerk candidate list | https://bouldercolorado.gov/2026-city-boulder-mayoral-and-city-council-candidates | 2026 | HTML | **Canonical 2026 field.** Certified-on dates, matching-funds asterisks. Ballot order by lot Aug 25. |
| Voting / election info | https://bouldercolorado.gov/services/voting-and-election-information | 2026 | HTML | Election day Nov 3 2026. Intent-to-run / petition window Aug 4–24. Links to committee filings and past records. |
| Election guidelines / campaign finance calendar | https://bouldercolorado.gov/election-guidelines | 2026 | HTML | Municipal finance is **city**, not TRACER. Filings: 42/28/21/14 days out + Thursday before + 30 days after. |
| Committee filings | https://bouldercolorado.gov/elections/election-committee-filings | 2026 | HTML | Live during season. Not yet scraped. |
| Election records 2008–present | Laserfiche via city site | 2008– | PDFs | Historical committees. |
| RCV guide | https://bouldercolorado.gov/guide/ranked-choice-voting-guide | 2023, 2026 | HTML | RCV is **mayor only**. 2026 = second use. |
| Current council | https://bouldercolorado.gov/government/city-council | current | HTML | Eight names as of Aug 27 2026 (Wallach gone). Term years listed. |
| Agendas | OneMeeting + records archive | ongoing | portal | wovenboulder.org’s original idea lives here: meetings, not campaigns. Switchover July 24 2025. |
| Meeting video | City of Boulder YouTube | ongoing | video | Transcripts auto-generated, messy. |

## County (results)

| Source | URL | Years | Shape |
|---|---|---|---|
| 2023 election hub | https://bouldercounty.gov/elections/by-year/2023-election/ | 2023 | HTML + Excel + PDF |
| 2023 recount summary | https://assets.bouldercounty.gov/wp-content/uploads/2023/12/2023C-Boulder-County-Official-Summary-of-Votes-Recount.pdf | 2023 | PDF |
| 2023 official ENR | https://electionresults.bouldercounty.gov/ElectionResults2023C/Home/IndexCategory/39.html | 2023 | HTML |
| 2023 RCV summary | https://assets.bouldercounty.gov/wp-content/uploads/2023/11/2023C-Boulder-County-Official-Summary-of-Votes.pdf | 2023 | PDF |
| 2025 Clarity ENR | https://results.enr.clarityelections.com/CO/Boulder/124417/ | 2025 | HTML |
| Results index | https://bouldercounty.gov/elections/results/ | ongoing | HTML |
| Elections by year | https://bouldercounty.gov/elections/by-year/ | 2023+ | HTML |

Municipal **candidates file with the city**; **ballots and results are the county**.

## Press

| Outlet | Pattern | Strength |
|---|---|---|
| **Boulder Reporting Lab** https://boulderreportinglab.org | Voter guides, all-candidate questionnaires (2025: 11/11 responded), vote tracker, forum writeups, resignation/airport. John Herrick, Brooke Stephenson. | Best structured civic record in town. 2025 questionnaire is the ingest target. |
| **Daily Camera** https://www.dailycamera.com | Candidate profiles as they file; seating/certified totals; Chamber-adjacent coverage. James Burky. | Profiles are appearing now (Isaacson Aug 13, Brockett Aug 19). Paywall-ish. |
| **Boulder Weekly** https://www.boulderweekly.com and archives.boulderweekly.com | 2023 recap/analysis. 2026 city-council questionnaire not found in this pass (searched; did not fetch the full 2026 section). | Historical. Confirm 2025/2026 questionnaires on a dedicated pass. |
| **Axios Boulder** | Wallach resignation, local briefs. Mitchell Byars. | Short, dated, good for events. |
| **CU Independent** | 2025 results; noted the even-year/three-year-term transition. | Secondary. |
| **Denver Post** | 2023 RCV horse-race. | Not a 2026 primary source. |
| KGNU / CPR | Not harvested this pass. | Radio forum recordings likely exist. |

## Forums / civic orgs

| Host | What they do | 2026 status |
|---|---|---|
| **Boulder Chamber** | Season-opener forum every year. 2026: Aug 26, 5–8pm, eTown. | Happened. Need recording + who showed + questions. |
| **Boulder Progressives** | Raucous Caucus (June 6 2026, Twisted Pine). Endorses. | BRL wrote it up; seven then-declared candidates on stage. |
| **League of Women Voters of Boulder County** | Candidate forums + Vote411 questionnaires. Nonpartisan. | 2026 page exists and points at Vote411; city-council forum dates not posted in the slice we fetched. |
| **PLAN-Boulder County** | Endorsements, often the more conservation / slower-growth pole. | 2025 endorsed Wallach et al. 2026 questionnaire/forum not yet fetched. |
| **Open Boulder** | Endorsements, housing-supply pole. | 2025. |
| **Sierra Club Indian Peaks** | Isaacson is on the exec committee (BRL). Forum TBD. | |
| Neighborhood associations / eTown / KGNU | Historically host. | Calendar empty in this seed. |

## Aggregators

- **Vote411.org** — LWV. Will matter when questionnaires open. Not a substitute for local ingest.
- **Ballotpedia** — noisy (Boulder *City*, Nevada pollutes searches). Not relied on.
- **TRACER** (Colorado SOS) — **does not cover City of Boulder municipal campaigns**. Use the city clerk.

## Campaign self-publish

Verified this pass: [taraforboulder.com](https://www.taraforboulder.com/) (Tara Winer). Others not found in a short search; they exist, they just were not in the first result set. Do not invent URLs.

## What 2023 and 2025 actually were (certified)

**2023-11-07** — 34,249 city ballots, 68,812 active city voters.

Mayor RCV (official summary):

| | Round 1 | Round 2 |
|---|---|---|
| Aaron Brockett | 11,504 | **16,823 (elected)** |
| Bob Yates | 14,271 | 15,592 |
| Nicole Speer | 6,369 | eliminated |
| Paul Tweedlie | 749 | eliminated |

Council (recount-certified):

1. Tara Winer 21,255
2. Tina Marquis 14,958
3. Taishya Adams 14,633
4. Ryan Schuchard 14,411 **(won by 46 over Brncic)**
5. Terri Brncic 14,365
6. Jennifer Robins 11,249
7. Waylon Lewis 8,862
8. Silas Atkins 6,829
9. Aaron Gabriel Neyer 3,483
10. Jacques Decalo 3,329

**2025-11-04** — four seats, plurality, 11 candidates. Clarity ENR (matches Daily Camera seating totals for top four):

1. Matt Benjamin 20,276
2. Mark Wallach 17,476
3. Nicole Speer 16,165
4. Rob Kaplan 15,867
5. Jennifer Robins 14,781
6. Lauren Folkerts 14,222
7. Rachel Rose Isaacson 5,085
8. Montserrat Palacios 2,957
9. Maxwell Lord 2,853
10. Aaron Stone 2,707
11. Rob Smoke 1,499

## 2026 field (clerk, retrieved 2026-08-26)

**Mayor (RCV, 1):** Taishya Adams (8-5), Fred Smith (8-10), Aaron Brockett (8-11, matching funds), Jameson Goldstein (8-24), Lisa Ann Jacobs (8-24), Aquiles La Grave (8-24).

**Council (plurality, 5):** Rachel Rose Isaacson (8-4, matching), Tara Winer (8-5, matching), Ryan Schuchard (8-6), Jill Grano (8-6), Benita Duran (8-7), Ryan Jamieson (8-10), Lee Gilbert (8-17), Tina Marquis (8-17, matching), Jamillah Richmond (8-17), Sam Fuqua (8-18), Lynn Segal (8-20), David Martus (8-24), Scott Rendleman (8-24).

## Issues already on the table (from coverage, not from us)

Housing / Area III / middle-income supply · municipal airport + FAA grant assurances · tipped wage vs city minimum · budget shortfall / rec-center bonds / vacancy tax · wildfire hardening of existing homes · homelessness / camping ban · transportation (Iris, 30th) · whether council speaks on foreign affairs.

BRL’s June 7 2026 caucus piece is the first *binary* issue harvest: FAA grants — Brockett, Duran, Winer yes; Marquis, Schuchard, Grano, Isaacson no. That is a journalist’s grouping of spoken answers, stored as such.

## Forum calendar harvested 2026-08-27

**2023**
- Progressives, June 21, Elks Lodge (BRL June 23). Eight council + three mayor; full roster not copied.
- PLAN, Aug 23: four mayor + Adams + Decalo. PLAN, Aug 29: Winer, Brncic, Lewis, Marquis, Schuchard, Neyer, Robins. Source: planboulder.org/boulder-election-2023. Venues not on that page.
- Chamber, Aug 29, Boulder JCC. All 14; Speer virtual. Recording: youtube.com/watch?v=AEkK1eSLmNk
- Climate mayoral, ~Oct 5 (BRL Oct 6, Xcel).
- LWV council, Oct 15, Channel 8: youtube.com/watch?v=Xb83hgpphXo
- BRL–KGNU mayoral debate ~Oct 18 (mentioned in BRL Oct 27 caption; recording not located).
- LWV mayor, Oct 22: youtube.com/watch?v=n89j6Wk-qc8 — Brockett, Speer, Tweedlie, Yates in the transcript.

**2025**
- Chamber, Aug 26, New Vista. Ten of eleven; Palacios not named. Recording: youtube.com/watch?v=a-6Mso1bNhA (Chamber upload titled “2025 City Council Candidate Forum”).
- VOTES! Collaborative (Open Boulder / Better Boulder / PLAN), Sept 8, Nomad Playhouse. Eight present; Palacios, Smoke, Stone absent (Daily Camera Sept 6). Recording promised, not located.
- LWV + EFAA, Sept 27, Council Chambers. 8 of 11, all invited (moderator on tape). Recording: youtube.com/watch?v=JcJu9nd5mQk

**2026**
- Raucous Caucus June 6 (BRL). Chamber Aug 26 parked until they publish.

BRL questionnaires ingested via WP JSON: 2023 14×6, 2025 11×6.

## Best next harvest (ordered)

1. 2026 Chamber forum when the Chamber releases recording/materials.
2. City campaign-finance filings once the first required statements land.
3. Remaining 2026 campaign websites (do not guess).
4. LWV / Vote411 2026 questionnaire when it opens.
5. Name-by-name attendance from the 2023/2025 LWV videos (watch, don’t invent).
6. 2025 2A/2B certified yes/no from the county SOV.
7. BRL vote tracker → officeholder voting record, later.

## Out of scope until we say so

County races, BVSD, state, live social proof, AT Proto identities. The schema can grow a `did` column on `people` without rearranging the world.
