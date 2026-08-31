-- bouldervotes.org — civic evidence graph, not a brochure.
-- SQLite now; column types chosen so this can lift to Cloudflare D1 later.
-- Every public-facing fact should be joinable to a source.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  sort_name TEXT NOT NULL,          -- "Brockett, Aaron"
  notes TEXT
);

CREATE TABLE IF NOT EXISTS organizations (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  kind TEXT NOT NULL,               -- government | newspaper | forum_host | advocacy | civic | other
  website TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS offices (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,               -- "Mayor of Boulder" | "Boulder City Council"
  jurisdiction TEXT NOT NULL,       -- "City of Boulder"
  typical_seats INTEGER NOT NULL,
  term_years INTEGER NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS elections (
  id INTEGER PRIMARY KEY,
  year INTEGER NOT NULL,
  date TEXT NOT NULL,               -- ISO date
  jurisdiction TEXT NOT NULL,
  kind TEXT NOT NULL,               -- municipal_coordinated
  notes TEXT,
  UNIQUE (year, jurisdiction, kind)
);

CREATE TABLE IF NOT EXISTS races (
  id INTEGER PRIMARY KEY,
  election_id INTEGER NOT NULL REFERENCES elections(id),
  office_id INTEGER NOT NULL REFERENCES offices(id),
  seats_open INTEGER NOT NULL,
  voting_method TEXT NOT NULL,      -- plurality | ranked_choice
  notes TEXT,
  UNIQUE (election_id, office_id)
);

CREATE TABLE IF NOT EXISTS candidacies (
  id INTEGER PRIMARY KEY,
  person_id INTEGER NOT NULL REFERENCES people(id),
  race_id INTEGER NOT NULL REFERENCES races(id),
  status TEXT NOT NULL,             -- certified | withdrawn | elected | lost
  is_incumbent INTEGER NOT NULL DEFAULT 0,
  certified_on TEXT,                -- ISO date
  matching_funds INTEGER NOT NULL DEFAULT 0,
  campaign_url TEXT,
  notes TEXT,
  UNIQUE (person_id, race_id)
);

CREATE TABLE IF NOT EXISTS officeholders (
  id INTEGER PRIMARY KEY,
  person_id INTEGER NOT NULL REFERENCES people(id),
  office_id INTEGER NOT NULL REFERENCES offices(id),
  role TEXT,                        -- mayor | mayor_pro_tem | councilmember
  term_start TEXT NOT NULL,
  term_end TEXT,
  how_ended TEXT,                   -- elected | term_ended | resigned
  notes TEXT
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  published_on TEXT,
  org_id INTEGER REFERENCES organizations(id),
  kind TEXT NOT NULL,               -- official | article | questionnaire | video | campaign_site | results
  year INTEGER,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS source_mentions (
  source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  person_id INTEGER REFERENCES people(id),
  candidacy_id INTEGER REFERENCES candidacies(id),
  race_id INTEGER REFERENCES races(id),
  event_id INTEGER,
  PRIMARY KEY (source_id, person_id, candidacy_id, race_id, event_id)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  starts_on TEXT NOT NULL,
  venue TEXT,
  host_org_id INTEGER REFERENCES organizations(id),
  kind TEXT NOT NULL,               -- forum | caucus | debate | other
  recording_url TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS event_appearances (
  event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  candidacy_id INTEGER REFERENCES candidacies(id),
  person_id INTEGER REFERENCES people(id),
  attended INTEGER,                 -- 1 yes, 0 no, NULL unknown
  notes TEXT,
  PRIMARY KEY (event_id, person_id)
);

CREATE TABLE IF NOT EXISTS issues (
  slug TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS questions (
  id INTEGER PRIMARY KEY,
  prompt TEXT NOT NULL,
  issue_slug TEXT REFERENCES issues(slug),
  year INTEGER,                     -- cycle this prompt was asked; NULL if reused
  kind TEXT NOT NULL DEFAULT 'questionnaire',  -- questionnaire | forum | interview | other
  is_canonical INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY,
  candidacy_id INTEGER REFERENCES candidacies(id),
  person_id INTEGER NOT NULL REFERENCES people(id),
  question_id INTEGER NOT NULL REFERENCES questions(id),
  source_id INTEGER NOT NULL REFERENCES sources(id),
  event_id INTEGER REFERENCES events(id),
  kind TEXT NOT NULL DEFAULT 'questionnaire',  -- questionnaire | forum | interview | other
  stance TEXT,                      -- yes | no | mixed | unknown — only when the source is binary
  verbatim TEXT,                    -- quote or close paraphrase, attributed
  answered_on TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS measures (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  election_id INTEGER NOT NULL REFERENCES elections(id),
  letter TEXT,                      -- 2A, 2B, etc. NULL until the county assigns
  title TEXT NOT NULL,
  kind TEXT NOT NULL,               -- bond | tax | charter | other
  status TEXT NOT NULL,             -- referred | on_ballot | passed | failed | not_referred
  summary TEXT,
  ballot_language TEXT,
  source_id INTEGER REFERENCES sources(id),
  notes TEXT
);

CREATE TABLE IF NOT EXISTS measure_results (
  measure_id INTEGER NOT NULL REFERENCES measures(id),
  yes_votes INTEGER,
  no_votes INTEGER,
  passed INTEGER NOT NULL DEFAULT 0,
  source_id INTEGER REFERENCES sources(id),
  notes TEXT,
  PRIMARY KEY (measure_id)
);

CREATE TABLE IF NOT EXISTS results (
  candidacy_id INTEGER NOT NULL REFERENCES candidacies(id),
  round INTEGER NOT NULL DEFAULT 1, -- RCV round; 1 for plurality
  votes INTEGER NOT NULL,
  vote_share REAL,
  place INTEGER,
  elected INTEGER NOT NULL DEFAULT 0,
  source_id INTEGER REFERENCES sources(id),
  notes TEXT,
  PRIMARY KEY (candidacy_id, round)
);

CREATE TABLE IF NOT EXISTS finance_snapshots (
  id INTEGER PRIMARY KEY,
  person_id INTEGER REFERENCES people(id),
  candidacy_id INTEGER REFERENCES candidacies(id),
  year INTEGER NOT NULL,
  committee_name TEXT NOT NULL,
  contributions REAL,
  expenditures REAL,
  matching_received REAL,
  reported_on TEXT,
  source_id INTEGER REFERENCES sources(id),
  notes TEXT
);

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidacies_race ON candidacies(race_id);
CREATE INDEX IF NOT EXISTS idx_candidacies_person ON candidacies(person_id);
CREATE INDEX IF NOT EXISTS idx_answers_person ON answers(person_id);
CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_results_candidacy ON results(candidacy_id);
CREATE INDEX IF NOT EXISTS idx_sources_year ON sources(year);
CREATE INDEX IF NOT EXISTS idx_measures_election ON measures(election_id);
