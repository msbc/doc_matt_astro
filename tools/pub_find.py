#!/usr/bin/env python
"""Find my publications in SciX (the successor to NASA ADS) and print/save BibTeX.

    uv run tools/pub_find.py                 print BibTeX to the terminal
    uv run tools/pub_find.py -o pubs.bib     save it to a file
    uv run tools/pub_find.py -f apj          ApJ-style citations (also: bibtex, bibcodes, dict)
    uv run tools/pub_find.py --site          update the website's publications list (data/publications.js)

The API token is NOT stored in this file.  It is looked up, in order, from:
  1. the --token command-line flag (note: visible in shell history and `ps`)
  2. the file named by --token-file (one line, the token)
  3. the SCIX_API_TOKEN environment variable
  4. the ADS_DEV_KEY environment variable (the older ADS name)
  5. the file ~/.ads/dev_key (the usual ADS client location)
Get a token from https://scixplorer.org/user/settings/token

Structure
  SciXClient          talks to the SciX API (search, BibTeX export); owns the token
  OrcidClient         reads my public works list from the ORCID registry (no token)
  OrcidWork           one entry of that list, with its identifiers
  Publication         one BibTeX entry, parsed, with a sort key
  PublicationSource   something that yields bibcodes; subclass it to add a way of
                      finding papers (co-author search, SciX ORCID tags, ORCID registry,
                      a SciX library)
  PublicationFinder   merges the sources, fetches BibTeX, drops ignored entries,
                      sorts newest first
  OutputFormat        renders the Publications as text; one subclass per --format
  SitePage            writes the Publications into the website's data/publications.js
"""

import argparse
import json
import os
import pprint
import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

import requests

# --- CONFIG: edit these ---
# Use "Last, F. M." style as ADS expects (can be forgiving, but this helps).
ME = "Coleman, Matthew"  # e.g., "Coleman, Matthew S."
PIS = [
    "Blaes, Omer",
    "Rafikov, Roman",
    "Burrows, Adam",
    "Thompson, Todd",
]

# Your ORCID is the most precise filter.
MY_ORCID = "0000-0001-5939-5957"

# My "My Publications" library on SciX (https://scixplorer.org/user/libraries/<id>).
MY_LIBRARY = "GTuDTOy9Qx6mHB1Vk5aquQ"

# Ignore list: publications to skip (e.g., non-refereed)
IGNORE = ["2021arXiv211100022C", "2000ccdc.data.5353B", "2017PhDT.......294C"]

# Skip publications from before this year (None = no limit).
MIN_YEAR = 2014

# The website page that --site updates (relative paths are resolved from the current directory).
SITE_FILE = Path(__file__).resolve().parent.parent / "data" / "publications.js"

TIMEOUT = 60  # seconds, for every request
NOT_FOUND_STATUSES = (404, 500)

MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


class ApiError(Exception):
    """A request to SciX or ORCID failed; the message is meant to be shown to the user."""


def call(send, url, service, not_found=None, **kwargs):
    """Make a request with `send` (e.g. session.get) and return the response.

    Network problems and HTTP errors become an ApiError with a readable message.
    `not_found` is the message for statuses that mean "no such thing" (404, and
    SciX libraries answer 500 for an unknown id), e.g. "SciX library 'abc' not found".
    """
    try:
        response = send(url, timeout=TIMEOUT, **kwargs)
    except requests.exceptions.Timeout:
        raise ApiError(f"{service} did not answer within {TIMEOUT} seconds.") from None
    except requests.exceptions.RequestException as exc:
        raise ApiError(f"Could not reach {service} ({type(exc).__name__}). Check your network connection.") from None
    status = response.status_code
    if response.ok:
        return response
    if status in (401, 403) and service == "SciX":
        raise ApiError(
            f"SciX rejected the API token (HTTP {status}). Check --token, --token-file, "
            "SCIX_API_TOKEN or ~/.ads/dev_key, and that the token hasn't been revoked."
        )
    if status == 429:
        raise ApiError(f"{service} rate limit reached (HTTP 429). Wait a while and try again.")
    if not_found and status in NOT_FOUND_STATUSES:
        raise ApiError(f"{not_found} (HTTP {status}).")
    raise ApiError(f"{service} request failed: HTTP {status} {response.reason}.")


class SciXClient:
    """Minimal client for the SciX API (same API as ADS)."""

    # api.adsabs.harvard.edu/v1 also still works.
    BASE_URL = "https://api.scixplorer.org/v1"
    TOKEN_ENV_VARS = ("SCIX_API_TOKEN", "ADS_DEV_KEY")
    TOKEN_FILE = Path.home() / ".ads" / "dev_key"
    MAX_ROWS = 2000  # the API returns only 10 rows unless asked for more

    def __init__(self, token=None, token_file=None):
        self.session = requests.Session()
        token = token or self.find_token(token_file)
        self.session.headers["Authorization"] = "Bearer " + token

    @staticmethod
    def read_token_file(path):
        """Return the stripped contents of a token file, or "" if missing/empty."""
        path = Path(path).expanduser()
        return path.read_text().strip() if path.is_file() else ""

    @classmethod
    def find_token(cls, token_file=None):
        """Return the token from an explicit file, the environment or the default file, or exit."""
        if token_file:
            # An explicitly named file must work; don't silently fall back to another token.
            token = cls.read_token_file(token_file)
            if not token:
                sys.exit(f"Token file {token_file} is missing or empty.")
            return token
        for var in cls.TOKEN_ENV_VARS:
            if os.environ.get(var, "").strip():
                return os.environ[var].strip()
        token = cls.read_token_file(cls.TOKEN_FILE)
        if token:
            return token
        sys.exit(
            "No SciX API token found. Set SCIX_API_TOKEN or put the token in "
            f"{cls.TOKEN_FILE} (get one at https://scixplorer.org/user/settings/token)."
        )

    def search(self, query, fq=None):
        """Return the bibcodes matching a SciX/ADS query string (`fq`: an extra filter, e.g. "property:refereed")."""
        params = {"q": query, "fl": "bibcode", "rows": self.MAX_ROWS}
        if fq:
            params["fq"] = fq
        response = call(self.session.get, f"{self.BASE_URL}/search/query", "SciX", params=params)
        return [doc["bibcode"] for doc in response.json()["response"]["docs"]]

    def lookup(self, identifiers, chunk=50, fq=None):
        """Return the bibcodes of records matching any identifier (DOI, "arXiv:...", bibcode)."""
        identifiers = sorted(set(identifiers))
        found = []
        for i in range(0, len(identifiers), chunk):
            terms = " OR ".join(f'"{v}"' for v in identifiers[i : i + chunk])
            # (`doi:(...)` with a group is a syntax error in SciX; `identifier:(...)` works and matches DOIs too.)
            found.extend(self.search(f"identifier:({terms})", fq))
        return found

    def refereed(self, bibcodes):
        """Return the subset of `bibcodes` that SciX marks as refereed."""
        return set(self.lookup(bibcodes, fq="property:refereed"))

    def library_bibcodes(self, library_id, page=100):
        """Return the bibcodes in a SciX library (one you own, or a public one)."""
        bibcodes = []
        while True:
            response = call(
                self.session.get,
                f"{self.BASE_URL}/biblib/libraries/{library_id}",
                "SciX",
                not_found=f"SciX library '{library_id}' not found, or not visible to this token",
                params={"start": len(bibcodes), "rows": page},
            )
            data = response.json()
            bibcodes.extend(data["documents"])
            if not data["documents"] or len(bibcodes) >= data["metadata"]["num_documents"]:
                return bibcodes

    def export_bibtex(self, bibcodes):
        """Return one BibTeX string covering all the given bibcodes."""
        response = call(
            self.session.post,
            f"{self.BASE_URL}/export/bibtex",
            "SciX",
            json={"bibcode": list(bibcodes)},
        )
        return response.json()["export"]


@dataclass
class OrcidWork:
    """One work from an ORCID record, with the identifiers needed to find it in SciX."""

    title: str
    year: str
    bibcodes: list = field(default_factory=list)
    dois: list = field(default_factory=list)
    arxiv_ids: list = field(default_factory=list)

    @classmethod
    def from_group(cls, group):
        """Build from one entry of the ORCID `group` list (duplicates already merged by ORCID)."""
        summary = group["work-summary"][0]
        date = summary.get("publication-date") or {}
        work = cls(
            title=summary["title"]["title"]["value"],
            year=(date.get("year") or {}).get("value", ""),
        )
        targets = {"bibcode": work.bibcodes, "doi": work.dois, "arxiv": work.arxiv_ids}
        for ext in group["external-ids"]["external-id"]:
            # "self" means the work itself; "part-of" would be e.g. the proceedings volume.
            if ext["external-id-relationship"] == "self" and ext["external-id-type"] in targets:
                targets[ext["external-id-type"]].append(ext["external-id-value"].strip())
        return work


class OrcidClient:
    """Reads a public ORCID record (no authentication needed)."""

    BASE_URL = "https://pub.orcid.org/v3.0"

    def works(self, orcid):
        response = call(
            requests.get,
            f"{self.BASE_URL}/{orcid}/works",
            "ORCID",
            not_found=f"ORCID record '{orcid}' not found",
            headers={"Accept": "application/json"},
        )
        return [OrcidWork.from_group(g) for g in response.json()["group"]]


def tex_to_text(text):
    """Light LaTeX clean-up for BibTeX values: accents, braces, ties.  Not a full converter.

    Text between $...$ is math and is left alone.
    """
    parts = text.split("$")
    for i in range(0, len(parts), 2):  # even-numbered parts are outside math
        part = re.sub(r"\\[`'^\"~=.uvHcdbk]\s*\{?\\?([A-Za-z])\}?", r"\1", parts[i])  # \'e, \={\i}, ...
        part = part.replace("\\&", "&").replace("~", " ")
        parts[i] = re.sub(r"[{}]", "", part)
    return "$".join(parts).strip()


SUPERSCRIPT = str.maketrans("0123456789+-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻")
SUBSCRIPT = str.maketrans("0123456789+-", "₀₁₂₃₄₅₆₇₈₉₊₋")
MATH_SYMBOLS = {
    r"\odot": "☉",
    r"\sim": "~",
    r"\times": "×",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\mu": "μ",
}


def math_to_text(text):
    """Replace simple inline math with plain Unicode: "$^{56}$Ni" -> "⁵⁶Ni", "M$_\\odot$" -> "M☉".

    Math this can't convert is left as it was ($...$ and all), so callers can spot it with `"$" in text`.
    """

    def convert(match):
        body = re.sub(r"\^\{?([0-9+-]+)\}?", lambda m: m.group(1).translate(SUPERSCRIPT), match.group(1))
        body = re.sub(r"_\{?([0-9+-]+)\}?", lambda m: m.group(1).translate(SUBSCRIPT), body)
        for tex, char in MATH_SYMBOLS.items():
            body = re.sub(rf"_?\{{?{re.escape(tex)}\}}?", char, body)
        return match.group(0) if re.search(r"[\\^_{}]", body) else body.strip()

    return re.sub(r"\$([^$]*)\$", convert, text)


class Author(NamedTuple):
    last: str
    given: str = ""

    @property
    def initials(self):
        """ "Matthew S.~B." -> "M. S. B."; hyphenated parts keep the hyphen ("T.-H.")."""
        tokens = self.given.replace("~", " ").split()
        return " ".join("-".join(f"{part[0]}." for part in tok.split("-") if part) for tok in tokens)

    @property
    def last_initials(self):
        return f"{self.last}, {self.initials}" if self.initials else self.last

    @property
    def last_first(self):
        return f"{self.last}, {self.given}" if self.given else self.last


@dataclass
class Publication:
    """One BibTeX entry."""

    bibcode: str
    entry_type: str
    fields: dict
    bibtex: str

    @classmethod
    def from_bibtex(cls, entry):
        """Parse one entry; return None if it doesn't look like BibTeX."""
        lines = entry.strip().split("\n")
        if not lines[0].startswith("@"):
            return None
        entry_type, rest = lines[0][1:].split("{", 1)
        fields = {}
        for line in lines[1:]:
            if "=" in line:
                key, value = line.split("=", 1)
                fields[key.strip()] = value.strip().rstrip(",")
        return cls(rest.rstrip(","), entry_type, fields, entry)

    @property
    def year(self):
        return int(self.fields["year"])

    @property
    def month_number(self):
        month = self.fields.get("month", "").lower()
        return f"{MONTHS.index(month) + 1:02d}" if month in MONTHS else "00"

    @property
    def sort_key(self):
        """Year, month, then arXiv id and DOI as tie-breakers."""
        parts = [self.fields["year"], self.month_number, self.fields.get("eprint", ""), self.fields.get("doi", "")]
        return "_".join(parts)

    def get(self, key, default=""):
        """A field with its BibTeX quoting/braces and LaTeX removed."""
        value = self.fields.get(key)
        if value is None:
            return default
        value = value.strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        return tex_to_text(value)

    @property
    def authors(self):
        raw = self.fields.get("author", "").strip()
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        authors = []
        for name in re.split(r"\s+and\s+", raw):
            last, _, given = tex_to_text(name).partition(",")
            if last:
                authors.append(Author(last.strip(), given.strip()))
        return authors

    @property
    def journal_abbrev(self):
        """ADS's standard abbreviation (ApJ, MNRAS, PhRvD, ...): it is baked into the bibcode."""
        return self.bibcode[4:9].strip(".")

    @property
    def first_page(self):
        """First page or article number ("490-517" -> "490")."""
        return (self.get("pages") or self.get("eid")).split("-")[0].strip()

    @property
    def venue(self):
        """Where it appeared: journal/volume/page, a thesis, or an arXiv preprint."""
        if self.entry_type.lower() == "phdthesis":
            return ", ".join(filter(None, ["PhD thesis", self.get("school")]))
        if self.journal_abbrev == "arXiv":
            return f"arXiv:{self.get('eprint')}"
        volume = self.get("volume")
        if volume == str(self.year):  # meeting abstracts use the year as the "volume"
            volume = ""
        return ", ".join(filter(None, [self.journal_abbrev, volume, self.first_page]))

    def to_dict(self):
        month = self.month_number
        return {
            "bibcode": self.bibcode,
            "type": self.entry_type.lower(),
            "authors": [a.last_first for a in self.authors],
            "title": self.get("title") or None,
            "journal": self.journal_abbrev,
            "year": self.year,
            "month": int(month) or None,
            "volume": self.get("volume") or None,
            "issue": self.get("number") or None,
            "page": self.first_page or None,
            "doi": self.get("doi") or None,
            "arxiv": self.get("eprint") or None,
            "url": self.get("adsurl") or None,
        }


class PublicationSource(ABC):
    """A way of finding my papers.  Each source returns SciX bibcodes."""

    @abstractmethod
    def find(self) -> Iterable[str]:
        """Return an iterable of bibcodes."""


class CoauthorSource(PublicationSource):
    """Papers on which I am an author together with one of the given co-authors."""

    def __init__(self, client, me, coauthors):
        self.client = client
        self.me = me
        self.coauthors = coauthors

    def query(self, coauthor):
        # Author filters AND together.
        return " AND ".join(f'author:("{name}")' for name in (self.me, coauthor))

    def find(self) -> Iterable[str]:
        for coauthor in self.coauthors:
            yield from self.client.search(self.query(coauthor))


class SciXOrcidSource(PublicationSource):
    """Papers that SciX has already tagged with my ORCID."""

    def __init__(self, client, orcid):
        self.client = client
        self.orcid = orcid.strip()

    def find(self) -> Iterable[str]:
        return self.client.search(f'orcid:"{self.orcid}"')


class LibrarySource(PublicationSource):
    """Every paper in a SciX library."""

    def __init__(self, client, library):
        self.client = client
        # Accept either the bare id or the full https://scixplorer.org/user/libraries/<id> URL.
        self.library_id = library.strip().rstrip("/").rsplit("/", 1)[-1]

    def find(self) -> Iterable[str]:
        return self.client.library_bibcodes(self.library_id)


class OrcidRegistrySource(PublicationSource):
    """Works listed on my ORCID record.

    A work that carries a bibcode is used as is; the rest are looked up in SciX by
    DOI and arXiv id.  Works SciX can't match are kept in `unresolved`.
    """

    def __init__(self, client, orcid_client, orcid):
        self.client = client
        self.orcid_client = orcid_client
        self.orcid = orcid.strip()
        self.unresolved = []

    def resolve(self, work):
        """Return SciX bibcodes for one work ([] if SciX doesn't know it)."""
        if work.bibcodes:
            return work.bibcodes
        return self.client.lookup(work.dois + [f"arXiv:{a}" for a in work.arxiv_ids])

    def find(self) -> Iterable[str]:
        self.unresolved = []
        found = set()
        for work in self.orcid_client.works(self.orcid):
            bibcodes = self.resolve(work)
            if bibcodes:
                found.update(bibcodes)
            else:
                self.unresolved.append(work)
        return found


class PublicationFinder:
    """Combine sources into a sorted, de-duplicated list of Publications."""

    def __init__(self, client, sources, ignore=(), min_year=None):
        self.client = client
        self.sources = list(sources)
        self.ignore = set(ignore)
        self.min_year = min_year

    def bibcodes(self):
        found = set()
        for source in self.sources:
            found.update(source.find())
        return found - self.ignore

    def publications(self):
        """Publications (not before min_year), newest first."""
        bibcodes = self.bibcodes()
        if not bibcodes:
            return []
        entries = self.client.export_bibtex(bibcodes).strip().split("\n\n")
        pubs = {}
        for entry in entries:
            pub = Publication.from_bibtex(entry)
            if pub and pub.bibcode not in self.ignore and (self.min_year is None or pub.year >= self.min_year):
                pubs[pub.bibcode] = pub
        return sorted(pubs.values(), key=lambda p: p.sort_key, reverse=True)


class OutputFormat(ABC):
    """Turns a list of Publications into text.  `name` is the --format value."""

    name = ""

    def __init__(self, max_authors=None):
        self.max_authors = max_authors

    @abstractmethod
    def render(self, publications) -> str:
        """Return the text, ending in a newline."""


class BibtexFormat(OutputFormat):
    name = "bibtex"

    def render(self, publications):
        return "\n\n".join(p.bibtex for p in publications).strip() + "\n"


class BibcodesFormat(OutputFormat):
    name = "bibcodes"

    def render(self, publications):
        return "".join(f"{p.bibcode}\n" for p in publications)


class DictFormat(OutputFormat):
    """A Python literal: a list of dicts, so the output can be pasted into code or ast.literal_eval'd."""

    name = "dict"

    def render(self, publications):
        return pprint.pformat([p.to_dict() for p in publications], sort_dicts=False, width=110) + "\n"


class ApjFormat(OutputFormat):
    """One ApJ-style reference per line, e.g.

        Vartanyan, D., Coleman, M. S. B., & Burrows, A. 2022, MNRAS, 510, 4689

    `max_authors`: list only the first N authors followed by "et al." (None = all).
    """

    name = "apj"

    def authors(self, pub):
        names = [a.last_initials for a in pub.authors]
        if self.max_authors and len(names) > self.max_authors:
            return ", ".join(names[: self.max_authors] + ["et al."])
        if len(names) <= 1:
            return "".join(names)
        return ", ".join(names[:-1]) + ", & " + names[-1]

    def render(self, publications):
        return "".join(f"{self.authors(p)} {p.year}, {p.venue}\n" for p in publications)


FORMATS = {cls.name: cls for cls in (BibtexFormat, BibcodesFormat, DictFormat, ApjFormat)}


def title_key(pub):
    """The title reduced to lowercase letters and digits, so copies of the same work compare equal."""
    return re.sub(r"[^a-z0-9]+", "", pub.get("title").lower())


class SitePage:
    """Writes the publications into the website's data/publications.js.

    That file is edited by hand, except for the regions between marker comments:

        // pub_find:begin refereed (...)
        { ... },
        // pub_find:end refereed

    One region per name in SECTIONS ("refereed" and "other" = everything else).  Each run
    replaces what is between the markers and touches nothing outside them, so the page's
    title and intro, and any entries added by hand outside the markers, are kept.

    A preprint and its published version, or two copies of a thesis, count as one work (same
    title): the published record is listed, and takes over the preprint's arXiv link.
    """

    SECTIONS = ("refereed", "other")
    REGION = re.compile(
        r"^([ \t]*)// pub_find:begin (\w+)[^\n]*\n.*?^[ \t]*// pub_find:end \2[ \t]*$", re.MULTILINE | re.DOTALL
    )

    def __init__(self, path, client):
        self.path = Path(path)
        self.client = client
        self.formatter = ApjFormat()  # for the author lists
        self.notes = []  # things worth telling the user, filled in by update()

    def merge_duplicates(self, publications):
        """Return [(publication, arXiv id)], one per work, in the original order."""
        groups = {}
        for pub in publications:
            groups.setdefault(title_key(pub), []).append(pub)
        merged = {}
        for group in groups.values():
            best = next((p for p in group if p.journal_abbrev != "arXiv"), group[0])
            arxiv = next((p.get("eprint") for p in [best, *group] if p.get("eprint")), "")
            merged[best.bibcode] = arxiv.removeprefix("arXiv:")
            self.notes += [f"merged {p.bibcode} into {best.bibcode}" for p in group if p is not best]
        return [(p, merged[p.bibcode]) for p in publications if p.bibcode in merged]

    def item(self, pub, arxiv):
        title = math_to_text(pub.get("title"))
        if "$" in title:
            self.notes.append(f"{pub.bibcode}: the title still has LaTeX in it: {title}")
        item = {
            "year": pub.year,
            "authors": self.formatter.authors(pub),
            "title": title,
            "venue": pub.venue,
            "ads": pub.bibcode,
            "arxiv": arxiv,
            "doi": "" if pub.journal_abbrev == "arXiv" else pub.get("doi"),  # an arXiv DOI just repeats the arXiv link
        }
        return {key: value for key, value in item.items() if value}

    def sections(self, publications):
        """Return {section name: [item dicts]}."""
        merged = self.merge_duplicates(publications)
        refereed = self.client.refereed(p.bibcode for p, _ in merged)
        sections = {name: [] for name in self.SECTIONS}
        for pub, arxiv in merged:
            # SciX flags dissertations as refereed, but they aren't peer-reviewed papers.
            is_refereed = pub.bibcode in refereed and pub.entry_type.lower() != "phdthesis"
            sections["refereed" if is_refereed else "other"].append(self.item(pub, arxiv))
        return sections

    def update(self, publications):
        """Rewrite the marker regions of the file.  Returns {section name: number of items}."""
        sections = self.sections(publications)
        text = self.path.read_text(encoding="utf-8")

        def fill(match):
            indent, name = match.groups()
            if name not in sections:
                sys.exit(f"Error: {self.path} has a pub_find region '{name}'; the known ones are {self.SECTIONS}.")
            lines = [f"{indent}// pub_find:begin {name} (written by tools/pub_find.py; edits here are overwritten)"]
            for item in sections[name]:
                lines += (indent + line for line in (json.dumps(item, indent=2, ensure_ascii=False) + ",").split("\n"))
            return "\n".join([*lines, f"{indent}// pub_find:end {name}"])

        new_text = self.REGION.sub(fill, text)
        missing = [name for name in self.SECTIONS if f"// pub_find:begin {name}" not in new_text]
        if missing:
            sys.exit(f"Error: {self.path} has no '// pub_find:begin {missing[0]}' ... '// pub_find:end' markers.")
        if new_text != text:
            self.path.write_text(new_text, encoding="utf-8")
        return {name: len(items) for name, items in sections.items()}


def main(
    fn=None,
    quiet=None,
    token=None,
    token_file=None,
    min_year=MIN_YEAR,
    library=MY_LIBRARY,
    fmt="bibtex",
    max_authors=None,
    site=None,
):
    client = SciXClient(token, token_file)
    orcid_source = OrcidRegistrySource(client, OrcidClient(), MY_ORCID)
    finder = PublicationFinder(
        client,
        [
            CoauthorSource(client, ME, PIS),
            SciXOrcidSource(client, MY_ORCID),
            orcid_source,
            LibrarySource(client, library),
        ],
        ignore=IGNORE,
        min_year=min_year,
    )
    page = SitePage(site, client) if site else None
    try:
        publications = finder.publications()
        if publications and page:
            counts = page.update(publications)
    except ApiError as exc:
        sys.exit(f"Error: {exc}")
    for work in orcid_source.unresolved:
        print(f"ORCID work not found in SciX: {work.year} {work.title}", file=sys.stderr)
    if not publications:
        sys.exit("No publications found.")
    if page:
        for note in page.notes:
            print(f"Note: {note}", file=sys.stderr)
        print(f"Updated {site}: " + ", ".join(f"{n} {name}" for name, n in counts.items()) + ".", file=sys.stderr)
    if (fn or site) and quiet is None:
        quiet = True
    formatter = FORMATS[fmt](max_authors=max_authors)
    text = formatter.render(publications)
    if not quiet:
        print(text, end="")
    if fn:
        Path(fn).write_text(text)
    return publications


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find my publications.")
    parser.add_argument("--output", "-o", type=str, help="Output filename to save BibTeX entries.")
    auth = parser.add_mutually_exclusive_group()
    auth.add_argument("--token", "-t", type=str, help="SciX API token (default: env var or ~/.ads/dev_key).")
    auth.add_argument("--token-file", "-T", type=str, help="File containing the SciX API token.")
    parser.add_argument(
        "--min-year",
        "-y",
        type=int,
        default=MIN_YEAR,
        help="Skip publications before this year (default: %(default)s).",
    )
    parser.add_argument(
        "--library", "-l", default=MY_LIBRARY, help="SciX library id or URL to include (default: %(default)s)."
    )
    parser.add_argument(
        "--format", "-f", choices=sorted(FORMATS), default="bibtex", help="Output format (default: %(default)s)."
    )
    parser.add_argument(
        "--max-authors", type=int, metavar="N", help='With -f apj: list only the first N authors, then "et al."'
    )
    parser.add_argument(
        "--site",
        nargs="?",
        const=SITE_FILE,
        metavar="FILE",
        help="Update the website's publications list in FILE instead of printing (default: %(const)s).",
    )
    parser.add_argument("--quiet", "-q", action="store_true", default=None, help="Suppress console output.")
    args = parser.parse_args()
    if args.max_authors is not None and args.format != "apj":
        parser.error("--max-authors only applies to --format apj")
    main(
        fn=args.output,
        quiet=args.quiet,
        token=args.token,
        token_file=args.token_file,
        min_year=args.min_year,
        library=args.library,
        fmt=args.format,
        max_authors=args.max_authors,
        site=args.site,
    )
