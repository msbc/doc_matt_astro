/* theme-init.js — runs BEFORE the page is drawn.
   1. Picks one of the LCARS styles at random (new pick on every page load)
      and sets <html data-style="...">. The colors for each style live in
      css/tokens.css. Add a style here AND there.
   2. If the visitor picked light or dark with the toggle on an earlier visit,
      apply it now so the page never flashes in the wrong theme.
      (No saved choice = follow the system setting, handled purely in CSS.) */
(function () {
  var styles = ["lower-decks", "lower-decks-padd", "picard"];

  // Uniform random index from the browser's cryptographic generator.
  // Values past the largest multiple of styles.length are redrawn so no style is favored.
  function randomIndex(n) {
    var c = window.crypto || window.msCrypto;
    if (!c || !c.getRandomValues) return Math.floor(Math.random() * n);
    var buf = new Uint32Array(1);
    var limit = Math.floor(4294967296 / n) * n;
    do { c.getRandomValues(buf); } while (buf[0] >= limit);
    return buf[0] % n;
  }

  document.documentElement.setAttribute("data-style", styles[randomIndex(styles.length)]);

  try {
    var saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") {
      document.documentElement.setAttribute("data-theme", saved);
    }
  } catch (e) {
    /* Storage can be blocked (e.g. private mode). The CSS still follows the system. */
  }
})();
