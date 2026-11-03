/* =====================================================================
   psf-star.js — draws a star the way a telescope "sees" it: a bright core,
   a soft halo, and diffraction spikes. Used for the "." in the wordmark
   and for the bright stars in the placeholder starfield.

   Usage:  Site.psfStar(params)  → returns an <svg> element
           Site.psfParams({ preset: "jwst", rotation: 0 }) → params
   The star is drawn in "currentColor", so CSS `color` sets its color.
   ===================================================================== */
(function () {
  "use strict";
  var Site = (window.Site = window.Site || {});

  var NS = "http://www.w3.org/2000/svg";
  var counter = 0; // gives every star's gradients a unique id

  // Small helper: make an SVG element and set its attributes.
  function svgEl(tag, attrs) {
    var node = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach(function (key) {
      node.setAttribute(key, attrs[key]);
    });
    return node;
  }

  // Look up a preset by name and add the per-image rotation.
  Site.psfParams = function (psf) {
    var presets = (window.SITE && window.SITE.psfPresets) || {};
    var name = (psf && psf.preset) || "none";
    var preset = presets[name] || presets.none || { core: 7, halo: 22, spikes: [] };
    return Object.assign({}, preset, { rotation: (psf && psf.rotation) || 0 });
  };

  Site.psfStar = function (params) {
    var id = "psf" + (++counter);
    var svg = svgEl("svg", { viewBox: "-50 -50 100 100", "aria-hidden": "true", focusable: "false" });

    // --- Gradients: spikes fade out toward their tips; the core fades at its edge.
    var defs = svgEl("defs");
    var spikeGrad = svgEl("linearGradient", { id: id + "-spike", x1: "0", y1: "0", x2: "1", y2: "0" });
    spikeGrad.append(
      svgEl("stop", { offset: "0", "stop-color": "currentColor", "stop-opacity": "1" }),
      svgEl("stop", { offset: "1", "stop-color": "currentColor", "stop-opacity": "0" })
    );
    var coreGrad = svgEl("radialGradient", { id: id + "-core" });
    coreGrad.append(
      svgEl("stop", { offset: "0", "stop-color": "currentColor", "stop-opacity": "1" }),
      svgEl("stop", { offset: "0.4", "stop-color": "currentColor", "stop-opacity": "0.85" }),
      svgEl("stop", { offset: "1", "stop-color": "currentColor", "stop-opacity": "0" })
    );
    defs.append(spikeGrad, coreGrad);
    svg.append(defs);

    // Everything is grouped so the whole star can be rotated to match the photo.
    var g = svgEl("g", { transform: "rotate(" + (params.rotation || 0) + ")" });

    // Halo: a big faint glow.
    g.append(svgEl("circle", { r: params.halo || 16, fill: "url(#" + id + "-core)", opacity: "0.35" }));

    // Spikes: each one is a thin diamond pointing along +x, then rotated.
    (params.spikes || []).forEach(function (s) {
      var w = s.width, L = s.length;
      g.append(svgEl("path", {
        d: "M0 " + (-w) + " L" + L + " 0 L0 " + w + " Z",
        fill: "url(#" + id + "-spike)",
        opacity: s.opacity == null ? 1 : s.opacity,
        transform: "rotate(" + s.angle + ")",
      }));
    });

    // JWST only: a faint hexagon hinting at the mirror's shape.
    if (params.hex) {
      var r = (params.core || 6) * 1.7, pts = [];
      for (var k = 0; k < 6; k++) {
        var a = (Math.PI / 180) * (-90 + 60 * k);
        pts.push((r * Math.cos(a)).toFixed(2) + "," + (r * Math.sin(a)).toFixed(2));
      }
      g.append(svgEl("polygon", {
        points: pts.join(" "), fill: "none", stroke: "currentColor",
        "stroke-width": "0.7", opacity: "0.5",
      }));
    }

    // Core: the bright center.
    g.append(svgEl("circle", { r: params.core || 6, fill: "url(#" + id + "-core)" }));

    svg.append(g);
    return svg;
  };
})();
