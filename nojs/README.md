# nojs/ — generated, not edited by hand

This folder holds a **text-only, JavaScript-free copy of every page** of the
site, for visitors who have JavaScript turned off. Each page in the main site
links here from its `<noscript>` notice (for example `about.html` links to
`nojs/about.html`).

Visitors who *do* have JavaScript are redirected straight on to the full page
(each generated page starts with a one-line script that does this). To look at a
text-only page with JavaScript on, add `?text` to its URL, for example
`nojs/about.html?text`.

**Everything here except this README is generated and git-ignored.** If you are
browsing the repository and don't see any `.html` files in this folder, that is
expected: they are not stored in git.

## How the files get here

`tools/build_nojs.py` writes `nojs/<page>.html` for each top-level `<page>.html`,
using that page's header and nav, its text from `data/<page>.js`, and the footer
from `js/site-data.js`.

- **On the live site**, the GitHub Actions workflow
  [`.github/workflows/pages.yml`](../.github/workflows/pages.yml) runs the build
  on every push to `main` and publishes the result along with the rest of the site.
- **Locally**, run it yourself to preview or to check the output:

  ```
  python3 tools/build_nojs.py          # (re)generate nojs/*.html; needs node
  python3 tools/build_nojs.py --check  # exit 1 if nojs/ is out of date
  ```

Don't edit the `.html` files here; they are overwritten on every build. To change
what they say, edit `data/*.js`, `js/site-data.js`, or a page's header/nav, then
rebuild. The main site never needs this folder to work.
