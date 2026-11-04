#!/usr/bin/env python3
"""Write js/images.js: the background-photo registry, built from img/tier*/.

For every <stem>_native.jpg in img/tier1, img/tier2, ... this collects

  * the size ladder  <stem>_2powNN.jpg  (written by tools/make_sizes.py), with
    each file's real pixel width, which is what the srcset needs;
  * credit / license / title from the photo's embedded metadata (read with
    exiftool).  Nothing is invented: a photo with no embedded credit gets
    credit "TODO" and weight 0, so it never shows until you fill it in.

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


def exif(paths):
    """{path: {tag: str}} for every path, in one exiftool call."""
    if not paths:   # e.g. an empty tier3/ folder
        return {}
    cmd = ["exiftool", "-json", *[f"-{t}" for t in TAGS], *map(str, paths)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False).stdout
    return {Path(r["SourceFile"]): {k: str(v) for k, v in r.items()} for r in json.loads(out)}


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def credit_of(meta):
    c = clean(meta.get("Credit", ""))
    c = re.split(r"\s*Acknowledg(?:e)?ments?\b", c, maxsplit=1)[0]   # keep the creators, drop courtesy lines
    return c.rstrip(" .;,")


def credit_truncated(meta):
    """ESA files carry a credit cut off at the 32-character IPTC limit (e.g. '... J. Lee and th')."""
    return len(clean(meta.get("Credit", ""))) == 32


def credit_for_site(meta):
    c = credit_of(meta)
    if credit_truncated(meta):
        c = c.rsplit(",", 1)[0].strip()      # drop the last, possibly half-cut, name
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
    if "CSA" in credit:       # NASA/ESA/CSA = Webb; NASA/ESA alone = Hubble
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
            known = bool(credit)
            title = clean(md.get("Title") or md.get("Headline") or md.get("ObjectName") or "").lstrip("*").strip()
            entries.append({
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
                "weight": weights.get(tier.name, 1) if known else 0,
                "tier": tier.name,
            })
    return entries


def js_string(s):
    return json.dumps(s, ensure_ascii=False)


def render(entries):
    out = ["""/* =====================================================================
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
  var NEW = {"""]
    for e in entries:
        out.append(f"    {js_string(e['name'])}: {{")
        out.append(f"      src: {js_string(e['src'])},")
        out.append("      ladder: " + json.dumps(e["ladder"]) + ",")
        out.append(f"      alt: {js_string(e['alt'])},")
        out.append(f"      title: {js_string(e['title'])},")
        out.append(f"      credit: {js_string(e['credit'])},"  + ("   // file metadata was cut off; last name dropped, see the release page" if e["trimmed"] else ""))
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
    ap.add_argument("--weight", action="append", default=[], metavar="TIER=W",
                    help="rotation weight per tier folder (default tier1=2, tier2=1, others 1)")
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
