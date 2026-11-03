/* =====================================================================
   theme-toggle.js — the "Dark mode" switch in the header.

   Pressed  = dark theme showing.  Not pressed = light theme showing.
   If you switch to the SAME theme your system already uses, the saved
   choice is forgotten, so the site goes back to following the system.
   ===================================================================== */
(function () {
  "use strict";
  var root = document.documentElement;
  var button = document.getElementById("theme-toggle");
  if (!button) return;

  var systemDark = window.matchMedia("(prefers-color-scheme: dark)");

  function isDark() {
    var chosen = root.getAttribute("data-theme");
    return chosen ? chosen === "dark" : systemDark.matches;
  }

  function save(value) {
    try {
      if (value) localStorage.setItem("theme", value);
      else localStorage.removeItem("theme");
    } catch (e) { /* storage blocked: the choice just won't be remembered */ }
  }

  function updateButton() {
    button.setAttribute("aria-pressed", String(isDark()));
  }

  button.addEventListener("click", function () {
    var wanted = isDark() ? "light" : "dark";
    var system = systemDark.matches ? "dark" : "light";
    if (wanted === system) {
      root.removeAttribute("data-theme"); // back to "follow the system"
      save(null);
    } else {
      root.setAttribute("data-theme", wanted);
      save(wanted);
    }
    updateButton();
  });

  // Keep the button honest if the system theme changes while the page is open.
  systemDark.addEventListener("change", updateButton);

  button.hidden = false; // the button is hidden in the HTML until JS is ready
  updateButton();
})();
