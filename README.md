# Doc. Matt Astro — personal site

Plain HTML, CSS, and JavaScript. There is no build step and nothing to install. The only outside resource is Google Fonts.

## Preview it

- **Quickest:** double-click `index.html`. The site works when opened straight from disk.
- **Like a real server:** run `python3 -m http.server` in this folder, then open <http://localhost:8000>.

## Where things live

```
index.html, about.html, research.html, publications.html, computing.html, 404.html
                      ← each page; its TEXT is in the JSON block at the top
js/site-data.js       ← settings shared by every page (name, footer, images, star shapes)
css/tokens.css        ← every color, font, and size (light + dark themes)
css/*.css             ← layout and component styles
js/*.js               ← the code that builds pages from the JSON (no need to touch for text edits)
img/                  ← background photos
cv/Matt_Coleman_CV.pdf ← put your CV here (the "CV" button links to it)
```

## Edit the text on a page

Open the page's `.html` file. Near the top is a block that starts with `<script type="application/json" id="page-data">`. Everything you see on the page comes from there.

JSON is strict. Keep these rules in mind:
- Text goes inside "double quotes". To write a quote inside text, use `\"` or curly quotes (“ ”).
- Put a comma between items, but **not** after the last item in a list `[ ]` or object `{ }`.
- If you break a rule, the page shows a red **CONTENT ERROR** panel with a line number, so you won't silently get a blank page.

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
| `pubs` | Publication list with All/First-author filter | `year`, `authors`, `title`, `venue`, `ads` (bibcode or URL), `arxiv` (e.g. `2501.01234`), `doi`, `url` |

Your name is bolded in author lists automatically. Set the spelling(s) in `js/site-data.js` under `owner.pubNames`. Any paper whose author list *starts* with one of those spellings counts as first-author.

Adding a section to the JSON is all it takes: it appears on the page and in the section indicator (the chip in the bottom-right corner).

## Shared settings (`js/site-data.js`)

This file holds the wordmark text, the footer links, the image registry, and the PSF star shapes. It is a JavaScript file, so comments and trailing commas are fine there.

The header wordmark and the navigation are plain HTML, so they still work with JavaScript off. To rename a nav item or add a page, edit the `<nav class="rail">` list in **every** `.html` file. To add a page, copy an existing one, then change its `<title>`, its JSON, and its `aria-current="page"` link.

## Background photos (`js/images.js`)

The photos in `img/tier1/`, `img/tier2/`, … are registered in `js/images.js`, which every page loads right after `site-data.js`. It adds to `SITE.images` and replaces the placeholder `SITE.rotation`. Each entry points at the `_2powNN.jpg` ladder from `tools/make_sizes.py` (`ladder: [[n, pixels], …]`, real widths, because the `NN` in the name is rounded) and the browser picks the rung that fits the screen.

`tools/make_image_registry.py` writes that file from the folders, reading credit, license and title from each photo's embedded metadata (needs `exiftool`). It refuses to overwrite a hand-edited `images.js` unless you pass `--force`. After running it, check:
- **`credit: "TODO"`, `weight: 0`**: the photo has no embedded credit, so it is never shown. Fill in credit and license, then raise the weight.
- **Credits that end after the last complete name**: ESA's embedded credits are cut off at 32 characters, so the generator drops the half-cut last name (marked with a comment). The `sourceUrl` release page has the full credit.
- **`psf` rotation** is `0` everywhere; the telescope is guessed from the credit.
- **Weights** default to 2 for `tier1` and 1 for `tier2`.

## Add a real space photo (the older `-1280` / `-2560` way)

1. **Check the license on the image's release page.**
   - NASA-produced images are generally public domain, but credit is expected.
   - ESA/Webb, ESA/Hubble, and NOIRLab/Rubin images are **CC BY 4.0**, so attribution is required.
   - Never use agency logos.
2. **Make two sizes** (on macOS, `sips` is built in):
   ```sh
   sips -Z 1280 original.jpg --out img/jwst-carina-1280.jpg
   sips -Z 2560 original.jpg --out img/jwst-carina-2560.jpg
   # WebP versions (needs `brew install webp`):
   cwebp -q 80 img/jwst-carina-1280.jpg -o img/jwst-carina-1280.webp
   cwebp -q 80 img/jwst-carina-2560.jpg -o img/jwst-carina-2560.webp
   ```
   Aim for 400 KB or less for the 1280 version.
3. **Add an entry** to `images` in `js/site-data.js`. There's a commented example there. Include `alt` text, `credit`, `license`, and `sourceUrl`; the credit is shown on the photo.
4. **Add its name to `rotation`** in `js/site-data.js` so it joins the slideshow. You can remove the `placeholder-…` names once real photos exist.

### Optional: a ladder of exact power-of-two sizes

`tools/make_sizes.py` makes `<name>_2pow08.jpg` … `<name>_2pow13.jpg` (width ≈ 2^n) for every JPG in `img/`, then renames each original to `<name>_native.jpg`. Each output pixel is the mean of an exact 2^k × 2^k block of source pixels. Where a side isn't divisible, the script trims or mirror-pads a few pixels at the edges (at most 1% trimmed, 0.1% padded per edge). Run `--plan` first to see what it will do.

```sh
pip install pillow numpy
python3 tools/make_sizes.py --plan                  # dry run
python3 tools/make_sizes.py --space oklab           # average in Oklab (also: srgb [default], cielab)
```

With `--space oklab` or `cielab` each image is converted from its own embedded ICC profile (no profile means sRGB), averaged in that space, and converted back. These files use a different naming scheme from the `-1280`/`-2560` pair above, which is what `js/render.js` currently loads.

### How rotation works

- Pages whose JSON says `"image": "rotate"` (all of them, by default) take turns through `SITE.rotation`. Each page view shows a randomly chosen photo, so clicking around the site tours different telescopes.
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

There is nothing to build: GitHub serves the files as they are.

1. Create a repository and push this folder to it.
   - Name it **`<username>.github.io`** and the site appears at `https://<username>.github.io/`.
   - Any other name puts it at `https://<username>.github.io/<repo>/`.
2. In the repository, open **Settings → Pages → Build and deployment**, choose **Deploy from a branch**, select `main` and `/ (root)`, and save.

Also included:
- `404.html`, a themed "Signal Lost" page that GitHub Pages shows for missing URLs.
- `.nojekyll`, an empty file that tells GitHub to serve the files as-is without running its Jekyll processor.

For a custom domain, add it under **Settings → Pages** (GitHub creates the `CNAME` file for you), then point your DNS at GitHub as its docs describe.
