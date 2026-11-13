#!/usr/bin/env python3
"""Write js/images.js: the background-photo registry, built from img/tier*/.

For every <stem>_native.jpg in img/tier1, img/tier2, ... this collects

  * the size ladder  <stem>_2powNN.jpg  (written by tools/make_sizes.py), with
    each file's real pixel width, which is what the srcset needs;
  * credit / license / title from the photo's embedded metadata (read with
    exiftool).  Nothing is invented: a photo with no embedded credit gets
    credit "TODO" and weight 0, so it never shows until you fill it in.
  * the OVERRIDES table below, which wins over the embedded metadata. Put researched
    credits there (not only in images.js) so --force keeps them.

The output is meant to be hand-edited afterwards (PSF rotation, credits, weights),
so an existing js/images.js is NOT overwritten unless you pass --force.

Needs Pillow and exiftool (brew install exiftool).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent
RUNG = re.compile(r"^(?P<stem>.+)_2pow(?P<n>\d{2})\.jpg$")
TAGS = ["Credit", "Source", "UsageTerms", "License", "Title", "Headline", "ObjectName"]

# Photos of the same target share an `object`, so showing one holds the others back.
OBJECTS = {
    "carina": ["weic2205a", "weic2205b", "carinanebula3"],
    "pillars": ["weic2216b", "pillarsofcreation_composite"],
    "cats-head": ["weic2622b", "weic2622d", "weic2622e"],
    "cas-a": ["weic2330e", "weic2330f"],
    "n44": ["Hubble_N44_potm2608a_lg", "Hubble_LMC_N44C_potw2536a"],
    "ring": ["weic2320b", "ring-nebula"],
}
OBJECT_OF = {stem: obj for obj, stems in OBJECTS.items() for stem in stems}

# Hand-researched metadata for photos whose embedded metadata is missing or cut off
# (Flickr downloads, for instance). Anything listed here wins over what exiftool finds, so
# re-running this script with --force keeps it. Keys are the file stem; allowed fields:
#   title, alt, credit, license, sourceUrl, psf (preset name), weight, note (comment shown
#   after the credit in images.js).
# An entry with a credit gets the tier's default weight unless it sets `weight` itself.
OVERRIDES = {
    # NASA Hubble on Flickr, "Southern Pinwheel" (M83); not found on esahubble.org.
    "50330680253-458032d203-o": {
        "title": "Southern Pinwheel",
        "alt": "Southern Pinwheel",
        "credit": "NASA, ESA, the Hubble Heritage Team (STScI/AURA)",
        "license": "CC BY 2.0",
        "sourceUrl": "https://www.flickr.com/photos/nasahubble/50330680253/",
        "psf": "hst",
    },
    # "A Lost Galaxy" (NGC 4535) on NASA Hubble's Flickr; the file's embedded credit is cut off.
    "52046519794-082f96a17d-o": {
        "credit": "ESA/Hubble & NASA, J. Lee and the PHANGS-HST Team",
        "sourceUrl": "https://www.flickr.com/photos/nasahubble/52046519794/",
        "note": "full credit from the Flickr page; file metadata was cut off",
    },
    # Bubble Nebula, esahubble.org heic1608a (ESA/Hubble images are CC BY 4.0).
    "37893980612-307324af83-o": {
        "title": "Bubble Nebula",
        "alt": "Bubble Nebula",
        "credit": "NASA, ESA, Hubble Heritage Team",
        "license": "CC BY 4.0",
        "sourceUrl": "https://esahubble.org/images/heic1608a/",
        "psf": "hst",
        "weight": 0,
    },
    # Tarantula Nebula, esahubble.org potw2305a. The page also lists "Acknowledgement: Y.-H. Chu",
    # which is dropped here like every other acknowledgement line (see credit_of).
    "hubble-trantula-potw2305a-jpg": {
        "title": "Exploring a Turbulent Tarantula",
        "alt": "Exploring a Turbulent Tarantula",
        "credit": "ESA/Hubble & NASA, C. Murray, E. Sabbi",
        "license": "CC BY 4.0",
        "sourceUrl": "https://esahubble.org/images/potw2305a/",
        "psf": "hst",
    },
    # "Spiral's Edge" (NGC 1827), NASA image page; the page states no license.
    "Hubble_NGC1827_1_flat_FINAL": {
        "title": "Spiral's Edge",
        "alt": "Edge-on spiral galaxy NGC 1827",
        "credit": "NASA, ESA, Michael Jones (California Institute of Technology). "
        "Image Processing: Gladys Kober (NASA/Catholic University of America)",
        "sourceUrl": "https://www.nasa.gov/image-detail/hubble-ngc1827-1-flat-final/",
        "psf": "hst",
    },
    # "Hubble Views the Dawn of a Sun-like Star" (HP Tau), NASA image page; no license stated.
    "hubble-hptau-wfc3-1-flat-finalok": {
        "title": "Hubble Views the Dawn of a Sun-like Star",
        "alt": "Triple-star system HP Tau in a reflection nebula",
        "credit": "NASA, ESA, G. Duchene (Universite de Grenoble I). "
        "Image Processing: Gladys Kober (NASA/Catholic University of America)",
        "sourceUrl": "https://science.nasa.gov/image-detail/hubble-hptau-wfc3-1-flat-finalok",
        "psf": "hst",
    },
    # Rubin First Look, southern Virgo Cluster: noirlab.edu noirlab2521a, 97943 x 51536 px (the TIFF's
    # embedded original size). Credit is the caption's wording on rubinobservatory.org's page for this
    # image; the Rubin media policy (CC BY 4.0) otherwise asks for "NSF-DOE Vera C. Rubin
    # Observatory/NOIRLab/SLAC/AURA".
    "Im1-10k": {
        "title": "The Cosmic Treasure Chest",
        "alt": "Southern part of the Virgo Cluster, seen by Rubin Observatory",
        "credit": "NSF–DOE Vera C. Rubin Observatory",
        "license": "CC BY 4.0",
        "sourceUrl": "https://noirlab.edu/public/images/noirlab2521a/",
        "psf": "rubin",
    },
    # Rubin First Look, Trifid and Lagoon Nebulae (NOIRLab noirlab2521b, which could not be read).
    # Credit is the caption wording on rubinobservatory.org's page; see Im1-10k for the policy note.
    "lm4-Trifid-10k": {
        "credit": "NSF–DOE Vera C. Rubin Observatory",
        "license": "CC BY 4.0",
        "sourceUrl": "https://rubinobservatory.org/gallery/image-releases/rubin-first-look/trifid-lagoon",
    },
    # Webb images whose esawebb.org page matches the local file's size and credit. The pages state no
    # license themselves; esawebb.org/copyright says ESA/Webb images are CC BY 4.0.
    "carinanebula3": {  # 14570 x 8452 px, released 15 Dec 2022
        "license": "CC BY 4.0",
        "sourceUrl": "https://esawebb.org/images/carinanebula3/",
    },
    "pillarsofcreation_composite": {  # 7130 x 6675 px, released 30 Nov 2022
        "license": "CC BY 4.0",
        "sourceUrl": "https://esawebb.org/images/pillarsofcreation_composite/",
    },
    "jupiter-auroras1": {  # 1646 x 1561 px, released 22 Aug 2022
        "license": "CC BY 4.0",
        "sourceUrl": "https://esawebb.org/images/jupiter-auroras1/",
    },
    # NGC 4254, esawebb.org weic2403o (3473 x 1941 px, same as the file). The file's embedded credit
    # names J. DePasquale and A. Pagan (STScI's version); this is ESA's credit line for the page.
    "STScI-01HMBZKXD4KQSVV76MNVPXN9RX": {
        "credit": "NASA, ESA, CSA, STScI, J. Lee (STScI), T. Williams (Oxford), PHANGS Team",
        "license": "CC BY 4.0",
        "sourceUrl": "https://esawebb.org/images/weic2403o/",
    },
    # Hubble's Ring Nebula (M57), esahubble.org heic1310a, 3179 x 3179 px like the local file.
    "ring-nebula": {
        "title": "Hubble image of the Ring Nebula (Messier 57)",
        "alt": "Hubble image of the Ring Nebula (Messier 57)",
        "credit": "NASA, ESA, and C. Robert O'Dell (Vanderbilt University)",
        "license": "CC BY 4.0",
        "sourceUrl": "https://esahubble.org/images/heic1310a/",
        "psf": "hst",
    },
    # Arp 273, "A rose made of galaxies", esahubble.org heic1107a.
    "46646118205-6b0b936128-o": {
        "title": 'Colliding Galaxy Pair Arp 273, the "Rose"',
        "alt": 'Colliding galaxy pair Arp 273, the "Rose"',
        "credit": "NASA, ESA and the Hubble Heritage Team (STScI/AURA)",
        "license": "CC BY 4.0",
        "sourceUrl": "https://esahubble.org/images/heic1107a/",
        "psf": "hst",
        "weight": 0,
    },
}


def exif(paths):
    """{path: {tag: str}} for every path, in one exiftool call."""
    if not paths:  # e.g. an empty tier3/ folder
        return {}
    cmd = ["exiftool", "-json", *[f"-{t}" for t in TAGS], *map(str, paths)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False).stdout
    return {Path(r["SourceFile"]): {k: str(v) for k, v in r.items()} for r in json.loads(out)}


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def credit_of(meta):
    c = clean(meta.get("Credit", ""))
    c = re.split(r"\s*Acknowledg(?:e)?ments?\b", c, maxsplit=1)[0]  # keep the creators, drop courtesy lines
    return c.rstrip(" .;,")


def credit_truncated(meta):
    """ESA files carry a credit cut off at the 32-character IPTC limit (e.g. '... J. Lee and th')."""
    return len(clean(meta.get("Credit", ""))) == 32


def credit_for_site(meta):
    c = credit_of(meta)
    if credit_truncated(meta):
        c = c.rsplit(",", 1)[0].strip()  # drop the last, possibly half-cut, name
    return c


def license_of(meta):
    terms = meta.get("UsageTerms", "") + " " + meta.get("License", "")
    return "CC BY 4.0" if "Creative Commons Attribution 4.0" in terms else ""


def source_url(stem, meta):
    """Release page, only where the ID in the file name is a real ESA release ID."""
    m = re.search(r"(weic|potm|potw)\d{4}[a-z]", stem)
    if not m:
        return ""
    host = {"ESA/Webb": "esawebb.org", "ESA/Hubble": "esahubble.org"}.get(clean(meta.get("Source", "")))
    return f"https://{host}/images/{m.group(0)}/" if host else ""


def psf_preset(stem, meta):
    credit, title, source = credit_of(meta), clean(meta.get("Title", "")), clean(meta.get("Source", ""))
    if "NOIRLab" in source or "Rubin" in credit:
        return "rubin"
    if "Hubble" in source or "Hubble" in title or "hubble" in stem.lower():
        return "hst"
    if "CSA" in credit:  # NASA/ESA/CSA = Webb; NASA/ESA alone = Hubble
        return "jwst"
    if credit and "ESA" in credit:
        return "hst"
    return "none"


def build(tier_dirs, max_n, weights):
    entries = []
    for tier in tier_dirs:
        by_stem = {}
        for p in sorted(tier.glob("*.jpg")):
            m = RUNG.match(p.name)
            if m and int(m["n"]) <= max_n:
                by_stem.setdefault(m["stem"], []).append((int(m["n"]), p))
        meta = exif([tier / f"{stem}_native.jpg" for stem in by_stem if (tier / f"{stem}_native.jpg").exists()])
        for stem, rungs in sorted(by_stem.items()):
            md = meta.get(tier / f"{stem}_native.jpg", {})
            ladder = []
            for n, p in sorted(rungs):
                with Image.open(p) as im:
                    ladder.append([n, im.width])
            credit = credit_for_site(md)
            title = clean(md.get("Title") or md.get("Headline") or md.get("ObjectName") or "").lstrip("*").strip()
            entry = {
                "name": stem,
                "src": f"img/{tier.name}/{stem}",
                "ladder": ladder,
                "alt": title,
                "title": title or stem,
                "credit": credit or "TODO",
                "license": license_of(md),
                "sourceUrl": source_url(stem, md),
                "object": OBJECT_OF.get(stem, ""),
                "psf": psf_preset(stem, md),
                "trimmed": credit_truncated(md),
                "note": "",
                "tier": tier.name,
            }
            override = OVERRIDES.get(stem, {})
            entry.update(override)
            if "credit" in override:
                entry["trimmed"] = False  # a hand-written credit is complete
            known = entry["credit"] != "TODO"
            entry["weight"] = override.get("weight", weights.get(tier.name, 1) if known else 0)
            entries.append(entry)
    return entries


def js_string(s):
    return json.dumps(s, ensure_ascii=False)


def render(entries):
    out = [
        """/* =====================================================================
   images.js — the real background photos. Loaded after site-data.js, it adds
   to SITE.images and replaces SITE.rotation (so the placeholder starfields
   are only a fallback).

   Generated by tools/make_image_registry.py from the img/tierN folders, then meant to be
   edited by hand. Things worth checking:
     weight   0 = never shown. Photos with no embedded credit start at 0 with
              credit "TODO": fill in credit + license, then raise the weight.
     psf      telescope guessed from the credit; `rotation` (degrees) is left
              at 0. Turn it until the logo's spikes match the photo's.
     ladder   [n, pixels]: the file <src>_2pow<nn>.jpg is that many px wide.
   ===================================================================== */
(function () {
  var S = window.SITE;
  if (!S) return;
  var NEW = {"""
    ]
    for e in entries:
        out.append(f"    {js_string(e['name'])}: {{")
        out.append(f"      src: {js_string(e['src'])},")
        out.append("      ladder: " + json.dumps(e["ladder"]) + ",")
        out.append(f"      alt: {js_string(e['alt'])},")
        out.append(f"      title: {js_string(e['title'])},")
        out.append(
            f"      credit: {js_string(e['credit'])},"
            + (
                f"   // {e['note']}"
                if e["note"]
                else "   // file metadata was cut off; last name dropped, see the release page"
                if e["trimmed"]
                else ""
            )
        )
        out.append(f"      license: {js_string(e['license'])},")
        out.append(f"      sourceUrl: {js_string(e['sourceUrl'])},")
        if e["object"]:
            out.append(f"      object: {js_string(e['object'])},")
        out.append(f"      psf: {{ preset: {js_string(e['psf'])}, rotation: 0 }},")
        out.append(f"      weight: {e['weight']},   // {e['tier']}")
        out.append("    },")
    out.append("  };")
    out.append("""
  // Fold `weight` into the rotation list, then drop it from the entries.
  var rotation = [];
  Object.keys(NEW).forEach(function (name) {
    rotation.push({ name: name, weight: NEW[name].weight });
    delete NEW[name].weight;
  });
  S.images = Object.assign(S.images || {}, NEW);
  S.rotation = rotation;
})();""")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--img", type=Path, default=ROOT / "img", help="folder holding the tier* subfolders")
    ap.add_argument("--out", type=Path, default=ROOT / "js" / "images.js")
    ap.add_argument("--max-n", type=int, default=12, help="largest 2^n rung to offer (default 12 = ~4096 px)")
    ap.add_argument(
        "--weight",
        action="append",
        default=[],
        metavar="TIER=W",
        help="rotation weight per tier folder (default tier1=2, tier2=1, others 1)",
    )
    ap.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = ap.parse_args()

    weights = {"tier1": 2, "tier2": 1}
    for item in args.weight:
        k, _, v = item.partition("=")
        weights[k] = float(v) if "." in v else int(v)
    if args.out.exists() and not args.force:
        sys.exit(f"{args.out} exists; it may hold hand edits. Re-run with --force to overwrite.")

    tiers = sorted(p for p in args.img.glob("tier*") if p.is_dir())
    entries = build(tiers, args.max_n, weights)
    args.out.write_text(render(entries), encoding="utf-8")
    todo = [e["name"] for e in entries if e["credit"] == "TODO"]
    print(f"wrote {args.out} ({len(entries)} photos, {len(todo)} need a credit)")
    for name in todo:
        print("  TODO credit:", name)


if __name__ == "__main__":
    main()
