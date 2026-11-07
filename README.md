# Doc. Matt Astro — personal site

Plain HTML, CSS, and JavaScript. There is no build step and nothing to install. The only outside resource is Google Fonts.

## Preview it

- **Quickest:** double-click `index.html`. The site works when opened straight from disk.
- **Like a real server:** run `python3 -m http.server` in this folder, then open <http://localhost:8000>.

## Where things live

```
index.html, about.html, research.html, publications.html, computing.html, 404.html
                      ← each page's frame (header, nav); its text is NOT here
data/*.js             ← the TEXT of each page (data/about.js is about.html, etc.)
nojs/*.html           ← GENERATED (git-ignored) text-only copy of every page, for visitors with JavaScript off
tools/build_nojs.py   ← regenerates nojs/ (optional; the main site never needs it)
js/site-data.js       ← settings shared by every page (name, footer, images, star shapes)
css/tokens.css        ← every color, font, and size (light + dark themes)
css/*.css             ← layout and component styles
js/*.js               ← the code that builds pages from the data/ files (no need to touch for text edits)
img/                  ← background photos
cv/Matt_Coleman_CV.pdf ← put your CV here (the "CV" button links to it)
```

## Edit the text on a page

Open the page's file in `data/` (for `about.html`, that's `data/about.js`). Everything you see on the page comes from there. Only the page's `<title>` and `<meta description>` live in the `.html` file.

The data file is JavaScript written to look like JSON (`window.PAGE = { ... };`). Keep these rules in mind:
- Text goes inside "double quotes". To write a quote inside text, use `\"` or curly quotes (“ ”).
- Put a comma between items. Comments (`/* ... */` and `// ...`) and a trailing comma after the last item are allowed, because it is a `.js` file.
- If you break a rule, the page shows a red **CONTENT ERROR** panel instead of a blank page. When you preview with `python3 -m http.server` it names the file and line (e.g. `data/about.js, line 11`). When you double-click the file, browsers hide that detail, so the panel tells you to check the browser console or use the server preview.

Inside any text you can write:
- `[link text](https://example.com)` for a link
- `*words*` for *italics*

### Page fields

| Field | What it does |
|---|---|
| `title` | The big heading. On the home page the heading is the wordmark instead. |
| `kicker` | The small cyan label above the heading |
| `intro` | One or two sentences under the heading |
| `image` | Which background photo to use (a name from `js/site-data.js`) |
| `home` | `true` only on `index.html` (gives the big hero) |
| `sections` | The list of sections, in order. Their numbers (01, 02, …) are added automatically. |

### Section types

Every section has `"id"` (a short name for links, like `"case-studies"`), `"label"` (its title), `"type"`, and an optional `"intro"`.

| `type` | Contents | Item fields |
|---|---|---|
| `text` | Paragraphs | `"paragraphs": ["…", "…"]` |
| `cards` | Grid of cards | `title`, `text`, `meta` (small label), `href` (makes the card a link), `tags` (list), `before`/`after`/`gain` (speedup readout) |
| `timeline` | Dated list | `when`, `title`, `where`, `text` |
| `stats` | Readout tiles | `label`, `value`, `note` |
| `pubs` | Publication list with All/First-author filter | `year`, `authors`, `title`, `venue`, `scix` (bibcode or URL), `arxiv` (e.g. `2501.01234`), `doi`, `url` |

Your name is bolded in author lists automatically. Set the spelling(s) in `js/site-data.js` under `owner.pubNames`. Any paper whose author list *starts* with one of those spellings counts as first-author. List the longest spelling first (`"Coleman, M. S. B."` before `"Coleman, M."`), or only the shorter prefix is bolded.

Adding a section to the data file is all it takes: it appears on the page and in the section indicator (the chip in the bottom-right corner).

## Update the publications list (`tools/pub_find.py`)

`publications.html` is filled in from SciX rather than typed by hand:

```
uv run tools/pub_find.py --site       # rewrites the paper lists in data/publications.js
```

It needs a SciX API token (see the top of `tools/pub_find.py`; yours is in `~/.ads/dev_key`). Then run `python3 tools/build_nojs.py` and commit, as for any other text change.

- **Only the regions between the `// pub_find:begin …` / `// pub_find:end …` comments in `data/publications.js` are rewritten.** The page title, intro, section labels and anything you add outside those comments are left alone. To list a paper SciX doesn't have, add an entry in the same `items` list but outside the comments.
- **Sections:** `refereed` gets the papers SciX marks as refereed; `other` gets the rest (meeting abstracts, proceedings, preprints that were never published) plus dissertations, which SciX flags as refereed but which are always put in `other`.
- **Preprint + published version, or two copies of a thesis, are listed once** (matched by title). The published record is kept and picks up the preprint's arXiv link. The script prints a `Note:` line for each merge.
- **To hide a paper**, add its bibcode to `IGNORE` in `tools/pub_find.py`. Which papers are found at all is set by the config at the top of that file (ORCID, SciX library, advisor names, `MIN_YEAR`).
- **Titles:** simple LaTeX like `$^{56}$Ni` becomes `⁵⁶Ni`. If a title has math the script can't convert, it prints a `Note:` and leaves the `$…$` in; extend `math_to_text` in `tools/pub_find.py` (a hand edit to `publications.js` would be overwritten).
- `--site FILE` writes to another file; `-f apj` etc. still print citations to the terminal as before.

## Text-only version for visitors without JavaScript (`nojs/`)

The main site is built in the browser, so with JavaScript off a page shows only the header, the nav, and a notice. That notice links to `nojs/<page>.html`, a plain-HTML copy of the page. The only script on those pages is a one-line redirect that sends visitors who *do* have JavaScript on to the full page; add `?text` to a `nojs/` URL (e.g. `nojs/about.html?text`) to stay on the text-only version, which is how you preview it. The main site never needs `nojs/` to work: there is still no build step for it.

`nojs/` is generated and git-ignored, so it is not in the repository. After you change `data/*.js`, `js/site-data.js`, or a page's header or nav, regenerate it:

```
python3 tools/build_nojs.py          # writes nojs/*.html  (needs node, which reads the .js data files)
python3 tools/build_nojs.py --check  # writes nothing; exits 1 if nojs/ is out of date
```

Never edit files in `nojs/` by hand; they are overwritten. Because `nojs/` is not committed, the GitHub Actions workflow in `.github/workflows/pages.yml` builds it on every deploy (see *Publish on GitHub Pages* below). Until you switch Pages to "GitHub Actions", the live site's "text-only version" links will 404. The text-only pages show no photo, no theme toggle, and no publication filter buttons. Because the `?text` marker isn't carried across links, clicking to another text-only page with JavaScript on takes you to the full page; add `?text` again, or turn JavaScript off to browse them. Keep the section renderers in `tools/build_nojs.py` in step with `BUILDERS` in `js/render.js` if you add a new section type.

## Shared settings (`js/site-data.js`)

This file holds the wordmark text, the footer links, the image registry, and the PSF star shapes. It is a JavaScript file, so comments and trailing commas are fine there.

The header wordmark and the navigation are plain HTML, so they still work with JavaScript off. To rename a nav item or add a page, edit the `<nav class="rail">` list in **every** `.html` file. To add a page, copy an existing one, then change its `<title>`, its `data/` script tag (and copy the matching `data/*.js` file), and its `aria-current="page"` link.

## Background photos (`js/images.js`)

The photos in `img/tier1/`, `img/tier2/`, … are registered in `js/images.js`, which every page loads right after `site-data.js`. It adds to `SITE.images` and replaces the placeholder `SITE.rotation`. Each entry points at the `_2powNN.jpg` ladder from `tools/make_sizes.py` (`ladder: [[n, pixels], …]`, real widths, because the `NN` in the name is rounded) and the browser picks the rung that fits the screen.

`tools/make_image_registry.py` writes that file from the folders, reading credit, license and title from each photo's embedded metadata (needs `exiftool`). It refuses to overwrite a hand-edited `images.js` unless you pass `--force`. After running it, check:
- **`credit: "TODO"`, `weight: 0`**: the photo has no embedded credit, so it is never shown. Fill in credit and license, then raise the weight.
- **Credits that end after the last complete name**: ESA's embedded credits are cut off at 32 characters, so the generator drops the half-cut last name (marked with a comment). The `sourceUrl` release page has the full credit.
- **`psf` rotation** is `0` everywhere; the telescope is guessed from the credit.
- **Weights** default to 2 for `tier1` and 1 for `tier2`.

## Add a real space photo

1. **Check the license on the image's release page.**
   - NASA-produced images are generally public domain, but credit is expected.
   - ESA/Webb, ESA/Hubble, and NOIRLab/Rubin images are **CC BY 4.0**, so attribution is required.
   - Never use agency logos.
2. **Put the original JPG in `img/tier1/`** (or `tier2`, …), then make the size ladder:
   ```sh
   python3 tools/make_sizes.py --plan                  # dry run
   python3 tools/make_sizes.py --space oklab           # average in Oklab (also: srgb [default], cielab)
   ```
   (needs `pip install pillow numpy`)
3. **Register it:** run `tools/make_image_registry.py` (it refuses to overwrite a hand-edited `js/images.js` without `--force`), or copy an existing entry in `js/images.js` by hand. Include `alt` text, `credit`, `license`, and `sourceUrl`; the credit is shown on the photo.

Photos in `js/images.js` join the slideshow automatically (it replaces `SITE.rotation`). The `placeholder-…` starfields in `js/site-data.js` are only a fallback.

### The size ladder (`_2powNN`)

`tools/make_sizes.py` makes `<name>_2pow08.jpg` … `<name>_2pow13.jpg` (width ≈ 2^n) for every JPG in `img/`, then renames each original to `<name>_native.jpg`. Each output pixel is the mean of an exact 2^k × 2^k block of source pixels. Where a side isn't divisible, the script trims or mirror-pads a few pixels at the edges (at most 1% trimmed, 0.1% padded per edge). With `--space oklab` or `cielab` each image is converted from its own embedded ICC profile (no profile means sRGB), averaged in that space, and converted back.

This is the only naming scheme `js/render.js` loads. An entry needs `src` (the path without the `_2powNN.jpg` ending) and `ladder` (`[[n, real width], …]`; the `NN` in the filename is rounded, so the width is stored separately). An entry with a `src` but no `ladder` shows a placeholder and logs a console warning.

### How rotation works

- Pages whose data says `"image": "rotate"` (all of them, by default) take turns through `SITE.rotation`. Each page view shows a randomly chosen photo, so clicking around the site tours different telescopes.
- Picks are weighted. A `rotation` entry can be `{ name: "jwst-carina", weight: 3 }` (default weight 1, 0 = never).
- `rotationDecay` (default `[0, 1/3, 2/3]`) makes recently shown photos less likely: the last one is never repeated, the one before is a third as likely, the one before that two thirds. Set `[]` to turn it off. The history is remembered in the browser.
- Give several photos of the same target the same `object: "carina"` in `images`, and showing one also holds back the others, one decay step more mildly (with the default, a sibling of the photo just shown is a third as likely, not impossible).
- On the home page the photo also crossfades to another one every `rotationSeconds` (set `0` to turn this off). The logo star changes to match each photo.
- The home page has a **Pause slideshow** button. Visitors who ask their system for reduced motion start paused.
- To pin one page to a single photo, use its name instead: `"image": "jwst-carina"`.

### Match the star to the photo

The "." in **Doc. Matt Astro** is drawn as the point-spread function of the telescope that took the page's photo. Each image entry has `psf: { preset, rotation }`:
- **`preset`** is `jwst` (6 spikes plus 2 faint ones), `hst` (4 spikes), `rubin` (4 thin spikes), or `none`.
- **`rotation`** is in degrees. Turn it until the logo's spikes line up with the spikes on bright stars in the photo.

You can fine-tune spike lengths and widths under `psfPresets` in the same file.

## Colors and themes

All colors are in `css/tokens.css`.
- There are three LCARS styles, with their colors taken from [thelcars.com/themes](https://www.thelcars.com/themes/): **Lower Decks** (orange), **Lower Decks PADD** (blue), and **Picard**. `js/theme-init.js` picks one at random on every page load. Each style is a `:root[data-style="..."]` block in `tokens.css` (Lower Decks is the default block at the top, and is what shows without JavaScript).
- To force one style while testing, run `document.documentElement.dataset.style = "picard"` in the browser console.
- The light theme is at the top.
- The dark theme appears **twice**: once for "system is dark" and once for "visitor picked dark". Edit both together.

The **Dark mode** button remembers a visitor's choice. Picking the theme their system already uses clears that memory, so the site goes back to following the system.

The site respects "reduce motion": visitors with that setting get no transitions or star twinkle.

## Publish on GitHub Pages

The site itself has nothing to build. The one exception is `nojs/` (the text-only pages), which is generated rather than committed, so the site is deployed by a small GitHub Actions workflow (`.github/workflows/pages.yml`) that runs `tools/build_nojs.py` and then publishes the folder.

1. Create a repository and push this folder to it.
   - Name it **`<username>.github.io`** and the site appears at `https://<username>.github.io/`.
   - Any other name puts it at `https://<username>.github.io/<repo>/`.
2. In the repository, open **Settings → Pages → Build and deployment** and set **Source** to **GitHub Actions**. (Not "Deploy from a branch": that would publish the files without running the build, so `nojs/` would be missing.)
3. Push to `main`. The **Deploy site** workflow runs (see the repository's **Actions** tab) and publishes the site. You can also run it by hand from there.

Also included:
- `404.html`, a themed "Signal Lost" page that GitHub Pages shows for missing URLs.
- `.nojekyll`, an empty file that tells GitHub to serve the files as-is without running its Jekyll processor. (The Actions deployment doesn't run Jekyll either; the file is harmless and keeps a branch deployment working.)

For a custom domain, add it under **Settings → Pages** (GitHub creates the `CNAME` file for you), then point your DNS at GitHub as its docs describe.
