#!/usr/bin/env python3
"""Harvest Boulder Reporting Lab candidate questionnaires into data/harvest/.

Uses the public WordPress JSON API. Answers stay attached to the BRL URL.
Name aliases are explicit; unknown H2s are reported and skipped.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "harvest" / "brl_questionnaires.json"

# BRL heading → people.full_name in seed.py
ALIASES = {
    "jenny robins": "Jennifer Robins",
    "jenny robbins": "Jennifer Robins",
    "jennifer robins": "Jennifer Robins",
    "max lord": "Maxwell Lord",
    "maxwell lord": "Maxwell Lord",
    "montserrat palacios rodarte": "Montserrat Palacios",
    "montserrat palacios": "Montserrat Palacios",
    "aaron neyer": "Aaron Gabriel Neyer",
    "aaron gabriel neyer": "Aaron Gabriel Neyer",
    "taishya adams": "Taishya Adams",
    "silas atkins": "Silas Atkins",
    "terri brncic": "Terri Brncic",
    "aaron brockett": "Aaron Brockett",
    "jacques decalo": "Jacques Decalo",
    "waylon lewis": "Waylon Lewis",
    "tina marquis": "Tina Marquis",
    "paul tweedlie": "Paul Tweedlie",
    "ryan schuchard": "Ryan Schuchard",
    "nicole speer": "Nicole Speer",
    "tara winer": "Tara Winer",
    "bob yates": "Bob Yates",
    "matt benjamin": "Matt Benjamin",
    "lauren folkerts": "Lauren Folkerts",
    "rachel rose isaacson": "Rachel Rose Isaacson",
    "rob kaplan": "Rob Kaplan",
    "rob smoke": "Rob Smoke",
    "aaron stone": "Aaron Stone",
    "mark wallach": "Mark Wallach",
}

POSTS = [
    # 2023 — six questions, all 14 candidates (BRL)
    {
        "year": 2023,
        "slug": "2023-boulder-city-council-election-where-the-candidates-stand-on-homelessness-solutions",
        "prompt": "What do you think are the most promising initiatives for reducing homelessness?",
        "issue": "homelessness",
        "binary": False,
    },
    {
        "year": 2023,
        "slug": "2023-boulder-city-council-election-where-the-candidates-stand-on-homeless-encampments",
        "prompt": "What approach would you take to address camping in our parks, on our bike paths and along our waterways?",
        "issue": "homelessness",
        "binary": False,
    },
    {
        "year": 2023,
        "slug": "2023-boulder-city-council-election-where-the-candidates-stand-on-affordable-housing",
        "prompt": "What is your plan for increasing Boulder’s affordable housing supply?",
        "issue": "housing",
        "binary": False,
    },
    {
        "year": 2023,
        "slug": "2023-boulder-city-council-election-where-the-candidates-stand-on-climate-change-action",
        "prompt": "We are in a climate emergency. With your leadership, how would Boulder change commensurately?",
        "issue": "climate",
        "binary": False,
    },
    {
        "year": 2023,
        "slug": "2023-boulder-city-council-election-where-the-candidates-stand-on-making-streets-safer-for-cyclists-walkers-and-others",
        "prompt": "How can we better provide alternatives to cars when existing infrastructure prioritizes cars?",
        "issue": "transportation",
        "binary": False,
    },
    {
        "year": 2023,
        "slug": "2023-boulder-city-council-election-where-the-candidates-stand-on-their-one-year-visions",
        "prompt": "Assume you are elected this November. What one specific thing will you have accomplished that you’re proud of after one year?",
        "issue": None,
        "binary": False,
    },
    # 2025 — six questions, all 11 candidates (BRL)
    {
        "year": 2025,
        "slug": "2025-boulder-city-council-election-how-candidates-say-their-life-experiences-would-shape-their-work-on-council",
        "prompt": "What perspective or lived experience would you bring to city council, and how would it shape your approach to policy?",
        "issue": None,
        "binary": False,
    },
    {
        "year": 2025,
        "slug": "2025-boulder-city-council-election-where-candidates-stand-on-the-camping-ban",
        "prompt": "Should Boulder enforce its camping ban when the All Roads shelter is full?",
        "issue": "homelessness",
        "binary": True,
    },
    {
        "year": 2025,
        "slug": "2025-boulder-city-council-election-where-candidates-stand-on-making-the-city-more-wildfire-resilient",
        "prompt": "Should Boulder require existing homes (not just new construction) to meet wildfire mitigation standards — such as clearing five feet around structures and banning wood fences near homes?",
        "issue": "wildfire",
        "binary": True,
    },
    {
        "year": 2025,
        "slug": "2025-boulder-city-council-election-where-candidates-stand-on-the-councils-role-in-foreign-affairs",
        "prompt": "Should Boulder City Council weigh in on foreign affairs? If not, how should it handle protests and tensions in council chambers over the war in Gaza?",
        "issue": "foreign-affairs",
        "binary": False,
    },
    {
        "year": 2025,
        "slug": "2025-boulder-city-council-election-where-candidates-stand-on-the-housing-shortage",
        "prompt": "Boulder needs thousands of new homes by 2032. What specific actions would you take to overcome barriers and increase housing supply?",
        "issue": "housing",
        "binary": False,
    },
    {
        "year": 2025,
        "slug": "2025-boulder-city-council-election-where-candidates-stand-on-priorities-for-the-city-budget",
        "prompt": "With sales tax revenue slowing, a hiring freeze, and a $380 million maintenance backlog, what would be your top spending priorities — and what would you cut or delay?",
        "issue": "budget",
        "binary": False,
    },
]


def clean_text(s: str) -> str:
    s = html_unescape(s)
    s = s.replace("\xa0", " ").replace("&nbsp;", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def html_unescape(s: str) -> str:
    import html as html_mod
    return html_mod.unescape(s)


def canonical_name(raw: str) -> str | None:
    key = re.sub(r"\s+", " ", raw).strip().lower()
    key = re.sub(r"\s*\([^)]*\)\s*", " ", key).strip()
    key = key.strip("*: ")
    return ALIASES.get(key)


class BlockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_h = False
        self._in_p = False
        self._buf = ""
        self.blocks: list[tuple[str, list[str]]] = []
        self._current: str | None = None
        self.skipped_headings: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in ("h2", "h3"):
            self._in_h = True
            self._buf = ""
        elif tag == "p":
            self._in_p = True
            self._buf = ""

    def handle_data(self, data: str) -> None:
        if self._in_h or self._in_p:
            self._buf += data

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h2", "h3") and self._in_h:
            self._in_h = False
            heading = clean_text(self._buf)
            name = canonical_name(heading)
            if name:
                self._current = name
                self.blocks.append((name, []))
            else:
                if heading:
                    self.skipped_headings.append(heading)
                # Non-name heading ends the current candidate block.
                self._current = None
        elif tag == "p" and self._in_p:
            self._in_p = False
            text = clean_text(self._buf)
            if text and self._current and self.blocks:
                self.blocks[-1][1].append(text)


def stance_from(text: str, binary: bool) -> str | None:
    if not binary:
        return None
    lead = text.lstrip().lower()
    if lead.startswith("yes"):
        return "yes"
    if lead.startswith("no"):
        return "no"
    return "mixed"


def fetch_post(slug: str) -> dict:
    url = (
        "https://boulderreportinglab.org/wp-json/wp/v2/posts"
        f"?slug={slug}&_fields=id,date,slug,link,title,content"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "bouldervotes.org harvest/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        posts = json.load(resp)
    if not posts:
        raise SystemExit(f"no WP post for slug={slug}")
    return posts[0]


def main() -> None:
    harvested = []
    problems = []
    for spec in POSTS:
        post = fetch_post(spec["slug"])
        parser = BlockParser()
        parser.feed(post["content"]["rendered"])
        answers = []
        seen = set()
        for name, paras in parser.blocks:
            if name in seen:
                problems.append(f"duplicate {name} in {spec['slug']}")
                continue
            seen.add(name)
            verbatim = "\n\n".join(paras).strip()
            if not verbatim:
                problems.append(f"empty answer {name} in {spec['slug']}")
                continue
            answers.append(
                {
                    "person": name,
                    "verbatim": verbatim,
                    "stance": stance_from(verbatim, spec["binary"]),
                }
            )
        harvested.append(
            {
                "year": spec["year"],
                "slug": spec["slug"],
                "url": post["link"],
                "title": clean_text(post["title"]["rendered"]),
                "published_on": post["date"][:10],
                "prompt": spec["prompt"],
                "issue": spec["issue"],
                "binary": spec["binary"],
                "skipped_headings": parser.skipped_headings,
                "answers": answers,
            }
        )
        print(f"{spec['year']} {spec['slug']}: {len(answers)} answers")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "harvested_at": "2026-08-27",
        "source": "Boulder Reporting Lab WP JSON",
        "posts": harvested,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n = sum(len(p["answers"]) for p in harvested)
    print(f"wrote {OUT} posts={len(harvested)} answers={n}")
    if problems:
        print("problems:", *problems, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
