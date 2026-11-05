/* =====================================================================
   error-trap.js — remembers script errors so the page can show them.

   A typo in a data/*.js file is a syntax error the browser only prints to
   its console. This file loads first on every page (before the data
   files), records those errors, and render.js lists them in the red
   CONTENT ERROR panel with the file and line number. It also records a
   script that failed to load at all (e.g. a missing data file).
   ===================================================================== */
(function () {
  "use strict";
  var errors = (window.scriptErrors = []);

  // "file:///…/site/data/about.js" → "data/about.js"
  function shortName(url) {
    return String(url).replace(/^.*\/(?=(?:data|js)\/)/, "").replace(/[?#].*$/, "");
  }

  // Capture phase, so we also hear a <script> that failed to load (those don't bubble).
  window.addEventListener("error", function (e) {
    var t = e.target;
    if (t && t.tagName === "SCRIPT") {
      errors.push("Could not load " + shortName(t.src) + " (is the file missing or misnamed?)");
    } else if (e.filename) {
      errors.push(shortName(e.filename) + ", line " + e.lineno + ": " + e.message);
    } else if (/^Script error\.?$/.test(e.message || "")) {
      // Browsers hide the file and line of errors in scripts opened straight from disk.
      errors.push("A script has an error, but the browser hides where when a page is opened " +
        "straight from disk. Look in the browser console, or preview with " +
        "`python3 -m http.server` (then open http://localhost:8000) to see the file and line here.");
    }
  }, true);
})();
