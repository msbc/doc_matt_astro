#!/usr/bin/env python
"""Find my publications in SciX (the successor to NASA ADS) and print/save BibTeX.

    uv run tools/pub_find.py                 print BibTeX to the terminal
    uv run tools/pub_find.py -o pubs.bib     save it to a file

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
                      finding papers (co-author search, SciX ORCID tags, ORCID registry)
  PublicationFinder   merges the sources, fetches BibTeX, drops ignored entries,
                      sorts newest first
"""

import argparse
import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import requests

# --- CONFIG: edit these ---
# Use "Last, F. M." style as ADS expects (can be forgiving, but this helps).
ME = "Coleman, M"  # e.g., "Coleman, Matthew S."
PIS = [
    "Blaes, O",
    "Ravikov, R",
    "Burrows, A",
    "Thompson, T",
]

# Your ORCID is the most precise filter.
MY_ORCID = "0000-0001-5939-5957"

# Ignore list: publications to skip (e.g., non-refereed)
IGNORE = ["2021arXiv211100022C", "2000ccdc.data.5353B"]

# Skip publications from before this year (None = no limit).
MIN_YEAR = 2014

MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


class SciXClient:
    """Minimal client for the SciX API (same API as ADS)."""

    # api.adsabs.harvard.edu/v1 also still works.
    BASE_URL = "https://api.scixplorer.org/v1"
    TOKEN_ENV_VARS = ("SCIX_API_TOKEN", "ADS_DEV_KEY")
    TOKEN_FILE = Path.home() / ".ads" / "dev_key"
    MAX_ROWS = 2000  # the API returns only 10 rows unless asked for more
    TIMEOUT = 60

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

    def search(self, query):
        """Return the bibcodes matching a SciX/ADS query string."""
        response = self.session.get(
            f"{self.BASE_URL}/search/query",
            params={"q": query, "fl": "bibcode", "rows": self.MAX_ROWS},
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()
        return [doc["bibcode"] for doc in response.json()["response"]["docs"]]

    def lookup(self, identifiers, chunk=50):
        """Return the bibcodes of records matching any identifier (DOI, "arXiv:...", bibcode)."""
        identifiers = sorted(set(identifiers))
        found = []
        for i in range(0, len(identifiers), chunk):
            terms = " OR ".join(f'"{v}"' for v in identifiers[i : i + chunk])
            # (`doi:(...)` with a group is a syntax error in SciX; `identifier:(...)` works and matches DOIs too.)
            found.extend(self.search(f"identifier:({terms})"))
        return found

    def export_bibtex(self, bibcodes):
        """Return one BibTeX string covering all the given bibcodes."""
        response = self.session.post(
            f"{self.BASE_URL}/export/bibtex",
            json={"bibcode": list(bibcodes)},
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()
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
    TIMEOUT = 60

    def works(self, orcid):
        response = requests.get(
            f"{self.BASE_URL}/{orcid}/works",
            headers={"Accept": "application/json"},
            timeout=self.TIMEOUT,
        )
        response.raise_for_status()
        return [OrcidWork.from_group(g) for g in response.json()["group"]]


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

    @staticmethod
    def to_bibtex(publications):
        return "\n\n".join(p.bibtex for p in publications).strip() + "\n"


def main(fn=None, quiet=None, token=None, token_file=None, min_year=MIN_YEAR):
    client = SciXClient(token, token_file)
    orcid_source = OrcidRegistrySource(client, OrcidClient(), MY_ORCID)
    finder = PublicationFinder(
        client,
        [CoauthorSource(client, ME, PIS), SciXOrcidSource(client, MY_ORCID), orcid_source],
        ignore=IGNORE,
        min_year=min_year,
    )
    publications = finder.publications()
    for work in orcid_source.unresolved:
        print(f"ORCID work not found in SciX: {work.year} {work.title}", file=sys.stderr)
    if not publications:
        sys.exit("No publications found.")
    if fn and quiet is None:
        quiet = True
    text = finder.to_bibtex(publications)
    if not quiet:
        print(text)
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
    parser.add_argument("--quiet", "-q", action="store_true", default=None, help="Suppress console output.")
    args = parser.parse_args()
    main(fn=args.output, quiet=args.quiet, token=args.token, token_file=args.token_file, min_year=args.min_year)
