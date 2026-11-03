/* =====================================================================
   rotator.js — on the home page, slowly cycles the hero through the
   photos in SITE.rotation (every SITE.rotationSeconds), choosing each
   one with the same weighted pick as a page load (Site.pickImage in
   render.js), with a Pause / Play button.

   - Visitors who prefer reduced motion start paused (they can press Play).
   - It also pauses while the browser tab is hidden.
   ===================================================================== */
(function () {
  "use strict";
  var SITE = window.SITE || {};
  var Site = window.Site || {};
  var list = SITE.rotation || [];
  var seconds = SITE.rotationSeconds || 0;
  var hero = document.querySelector(".viewscreen--hero");
  if (!hero || list.length < 2 || seconds <= 0 || !Site.showImage) return;

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var paused = reduceMotion.matches;
  var timer = null;

  // The Pause / Play button, placed in the strip along the top of the photo.
  var button = document.createElement("button");
  button.type = "button";
  button.className = "rotator-btn dark-island";
  hero.querySelector(".viewscreen-top").prepend(button);

  function next() {
    Site.showImage(Site.pickImage());
  }

  function update() {
    clearInterval(timer);
    timer = null;
    if (!paused && !document.hidden) timer = setInterval(next, seconds * 1000);
    // Icon + text: ❚❚ Pause  /  ▶ Play
    button.textContent = "";
    var icon = document.createElement("span");
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = paused ? "▶" : "❚❚";
    button.append(icon, paused ? " Play slideshow" : " Pause slideshow");
  }

  button.addEventListener("click", function () {
    paused = !paused;
    if (!paused) next(); // pressing Play moves on right away, so it visibly responds
    update();
  });
  document.addEventListener("visibilitychange", update);
  update();
})();
