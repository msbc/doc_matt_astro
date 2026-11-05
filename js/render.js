/* =====================================================================
   render.js — reads the page's data (window.PAGE) and builds the page.

   You shouldn't need to edit this file to change TEXT — edit the matching
   file in data/ (e.g. data/about.js) instead. Edit this file to add a new
   section TYPE.

   Page data shape (data/<page>.js sets  window.PAGE = { ... };):
   {
     "title": "Research",                // the page's big heading (h1)
     "kicker": "Sector 02",              // small label above the heading (optional)
     "intro": "One or two sentences.",   // text under the heading (optional)
     "image": "rotate",                  // "rotate", or one name from SITE.images
     "home": false,                      // true only on index.html (big hero)
     "sections": [ { "id", "label", "type", "intro", "items" | "paragraphs" } ]
   }

   Section types: text, cards, timeline, stats, pubs  (see BUILDERS below)

   Inside any text you can write:
     [link text](https://example.com)   → a link
     *some words*                       → italics
   ===================================================================== */
(function () {
  "use strict";
  var Site = (window.Site = window.Site || {});
  var SITE = window.SITE || {};

  /* ---------------- Small helpers ---------------- */

  // el("p", { class: "x" }, [children]) → <p class="x">children</p>
  // Text is always added as plain text (never as HTML), so it's safe.
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (value === null || value === undefined || value === false) return;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else node.setAttribute(key, value);
    });
    (children || []).forEach(function (child) {
      if (child === null || child === undefined) return;
      node.append(child); // strings become text, elements are inserted
    });
    return node;
  }

  // Only allow ordinary web, email, and relative links (blocks "javascript:" etc.).
  function safeUrl(url) {
    var scheme = /^([a-z][a-z0-9+.-]*):/i.exec(url);
    if (scheme && ["http", "https", "mailto"].indexOf(scheme[1].toLowerCase()) === -1) return "#";
    return url;
  }

  // Turn "[text](url)" and "*text*" into links and italics; everything else stays plain text.
  var INLINE = /\[([^\]]+)\]\(([^)\s]+)\)|\*([^*]+)\*/g;
  function inline(text) {
    text = String(text);
    var frag = document.createDocumentFragment();
    var last = 0, match;
    INLINE.lastIndex = 0;
    while ((match = INLINE.exec(text)) !== null) {
      frag.append(text.slice(last, match.index));
      if (match[1]) frag.append(el("a", { href: safeUrl(match[2]), text: match[1] }));
      else frag.append(el("em", { text: match[3] }));
      last = match.index + match[0].length;
    }
    frag.append(text.slice(last));
    return frag;
  }

  // "Galaxy Evolution" → "galaxy-evolution" (used when a section has no "id").
  function slug(text) {
    return String(text).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  }

  // Draw the PSF star into every .psf span (the wordmark's "dot").
  function drawPsfMarks(params) {
    document.querySelectorAll(".psf").forEach(function (span) {
      span.textContent = "";
      span.append(Site.psfStar(params));
      span.classList.add("psf--drawn");
    });
  }

  /* ---------------- Section builders ----------------
     Each one takes a section object from the page data and returns an element. */

  var BUILDERS = {
    // "paragraphs": ["First paragraph.", "Second paragraph."]
    text: function (sec) {
      var box = el("div", { class: "prose" });
      (sec.paragraphs || []).forEach(function (p) { box.append(el("p", null, [inline(p)])); });
      return box;
    },

    // "items": [{ "title", "text", "meta", "href", "tags": [], "before", "after", "gain" }]
    cards: function (sec) {
      var list = el("ul", { class: "cards" });
      (sec.items || []).forEach(function (item) {
        var title = item.href
          ? el("a", { class: "card-link", href: safeUrl(item.href), text: item.title })
          : item.title;
        var card = el("article", { class: "card" }, [
          item.meta ? el("p", { class: "meta", text: item.meta }) : null,
          el("h3", null, [title]),
          item.before || item.after ? speedup(item) : null,
          item.text ? el("p", null, [inline(item.text)]) : null,
          item.tags ? el("ul", { class: "tags", "aria-label": "Tags" },
            item.tags.map(function (t) { return el("li", { text: t }); })) : null,
        ]);
        list.append(el("li", null, [card]));
      });
      return list;
    },

    // "items": [{ "when", "title", "where", "text" }]
    timeline: function (sec) {
      var list = el("ol", { class: "timeline" });
      (sec.items || []).forEach(function (item) {
        list.append(el("li", null, [
          item.when ? el("p", { class: "meta", text: item.when }) : null,
          el("h3", { text: item.title }),
          item.where ? el("p", { class: "meta", text: item.where }) : null,
          item.text ? el("p", null, [inline(item.text)]) : null,
        ]));
      });
      return list;
    },

    // "items": [{ "label", "value", "note" }]
    stats: function (sec) {
      var list = el("dl", { class: "readouts" });
      (sec.items || []).forEach(function (item) {
        list.append(el("div", { class: "readout" }, [
          el("dt", { text: item.label }),
          el("dd", null, [
            el("span", { class: "readout-value", text: item.value }),
            item.note ? el("span", { class: "readout-note" }, [inline(item.note)]) : null,
          ]),
        ]));
      });
      return list;
    },

    // "items": [{ "authors", "year", "title", "venue", "ads", "arxiv", "doi", "url" }]
    pubs: function (sec) {
      var wrap = el("div");
      var items = sec.items || [];
      var list = el("ol", { class: "pubs" });

      items.forEach(function (pub) {
        var links = [];
        if (pub.ads)   links.push(["ADS", /^https?:/.test(pub.ads) ? pub.ads : "https://ui.adsabs.harvard.edu/abs/" + pub.ads]);
        if (pub.arxiv) links.push(["arXiv", "https://arxiv.org/abs/" + pub.arxiv]);
        if (pub.doi)   links.push(["DOI", "https://doi.org/" + pub.doi]);
        if (pub.url)   links.push(["Link", pub.url]);

        var li = el("li", { class: "pub" }, [
          el("span", { class: "pub-year", text: pub.year }),
          el("div", null, [
            el("p", { class: "pub-title" }, [inline(pub.title || "")]),
            el("p", { class: "pub-authors" }, [boldOwner(pub.authors || "")]),
            pub.venue ? el("p", { class: "pub-venue", text: pub.venue }) : null,
            links.length ? el("ul", { class: "pub-links" }, links.map(function (l) {
              return el("li", null, [el("a", { href: safeUrl(l[1]), text: l[0] })]);
            })) : null,
          ]),
        ]);
        if (isFirstAuthor(pub.authors || "")) li.setAttribute("data-first", "");
        list.append(li);
      });

      // Filter buttons: All / First author.
      var count = el("p", { class: "pub-count meta", role: "status" });
      var allBtn = el("button", { class: "seg-btn", type: "button", "aria-pressed": "true", text: "All" });
      var firstBtn = el("button", { class: "seg-btn", type: "button", "aria-pressed": "false", text: "First author" });
      function apply(firstOnly) {
        var shown = 0;
        list.querySelectorAll(".pub").forEach(function (li) {
          var show = !firstOnly || li.hasAttribute("data-first");
          li.hidden = !show;
          if (show) shown++;
        });
        allBtn.setAttribute("aria-pressed", String(!firstOnly));
        firstBtn.setAttribute("aria-pressed", String(firstOnly));
        count.textContent = "Showing " + shown + " of " + items.length;
      }
      allBtn.addEventListener("click", function () { apply(false); });
      firstBtn.addEventListener("click", function () { apply(true); });
      apply(false);

      wrap.append(el("div", { class: "pub-filter", role: "group", "aria-label": "Filter " + sec.label }, [allBtn, firstBtn, count]), list);
      return wrap;
    },
  };

  // Before → after readout for case-study cards.
  function speedup(item) {
    return el("dl", { class: "speedup" }, [
      el("dt", { text: "Before" }), el("dd", { text: item.before || "—" }),
      el("dt", { text: "After" }), el("dd", { text: item.after || "—" }),
      item.gain ? el("dd", { class: "gain", text: item.gain }) : null,
    ]);
  }

  // Your name variants from SITE.owner.pubNames.
  function ownerNames() {
    return (SITE.owner && SITE.owner.pubNames) || [];
  }
  function isFirstAuthor(authors) {
    return ownerNames().some(function (n) { return authors.trim().indexOf(n) === 0; });
  }
  // Bold every occurrence of your name in an author list.
  function boldOwner(authors) {
    var frag = document.createDocumentFragment();
    var rest = authors;
    while (rest) {
      var hit = null;
      ownerNames().forEach(function (n) {
        var i = rest.indexOf(n);
        if (i !== -1 && (!hit || i < hit.i)) hit = { i: i, n: n };
      });
      if (!hit) { frag.append(rest); break; }
      frag.append(rest.slice(0, hit.i), el("strong", { text: hit.n }));
      rest = rest.slice(hit.i + hit.n.length);
    }
    return frag;
  }

  /* ---------------- Page pieces ---------------- */

  // Which photo this page shows: a fixed name, or "rotate" = a weighted
  // random pick from SITE.rotation (see Site.pickImage below).
  function pickImageName(page) {
    if (page.image && page.image !== "rotate") return page.image;
    return Site.pickImage() || Object.keys(SITE.images || {})[0];
  }

  // Weighted random pick from SITE.rotation, used on every page view and by
  // rotator.js's timer. Each entry is "name" or { name, weight } (default 1).
  // A photo is also made less likely if its OBJECT was shown recently:
  // SITE.rotationDecay[0] scales the object shown last, [1] the one before,
  // and so on; older ones count in full. Photos that share an `object` in
  // SITE.images (e.g. two views of the Carina Nebula) are held back too, but
  // one decay step more mildly than the photo that was actually shown.
  var memHistory = []; // used when localStorage is blocked
  function readHistory() {
    try {
      var h = JSON.parse(localStorage.getItem("imageHistory"));
      if (Array.isArray(h)) return h;
    } catch (e) {}
    return memHistory;
  }
  function writeHistory(h) {
    memHistory = h;
    try { localStorage.setItem("imageHistory", JSON.stringify(h)); } catch (e) {}
  }
  function objectOf(name) {
    var image = (SITE.images || {})[name];
    return (image && image.object) || name;
  }

  Site.pickImage = function () {
    var entries = (SITE.rotation || []).map(function (e) {
      return typeof e === "string" ? { name: e, weight: 1 } : { name: e.name, weight: e.weight == null ? 1 : e.weight };
    });
    if (!entries.length) return null;
    var decay = SITE.rotationDecay || [];
    var history = readHistory();
    // history holds one photo name per object, most recent first.
    var weights = entries.map(function (e) {
      var obj = objectOf(e.name);
      var i = history.findIndex(function (h) { return objectOf(h) === obj; });
      if (i < 0) return e.weight;
      if (history[i] !== e.name) i++; // a sibling: one step milder
      return e.weight * (i < decay.length ? decay[i] : 1);
    });
    var total = weights.reduce(function (a, b) { return a + b; }, 0);
    if (total <= 0) { // decay ruled everything out (e.g. one object): use plain weights
      weights = entries.map(function (e) { return e.weight; });
      total = weights.reduce(function (a, b) { return a + b; }, 0);
    }
    var pick = entries.length - 1;
    if (total > 0) {
      var r = Math.random() * total;
      for (var k = 0; k < entries.length; k++) {
        r -= weights[k];
        if (r < 0) { pick = k; break; }
      }
    } else {
      pick = Math.floor(Math.random() * entries.length);
    }
    var name = entries[pick].name;
    var obj = objectOf(name);
    writeHistory([name].concat(history.filter(function (h) { return objectOf(h) !== obj; })).slice(0, decay.length));
    return name;
  };

  // Where the bright placeholder stars sit (x/y in %, size in rem), one set per starfield.
  var STAR_SETS = [
    [ { x: 16, y: 30, s: 9 }, { x: 70, y: 20, s: 5 }, { x: 54, y: 72, s: 7 }, { x: 88, y: 58, s: 4 }, { x: 34, y: 84, s: 3.5 } ],
    [ { x: 78, y: 28, s: 8 }, { x: 22, y: 18, s: 4.5 }, { x: 40, y: 62, s: 6 }, { x: 92, y: 80, s: 5 }, { x: 8, y: 70, s: 3.5 } ],
    [ { x: 58, y: 24, s: 10 }, { x: 12, y: 46, s: 5 }, { x: 84, y: 70, s: 6 }, { x: 30, y: 16, s: 3.5 }, { x: 70, y: 90, s: 4 } ],
  ];

  // One full-size photo layer: a real image, or a placeholder starfield.
  function mediaLayer(image) {
    var layer = el("div", { class: "viewscreen-layer" });
    if (image.src && image.ladder && image.ladder.length) {
      // Size ladder from tools/make_sizes.py: <src>_2pow<nn>.jpg, each [nn, real pixel width].
      var rungs = image.ladder.map(function (r) {
        return { url: image.src + "_2pow" + String(r[0]).padStart(2, "0") + ".jpg", width: r[1] };
      });
      // Fallback <img src> for browsers without srcset: the smallest rung that is at least ~1000px.
      var fallback = rungs.filter(function (r) { return r.width >= 1000; })[0] || rungs[rungs.length - 1];
      layer.append(el("picture", { class: "viewscreen-media" }, [
        el("img", {
          src: fallback.url,
          srcset: rungs.map(function (r) { return r.url + " " + r.width + "w"; }).join(", "),
          sizes: "(max-width: 45em) 100vw, 80vw",
          alt: image.alt || "",
          decoding: "async",
        }),
      ]));
    } else if (image.src) {
      var sizes = "(max-width: 45em) 100vw, 80vw";
      layer.append(el("picture", { class: "viewscreen-media" }, [
        el("source", { type: "image/webp", srcset: image.src + "-1280.webp 1280w, " + image.src + "-2560.webp 2560w", sizes: sizes }),
        el("img", {
          src: image.src + "-1280.jpg",
          srcset: image.src + "-1280.jpg 1280w, " + image.src + "-2560.jpg 2560w",
          sizes: sizes,
          alt: image.alt || "",
          decoding: "async",
        }),
      ]));
    } else {
      // Placeholder: CSS starfield plus a few bright stars with this telescope's PSF.
      var variant = image.starfield || 1;
      layer.append(el("div", { class: "starfield starfield--" + variant, "aria-hidden": "true" }));
      var params = Site.psfParams(image.psf);
      STAR_SETS[(variant - 1) % STAR_SETS.length].forEach(function (star) {
        var span = el("span", {
          class: "field-star", "aria-hidden": "true",
          style: "left:" + star.x + "%;top:" + star.y + "%;width:" + star.s + "rem;height:" + star.s + "rem",
        });
        span.append(Site.psfStar(params));
        layer.append(span);
      });
    }
    return layer;
  }

  // Page backdrop: the current photo, blurred and veiled, fixed behind everything
  // outside the header. It is blurred, so a small rung is plenty.
  function backdropUrl(image) {
    if (!image || !image.src) return null;
    if (image.ladder && image.ladder.length) {
      var r = image.ladder.filter(function (x) { return x[1] >= 800; })[0] || image.ladder[image.ladder.length - 1];
      return image.src + "_2pow" + String(r[0]).padStart(2, "0") + ".jpg";
    }
    return image.src + "-1280.jpg";
  }

  Site.showBackdrop = function (name) {
    var url = backdropUrl((SITE.images || {})[name]);
    var box = document.querySelector(".page-backdrop");
    if (!box) {
      box = el("div", { class: "page-backdrop", "aria-hidden": "true" });
      document.body.prepend(box);
    }
    var old = box.querySelectorAll(".page-backdrop-layer");
    if (url) {
      var layer = el("div", { class: "page-backdrop-layer is-entering" }, [el("img", { src: url, alt: "", decoding: "async" })]);
      box.append(layer);
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { layer.classList.remove("is-entering"); });
      });
    }
    setTimeout(function () { old.forEach(function (o) { o.remove(); }); }, 1500);
  };

  // The visible credit line for an image.
  function creditContent(image) {
    var text = "Source: " + (image.credit || "unknown") + (image.license ? " · " + image.license : "");
    return image.sourceUrl ? el("a", { href: safeUrl(image.sourceUrl), text: text }) : text;
  }

  // Switch the viewscreen to another image from SITE.images (used by rotator.js).
  // The new photo fades in over the old one; the logo's star changes to match.
  Site.showImage = function (name) {
    var image = (SITE.images || {})[name];
    var screen = document.querySelector(".viewscreen");
    if (!image || !screen) return;
    var old = screen.querySelectorAll(".viewscreen-layer");
    var layer = mediaLayer(image);
    layer.classList.add("is-entering");
    // Insert just above the current photo (later in the page = drawn on top).
    if (old.length) old[old.length - 1].after(layer);
    else screen.prepend(layer);
    // Two animation frames: let the browser draw it transparent first, then fade it in.
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { layer.classList.remove("is-entering"); });
    });
    setTimeout(function () { old.forEach(function (o) { o.remove(); }); }, 1500);
    var credit = screen.querySelector(".credit");
    credit.textContent = "";
    credit.append(creditContent(image));
    drawPsfMarks(Site.psfParams(image.psf));
    Site.showBackdrop(name);
    Site.imageName = name;
  };

  // The framed space photo (or placeholder) at the top of the page.
  function viewscreen(page, image) {
    var isHome = !!page.home;
    var screen = el("div", { class: "viewscreen" + (isHome ? " viewscreen--hero" : "") });
    screen.append(mediaLayer(image));

    // Text panel on the photo. The home page's heading is the big wordmark.
    var heading;
    if (isHome) {
      var wm = SITE.wordmark || { before: "Doc", after: "Matt Astro" };
      heading = el("h1", null, [
        wm.before,
        el("span", { class: "sr-only", text: "." }),
        el("span", { class: "psf", "aria-hidden": "true" }),
        " " + wm.after,
      ]);
    } else {
      heading = el("h1", { text: page.title });
    }
    screen.append(el("div", { class: "viewscreen-panel dark-island" }, [
      page.kicker ? el("p", { class: "kicker", text: page.kicker }) : null,
      heading,
      page.intro ? el("p", null, [inline(page.intro)]) : null,
    ]));

    // Top strip: image credit (rotator.js adds its pause button here too).
    screen.append(el("div", { class: "viewscreen-top" }, [
      el("p", { class: "credit dark-island" }, [creditContent(image)]),
    ]));

    return screen;
  }

  function renderSection(sec, index) {
    var id = sec.id || slug(sec.label || "section-" + (index + 1));
    var code = String(index + 1).padStart(2, "0"); // 1 → "01"
    var builder = BUILDERS[sec.type];
    if (!builder) {
      throw new Error('Section "' + (sec.label || id) + '" has unknown type "' + sec.type +
        '". Use one of: ' + Object.keys(BUILDERS).join(", ") + ".");
    }
    return el("section", {
      class: "section section--" + sec.type,
      id: id,
      "data-label": sec.label || id,
      "data-code": code,
      "aria-labelledby": id + "-title",
    }, [
      el("header", { class: "section-head" }, [
        el("span", { class: "section-code", "aria-hidden": "true", text: code }),
        el("h2", { id: id + "-title", text: sec.label }),
      ]),
      sec.intro ? el("p", { class: "section-intro" }, [inline(sec.intro)]) : null,
      builder(sec),
    ]);
  }

  // Footer links from SITE.footer.
  function renderFooter() {
    var footer = document.querySelector(".site-footer");
    var data = SITE.footer;
    if (!footer || !data) return;
    footer.textContent = "";
    footer.append(
      el("p", { text: data.note }),
      el("ul", null, (data.links || []).map(function (l) {
        return el("li", null, [el("a", { href: safeUrl(l.href), text: l.label })]);
      })),
      el("p", { "aria-hidden": "true", text: data.readout })
    );
  }

  // A visible red panel instead of a blank page when something's wrong.
  function showError(main, title, message, hint) {
    main.append(el("div", { class: "content-error", role: "alert" }, [
      el("h2", { text: title }),
      el("pre", { text: message }),
      hint ? el("p", { text: hint }) : null,
    ]));
  }

  // The page's text is a .js file, so a typo is a syntax error the browser reports
  // in its console (with file and line) and window.PAGE never gets defined.
  var MISSING_DATA_HINT =
    "This page's text file in the data/ folder didn't load. Open the browser console " +
    "(Cmd+Option+J in Chrome, Cmd+Option+K in Firefox) to see which line has the problem. " +
    "Common causes: a missing comma, a missing closing bracket, or a straight quote (\") inside text.";

  /* ---------------- Go! ---------------- */
  function render() {
    var main = document.getElementById("main");
    if (!main) return;

    var page = window.PAGE;
    if (!page || typeof page !== "object") {
      showError(main, "Content error", "window.PAGE is not defined.", MISSING_DATA_HINT);
      return;
    }

    try {
      var images = SITE.images || {};
      var name = pickImageName(page);
      var image = images[name];
      if (!image) {
        throw new Error('No image named "' + name + '" in js/site-data.js (check "image" in this page\'s data file, or SITE.rotation).');
      }

      main.append(viewscreen(page, image));
      Site.showBackdrop(name);
      Site.imageName = name;
      (page.sections || []).forEach(function (sec, i) { main.append(renderSection(sec, i)); });
      renderFooter();
      drawPsfMarks(Site.psfParams(image.psf));
    } catch (err) {
      showError(main, "Content error", err.message);
    }
  }

  render();
})();
