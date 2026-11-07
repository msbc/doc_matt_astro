#!/usr/bin/env python3
"""Build nojs/: a static, JavaScript-free copy of every page.

The main site needs no build step and is never touched by this script.  This
is an optional extra for visitors who have JavaScript turned off: each page's
<noscript> panel links to nojs/<page>.html, which this script writes.  A
visitor whose JavaScript is ON is sent straight on to the full page (see
REDIRECT); add ?text to a nojs/ URL to stay on the text-only version.

For every top-level <page>.html it
  * takes the page's frame (header, nav, <title>, styles) from that file,
  * reads the page's text from data/<page>.js and the shared settings from
    js/site-data.js (evaluated with node, exactly as a browser would),
  * renders the same sections render.js draws (text, cards, timeline, stats,
    pubs) as plain HTML using the site's existing CSS classes,
  * drops every <script> and the (JS-only) dark-mode button, then adds the one
    small redirect script that only runs when JavaScript is enabled.

Re-run it after editing data/*.js, js/site-data.js, or a page's header/nav.
`--check` writes nothing and exits 1 if nojs/ is out of date (handy before a
commit).  Needs node (to read the .js data files) and nothing else.

Keep the builders below in step with BUILDERS in js/render.js.
"""

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Evaluate the .js data files the way the browser does and print them as JSON.
NODE_LOADER = r"""
const fs = require("fs"), vm = require("vm");
function load(file) {
  const win = {};
  vm.runInNewContext(fs.readFileSync(file, "utf8"), { window: win }, { filename: file });
  return win;
}
const [root, ...pages] = process.argv.slice(1);
const out = { site: load(root + "/js/site-data.js").SITE, pages: {} };
for (const p of pages) out.pages[p] = load(root + "/data/" + p + ".js").PAGE;
process.stdout.write(JSON.stringify(out));
"""

# Runs only when JavaScript is on: leave the text-only page for the full one, keeping
# any #section in the URL.  location.replace leaves no history entry, so Back works.
# "?text" in the URL skips it (to preview or test the text-only pages with JS on).
REDIRECT = (
    '<script>if(!/[?&]text(?:[=&]|$)/.test(location.search))location.replace("../%s.html"+location.hash)</script>\n'
)

INLINE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)|\*([^*]+)\*")
SIBLING_PAGE = re.compile(r"^[\w-]+\.html(?:[#?].*)?$")


def esc(value):
    return html.escape(str(value), quote=True)


def slug(text):
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", str(text).lower()))


class Builder:
    def __init__(self, site, stems):
        self.site = site or {}
        self.stems = stems
        self.owner_names = [n for n in (self.site.get("owner") or {}).get("pubNames", []) if n]

    # ---- links and inline text ----

    def href(self, url):
        """A link as written in the data, made to work from inside nojs/."""
        url = str(url)
        scheme = re.match(r"^([a-z][a-z0-9+.-]*):", url, re.IGNORECASE)
        if scheme:
            return url if scheme.group(1).lower() in ("http", "https", "mailto") else "#"
        if url.startswith(("#", "/")):
            return url
        if SIBLING_PAGE.match(url) and url.split("#")[0].split("?")[0][:-5] in self.stems:
            return url  # another page: its nojs/ twin sits next to this one
        return "../" + url  # css/, cv/, img/ ... live one level up

    def inline(self, text):
        text, out, last = str(text), [], 0
        for m in INLINE.finditer(text):
            out.append(esc(text[last : m.start()]))
            if m.group(1):
                out.append(f'<a href="{esc(self.href(m.group(2)))}">{esc(m.group(1))}</a>')
            else:
                out.append(f"<em>{esc(m.group(3))}</em>")
            last = m.end()
        out.append(esc(text[last:]))
        return "".join(out)

    # ---- section types (mirror BUILDERS in js/render.js) ----

    def text(self, sec):
        paras = "\n".join(f"<p>{self.inline(p)}</p>" for p in sec.get("paragraphs", []))
        return f'<div class="prose">\n{paras}\n</div>'

    def cards(self, sec):
        lis = []
        for item in sec.get("items", []):
            title = esc(item.get("title", ""))
            if item.get("href"):
                title = '<a class="card-link" href="{}">{}</a>'.format(esc(self.href(item["href"])), title)
            parts = []
            if item.get("meta"):
                parts.append('<p class="meta">{}</p>'.format(esc(item["meta"])))
            parts.append(f"<h3>{title}</h3>")
            if item.get("before") or item.get("after"):
                parts.append(self.speedup(item))
            if item.get("text"):
                parts.append("<p>{}</p>".format(self.inline(item["text"])))
            if item.get("tags"):
                tags = "".join(f"<li>{esc(t)}</li>" for t in item["tags"])
                parts.append(f'<ul class="tags">{tags}</ul>')
            lis.append('<li><article class="card">\n{}\n</article></li>'.format("\n".join(parts)))
        return '<ul class="cards">\n{}\n</ul>'.format("\n".join(lis))

    @staticmethod
    def speedup(item):
        parts = [
            "<dt>Before</dt><dd>{}</dd>".format(esc(item.get("before") or "—")),
            "<dt>After</dt><dd>{}</dd>".format(esc(item.get("after") or "—")),
        ]
        if item.get("gain"):
            parts.append('<dd class="gain">{}</dd>'.format(esc(item["gain"])))
        return '<dl class="speedup">{}</dl>'.format("".join(parts))

    def timeline(self, sec):
        lis = []
        for item in sec.get("items", []):
            parts = []
            if item.get("when"):
                parts.append('<p class="meta">{}</p>'.format(esc(item["when"])))
            parts.append("<h3>{}</h3>".format(esc(item.get("title", ""))))
            if item.get("where"):
                parts.append('<p class="meta">{}</p>'.format(esc(item["where"])))
            if item.get("text"):
                parts.append("<p>{}</p>".format(self.inline(item["text"])))
            lis.append("<li>\n{}\n</li>".format("\n".join(parts)))
        return '<ol class="timeline">\n{}\n</ol>'.format("\n".join(lis))

    def stats(self, sec):
        rows = []
        for item in sec.get("items", []):
            dd = '<span class="readout-value">{}</span>'.format(esc(item.get("value", "")))
            if item.get("note"):
                dd += '<span class="readout-note">{}</span>'.format(self.inline(item["note"]))
            rows.append('<div class="readout"><dt>{}</dt><dd>{}</dd></div>'.format(esc(item.get("label", "")), dd))
        return '<dl class="readouts">\n{}\n</dl>'.format("\n".join(rows))

    def pubs(self, sec):
        lis = []
        for pub in sec.get("items", []):
            authors = str(pub.get("authors", ""))
            links = []
            if pub.get("scix"):
                scix = str(pub["scix"])
                links.append(("SciX", scix if re.match(r"https?:", scix) else "https://scixplorer.org/abs/" + scix + "/abstract"))
            if pub.get("arxiv"):
                links.append(("arXiv", "https://arxiv.org/abs/" + str(pub["arxiv"])))
            if pub.get("doi"):
                links.append(("DOI", "https://doi.org/" + str(pub["doi"])))
            if pub.get("url"):
                links.append(("Link", pub["url"]))
            body = [
                '<p class="pub-title">{}</p>'.format(self.inline(pub.get("title", ""))),
                f'<p class="pub-authors">{self.bold_owner(authors)}</p>',
            ]
            if pub.get("venue"):
                body.append('<p class="pub-venue">{}</p>'.format(esc(pub["venue"])))
            if links:
                items = "".join(f'<li><a href="{esc(self.href(u))}">{esc(label)}</a></li>' for label, u in links)
                body.append(f'<ul class="pub-links">{items}</ul>')
            first = " data-first" if any(authors.strip().startswith(n) for n in self.owner_names) else ""
            lis.append(
                '<li class="pub"{}><span class="pub-year">{}</span>\n<div>\n{}\n</div></li>'.format(
                    first, esc(pub.get("year", "")), "\n".join(body)
                )
            )
        return '<ol class="pubs">\n{}\n</ol>'.format("\n".join(lis))

    def bold_owner(self, authors):
        out, rest = [], authors
        while rest:
            hit = None
            for name in self.owner_names:
                i = rest.find(name)
                if i != -1 and (hit is None or i < hit[0]):
                    hit = (i, name)
            if hit is None:
                out.append(esc(rest))
                break
            out.append(esc(rest[: hit[0]]) + f"<strong>{esc(hit[1])}</strong>")
            rest = rest[hit[0] + len(hit[1]) :]
        return "".join(out)

    # ---- page pieces ----

    def section(self, sec, index):
        sid = sec.get("id") or slug(sec.get("label") or f"section-{index + 1}")
        code = f"{index + 1:02d}"
        kind = sec.get("type")
        build = getattr(self, kind, None) if kind in ("text", "cards", "timeline", "stats", "pubs") else None
        if build is None:
            raise SystemExit('Section "{}" has unknown type "{}".'.format(sec.get("label") or sid, kind))
        intro = '<p class="section-intro">{}</p>\n'.format(self.inline(sec["intro"])) if sec.get("intro") else ""
        return (
            '<section class="section section--{}" id="{}" data-label="{}" data-code="{}" aria-labelledby="{}-title">\n'
            '<header class="section-head"><span class="section-code" aria-hidden="true">{}</span>'
            '<h2 id="{}-title">{}</h2></header>\n{}{}\n</section>'.format(
                kind,
                esc(sid),
                esc(sec.get("label") or sid),
                code,
                esc(sid),
                code,
                esc(sid),
                esc(sec.get("label", "")),
                intro,
                build(sec),
            )
        )

    def main(self, stem, page):
        home = bool(page.get("home"))
        if home:
            wm = self.site.get("wordmark") or {"before": "Doc", "after": "Matt Astro"}
            heading = '<h1>{}<span class="sr-only">.</span><span class="psf" aria-hidden="true"></span> {}</h1>'.format(
                esc(wm["before"]), esc(wm["after"])
            )
        else:
            heading = "<h1>{}</h1>".format(esc(page.get("title", "")))
        panel = []
        if page.get("kicker"):
            panel.append('<p class="kicker">{}</p>'.format(esc(page["kicker"])))
        panel.append(heading)
        if page.get("intro"):
            panel.append("<p>{}</p>".format(self.inline(page["intro"])))
        sections = "\n".join(self.section(s, i) for i, s in enumerate(page.get("sections", [])))
        return (
            '<main id="main" tabindex="-1">\n'
            '<div class="noscript-panel"><p>This is the text-only version of this page. '
            '<a href="../{}.html">Open the full site</a> (needs JavaScript).</p></div>\n'
            '<div class="viewscreen viewscreen--text{}">\n'
            '<div class="viewscreen-panel dark-island">\n{}\n</div>\n</div>\n'
            "{}\n</main>".format(stem, " viewscreen--hero" if home else "", "\n".join(panel), sections)
        )

    def footer(self):
        data = self.site.get("footer")
        if not data:
            return '<footer class="site-footer"></footer>'
        links = "".join(
            '<li><a href="{}">{}</a></li>'.format(esc(self.href(l["href"])), esc(l["label"]))
            for l in data.get("links", [])
        )
        return '<footer class="site-footer">\n<p>{}</p>\n<ul>{}</ul>\n<p aria-hidden="true">{}</p>\n</footer>'.format(
            esc(data.get("note", "")), links, esc(data.get("readout", ""))
        )


def build_page(stem, source_html, page, builder):
    out = source_html
    out = re.sub(r"[ \t]*<!-- 1\. Apply.*?-->\n", "", out, flags=re.DOTALL)
    out = re.sub(r"[ \t]*<!-- 4\. Scripts.*?-->\n", "", out, flags=re.DOTALL)
    out = re.sub(r"[ \t]*<script\b[^>]*>.*?</script>\n", "", out, flags=re.DOTALL)
    out = re.sub(r"[ \t]*<button id=\"theme-toggle\".*?</button>\n", "", out, flags=re.DOTALL)
    out = re.sub(r"<!-- Page text lives in .*?-->\n", "", out, flags=re.DOTALL)
    out = re.sub(r'\b(href|src)="(css|cv|js|img|data)/', r'\1="../\2/', out)  # we live in nojs/
    new_main = builder.main(stem, page)
    new_footer = builder.footer()
    out, n1 = re.subn(r'<main id="main".*?</main>', lambda m: new_main, out, flags=re.DOTALL)
    out, n2 = re.subn(r'<footer class="site-footer">.*?</footer>', lambda m: new_footer, out, flags=re.DOTALL)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f'{stem}.html: expected one <main id="main"> and one <footer class="site-footer">.')
    # Right after the viewport <meta>, so <meta charset> stays within the first 1024 bytes.
    out, n3 = re.subn(r'(<meta name="viewport"[^>]*>\n)', lambda m: m.group(1) + "  " + REDIRECT % stem, out, count=1)
    if n3 != 1:
        raise SystemExit(f'{stem}.html: expected a <meta name="viewport"> line to place the redirect after.')
    note = (
        f"<!-- GENERATED by tools/build_nojs.py from {stem}.html, data/{stem}.js and js/site-data.js. "
        "Do not edit; re-run the script. -->\n"
    )
    return out.replace("<head>", note + "<head>", 1) if "<head>" in out else note + out


def main():
    ap = argparse.ArgumentParser(description="Build nojs/, a static JavaScript-free copy of the site.")
    ap.add_argument("--root", type=Path, default=ROOT, help="site root (default: the repo)")
    ap.add_argument("--out", default="nojs", help="output folder inside the root (default: nojs)")
    ap.add_argument("--node", default="node", help="node executable (default: node)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if the output is out of date")
    args = ap.parse_args()

    root = args.root.resolve()
    sources = {p.stem: p for p in sorted(root.glob("*.html")) if (root / "data" / (p.stem + ".js")).exists()}
    if not sources:
        sys.exit(f"No <page>.html with a matching data/<page>.js found in {root}")

    proc = subprocess.run(
        [args.node, "-e", NODE_LOADER, str(root), *sources], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        sys.exit("node could not read the data files:\n" + proc.stderr)
    loaded = json.loads(proc.stdout)

    builder = Builder(loaded["site"], set(sources))
    outdir = root / args.out
    stale = []
    for stem, path in sources.items():
        text = build_page(stem, path.read_text(encoding="utf-8"), loaded["pages"][stem], builder)
        target = outdir / (stem + ".html")
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current != text:
            stale.append(target.relative_to(root))
            if not args.check:
                outdir.mkdir(exist_ok=True)
                target.write_text(text, encoding="utf-8")

    if args.check:
        if stale:
            print("Out of date (run tools/build_nojs.py):", *map(str, stale), sep="\n  ")
            sys.exit(1)
        print(f"{args.out}/ is up to date.")
    else:
        print(f"Wrote {len(sources)} page(s) to {args.out}/ ({len(stale)} changed).")


if __name__ == "__main__":
    main()
