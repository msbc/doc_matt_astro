/* =====================================================================
   scrollspy.js — the small fixed "you are here" chip, bottom-right.

   It watches every <section class="section"> on the page. Whichever
   section crosses a thin band across the middle of the screen becomes
   the "current" one. Clicking the chip opens a list of all sections.
   It hides itself on pages with fewer than 2 sections.
   ===================================================================== */
(function () {
  "use strict";

  var sections = Array.prototype.slice.call(document.querySelectorAll("main .section[id]"));
  if (sections.length < 2 || !("IntersectionObserver" in window)) return;

  /* ---------- Build the chip and its pop-up list ---------- */
  var wrap = document.createElement("div");
  wrap.className = "indicator";

  var chip = document.createElement("button");
  chip.type = "button";
  chip.className = "indicator-chip";
  chip.setAttribute("aria-expanded", "false");
  chip.setAttribute("aria-controls", "indicator-list");

  var prefix = document.createElement("span");
  prefix.className = "sr-only";
  prefix.textContent = "On this page, current section: ";
  var codeEl = document.createElement("span");
  codeEl.className = "indicator-code";
  var labelEl = document.createElement("span");
  labelEl.className = "indicator-label";
  chip.append(prefix, codeEl, labelEl);

  var nav = document.createElement("nav");
  nav.id = "indicator-list";
  nav.className = "indicator-list";
  nav.setAttribute("aria-label", "On this page");
  nav.hidden = true;
  var ol = document.createElement("ol");
  var links = sections.map(function (sec) {
    var a = document.createElement("a");
    a.href = "#" + sec.id;
    var code = document.createElement("span");
    code.textContent = sec.dataset.code;
    a.append(code, document.createTextNode(sec.dataset.label));
    var li = document.createElement("li");
    li.append(a);
    ol.append(li);
    return a;
  });
  nav.append(ol);
  wrap.append(nav, chip);
  document.body.append(wrap);

  /* ---------- Mark one section as current ---------- */
  function setCurrent(sec) {
    codeEl.textContent = "SEC " + sec.dataset.code;
    labelEl.textContent = sec.dataset.label;
    links.forEach(function (a) {
      if (a.getAttribute("href") === "#" + sec.id) a.setAttribute("aria-current", "location");
      else a.removeAttribute("aria-current");
    });
  }
  setCurrent(sections[0]);

  // The "band": the observer only sees a sliver 40%–45% down the screen.
  var bandObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) setCurrent(entry.target);
    });
  }, { rootMargin: "-40% 0px -55% 0px" });
  sections.forEach(function (sec) { bandObserver.observe(sec); });

  // At the very bottom, short last sections may never reach the band —
  // so a marker at the end of <main> selects the last section when it shows up.
  var endMarker = document.createElement("div");
  endMarker.setAttribute("aria-hidden", "true");
  document.getElementById("main").append(endMarker);
  new IntersectionObserver(function (entries) {
    if (entries[0].isIntersecting) setCurrent(sections[sections.length - 1]);
  }).observe(endMarker);

  /* ---------- Open / close the list ---------- */
  function setOpen(open) {
    nav.hidden = !open;
    chip.setAttribute("aria-expanded", String(open));
  }
  chip.addEventListener("click", function () { setOpen(nav.hidden); });
  links.forEach(function (a) { a.addEventListener("click", function () { setOpen(false); }); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !nav.hidden) { setOpen(false); chip.focus(); }
  });
  document.addEventListener("click", function (e) {
    if (!wrap.contains(e.target)) setOpen(false);
  });
})();
