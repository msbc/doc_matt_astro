#!/usr/bin/env python3
"""Build nojs/: a static, JavaScript-free copy of every page.

The main site needs no build step and is never touched by this script.  This
is an optional extra for visitors who have JavaScript turned off: each page's
<noscript> panel links to nojs/<page>.html, which this script writes.

For every top-level <page>.html it
  * takes the page's frame (header, nav, <title>, styles) from that file,
  * reads the page's text from data/<page>.js and the shared settings from
    js/site-data.js (evaluated with node, exactly as a browser would),
  * renders the same sections render.js draws (text, cards, timeline, stats,
    pubs) as plain HTML using the site's existing CSS classes,
  * drops every <script> and the (JS-only) dark-mode button.

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
        scheme = re.match(r"^([a-z][a-z0-9+.-]*):", url, re.I)
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
            out.append(esc(text[last:m.start()]))
            if m.group(1):
                out.append('<a href="%s">%s</a>' % (esc(self.href(m.group(2))), esc(m.group(1))))
            else:
                out.append("<em>%s</em>" % esc(m.group(3)))
            last = m.end()
        out.append(esc(text[last:]))
        return "".join(out)

    # ---- section types (mirror BUILDERS in js/render.js) ----

    def text(self, sec):
        paras = "\n".join("<p>%s</p>" % self.inline(p) for p in sec.get("paragraphs", []))
        return '<div class="prose">\n%s\n</div>' % paras

    def cards(self, sec):
        lis = []
        for item in sec.get("items", []):
            title = esc(item.get("title", ""))
            if item.get("href"):
                title = '<a class="card-link" href="%s">%s</a>' % (esc(self.href(item["href"])), title)
            parts = []
            if item.get("meta"):
                parts.append('<p class="meta">%s</p>' % esc(item["meta"]))
            parts.append("<h3>%s</h3>" % title)
            if item.get("before") or item.get("after"):
                parts.append(self.speedup(item))
            if item.get("text"):
                parts.append("<p>%s</p>" % self.inline(item["text"]))
            if item.get("tags"):
                tags = "".join("<li>%s</li>" % esc(t) for t in item["tags"])
                parts.append('<ul class="tags" aria-label="Tags">%s</ul>' % tags)
            lis.append('<li><article class="card">\n%s\n</article></li>' % "\n".join(parts))
        return '<ul class="cards">\n%s\n</ul>' % "\n".join(lis)

    @staticmethod
    def speedup(item):
        parts = [
            "<dt>Before</dt><dd>%s</dd>" % esc(item.get("before") or "—"),
            "<dt>After</dt><dd>%s</dd>" % esc(item.get("after") or "—"),
        ]
        if item.get("gain"):
            parts.append('<dd class="gain">%s</dd>' % esc(item["gain"]))
        return '<dl class="speedup">%s</dl>' % "".join(parts)

    def timeline(self, sec):
        lis = []
        for item in sec.get("items", []):
            parts = []
            if item.get("when"):
                parts.append('<p class="meta">%s</p>' % esc(item["when"]))
            parts.append("<h3>%s</h3>" % esc(item.get("title", "")))
            if item.get("where"):
                parts.append('<p class="meta">%s</p>' % esc(item["where"]))
            if item.get("text"):
                parts.append("<p>%s</p>" % self.inline(item["text"]))
            lis.append("<li>\n%s\n</li>" % "\n".join(parts))
        return '<ol class="timeline">\n%s\n</ol>' % "\n".join(lis)

    def stats(self, sec):
        rows = []
        for item in sec.get("items", []):
            dd = '<span class="readout-value">%s</span>' % esc(item.get("value", ""))
            if item.get("note"):
                dd += '<span class="readout-note">%s</span>' % self.inline(item["note"])
            rows.append('<div class="readout"><dt>%s</dt><dd>%s</dd></div>' % (esc(item.get("label", "")), dd))
        return '<dl class="readouts">\n%s\n</dl>' % "\n".join(rows)

    def pubs(self, sec):
        lis = []
        for pub in sec.get("items", []):
            authors = str(pub.get("authors", ""))
            links = []
            if pub.get("ads"):
                ads = str(pub["ads"])
                links.append(("ADS", ads if re.match(r"https?:", ads) else "https://ui.adsabs.harvard.edu/abs/" + ads))
            if pub.get("arxiv"):
                links.append(("arXiv", "https://arxiv.org/abs/" + str(pub["arxiv"])))
            if pub.get("doi"):
                links.append(("DOI", "https://doi.org/" + str(pub["doi"])))
            if pub.get("url"):
                links.append(("Link", pub["url"]))
            body = [
                '<p class="pub-title">%s</p>' % self.inline(pub.get("title", "")),
                '<p class="pub-authors">%s</p>' % self.bold_owner(authors),
            ]
            if pub.get("venue"):
                body.append('<p class="pub-venue">%s</p>' % esc(pub["venue"]))
            if links:
                items = "".join('<li><a href="%s">%s</a></li>' % (esc(self.href(u)), esc(label)) for label, u in links)
                body.append('<ul class="pub-links">%s</ul>' % items)
            first = " data-first" if any(authors.strip().startswith(n) for n in self.owner_names) else ""
            lis.append('<li class="pub"%s><span class="pub-year">%s</span>\n<div>\n%s\n</div></li>'
                       % (first, esc(pub.get("year", "")), "\n".join(body)))
        return '<ol class="pubs">\n%s\n</ol>' % "\n".join(lis)

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
            out.append(esc(rest[:hit[0]]) + "<strong>%s</strong>" % esc(hit[1]))
            rest = rest[hit[0] + len(hit[1]):]
        return "".join(out)

    # ---- page pieces ----

    def section(self, sec, index):
        sid = sec.get("id") or slug(sec.get("label") or "section-%d" % (index + 1))
        code = "%02d" % (index + 1)
        kind = sec.get("type")
        build = getattr(self, kind, None) if kind in ("text", "cards", "timeline", "stats", "pubs") else None
        if build is None:
            raise SystemExit('Section "%s" has unknown type "%s".' % (sec.get("label") or sid, kind))
        intro = '<p class="section-intro">%s</p>\n' % self.inline(sec["intro"]) if sec.get("intro") else ""
        return (
            '<section class="section section--%s" id="%s" data-label="%s" data-code="%s" aria-labelledby="%s-title">\n'
            '<header class="section-head"><span class="section-code" aria-hidden="true">%s</span>'
            '<h2 id="%s-title">%s</h2></header>\n%s%s\n</section>'
            % (kind, esc(sid), esc(sec.get("label") or sid), code, esc(sid), code, esc(sid),
               esc(sec.get("label", "")), intro, build(sec))
        )

    def main(self, stem, page):
        home = bool(page.get("home"))
        if home:
            wm = self.site.get("wordmark") or {"before": "Doc", "after": "Matt Astro"}
            heading = ('<h1>%s<span class="sr-only">.</span><span class="psf" aria-hidden="true"></span> %s</h1>'
                       % (esc(wm["before"]), esc(wm["after"])))
        else:
            heading = "<h1>%s</h1>" % esc(page.get("title", ""))
        panel = []
        if page.get("kicker"):
            panel.append('<p class="kicker">%s</p>' % esc(page["kicker"]))
        panel.append(heading)
        if page.get("intro"):
            panel.append("<p>%s</p>" % self.inline(page["intro"]))
        sections = "\n".join(self.section(s, i) for i, s in enumerate(page.get("sections", [])))
        return (
            '<main id="main" tabindex="-1">\n'
            '<div class="noscript-panel"><p>This is the text-only version of this page. '
            '<a href="../%s.html">Open the full site</a> (needs JavaScript).</p></div>\n'
            '<div class="viewscreen%s" style="min-height:0;padding-top:0">\n'  # no photo, so no photo-sized gap
            '<div class="viewscreen-panel dark-island">\n%s\n</div>\n</div>\n'
            "%s\n</main>"
            % (stem, " viewscreen--hero" if home else "", "\n".join(panel), sections)
        )

    def footer(self):
        data = self.site.get("footer")
        if not data:
            return '<footer class="site-footer"></footer>'
        links = "".join('<li><a href="%s">%s</a></li>' % (esc(self.href(l["href"])), esc(l["label"]))
                        for l in data.get("links", []))
        return ('<footer class="site-footer">\n<p>%s</p>\n<ul>%s</ul>\n<p aria-hidden="true">%s</p>\n</footer>'
                % (esc(data.get("note", "")), links, esc(data.get("readout", ""))))


def build_page(stem, source_html, page, builder):
    out = source_html
    out = re.sub(r"[ \t]*<!-- 1\. Apply.*?-->\n", "", out, flags=re.S)
    out = re.sub(r"[ \t]*<!-- 4\. Scripts.*?-->\n", "", out, flags=re.S)
    out = re.sub(r"[ \t]*<script\b[^>]*>.*?</script>\n", "", out, flags=re.S)
    out = re.sub(r"[ \t]*<button id=\"theme-toggle\".*?</button>\n", "", out, flags=re.S)
    out = re.sub(r"<!-- Page text lives in .*?-->\n", "", out, flags=re.S)
    out = re.sub(r'\b(href|src)="(css|cv|js|img|data)/', r'\1="../\2/', out)  # we live in nojs/
    new_main = builder.main(stem, page)
    new_footer = builder.footer()
    out, n1 = re.subn(r'<main id="main".*?</main>', lambda m: new_main, out, flags=re.S)
    out, n2 = re.subn(r'<footer class="site-footer">.*?</footer>', lambda m: new_footer, out, flags=re.S)
    if n1 != 1 or n2 != 1:
        raise SystemExit("%s.html: expected one <main id=\"main\"> and one <footer class=\"site-footer\">." % stem)
    note = ("<!-- GENERATED by tools/build_nojs.py from %s.html, data/%s.js and js/site-data.js. "
            "Do not edit; re-run the script. -->\n" % (stem, stem))
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
        sys.exit("No <page>.html with a matching data/<page>.js found in %s" % root)

    proc = subprocess.run([args.node, "-e", NODE_LOADER, str(root), *sources], capture_output=True, text=True)
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
        print("%s/ is up to date." % args.out)
    else:
        print("Wrote %d page(s) to %s/ (%d changed)." % (len(sources), args.out, len(stale)))


if __name__ == "__main__":
    main()
