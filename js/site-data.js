/* =====================================================================
   site-data.js — settings shared by EVERY page.

   This is a JavaScript file, but it's laid out like JSON so it's easy to
   edit: change the text between the quotes. (Unlike strict JSON, comments
   like this one and trailing commas are allowed here.)

   Each page's own text lives in its own file in the data/ folder
   (data/about.js for about.html, and so on).
   ===================================================================== */

window.SITE = {
  owner: {
    name: "Matt Coleman",
    // How your name appears in author lists. Any author string that STARTS
    // with one of these counts as "first author"; every match is bolded.
    // List the longest spelling first, or only the "Coleman, M." part of
    // "Coleman, M. S. B." gets bolded.
    pubNames: ["Coleman, M. S. B.", "Coleman, M."],
  },

  // The wordmark is "before" + PSF star + "after".
  wordmark: { before: "Doc", after: "Matt Astro" },

  // Footer links (shown on every page).
  footer: {
    note: "© 2026 Matt Coleman",
    readout: "NODE: HPC-01 // STATUS: NOMINAL",
    links: [
      { label: "Email",  href: "mailto:matthew.s.b.coleman@gmail.com" },
      { label: "GitHub", href: "https://github.com/msbc" },
      { label: "ORCID",  href: "https://orcid.org/0000-0001-5939-5957" },
    ],
  },

  /* ---------------------------------------------------------------
     IMAGE ROTATION
     Pages whose data says  "image": "rotate"  take turns through this
     list: every page view shows a randomly chosen photo, so clicking
     around the site tours different telescopes. On the home page the
     photo also changes by itself every `rotationSeconds` (0 = never),
     with a pause button. Visitors who ask for reduced motion start paused.

     WEIGHTS: an entry is either a name, or { name, weight } where a
     weight of 3 is picked three times as often as the default 1
     (0 = never). Example:  { name: "jwst-carina", weight: 3 }

     DECAY: to avoid repeats, photos shown recently are made less likely.
     rotationDecay lists the multiplier for the photo shown last, the one
     before, and the one before that; anything older counts in full.
     [0, 1/3, 2/3] = "never the last one, rarely the one before, ...".
     Use [] to turn decay off. If two photos show the same thing, give
     both the same  object: "<id>"  in the registry below: showing one
     holds the other back too, but one decay step more mildly (so with
     the default, a sibling of the last photo is ⅓ as likely).
     --------------------------------------------------------------- */
  rotation: ["placeholder-jwst", "placeholder-hst", "placeholder-rubin"],
  rotationDecay: [0, 1 / 3, 2 / 3],
  rotationSeconds: 300, // 5 minutes

  /* ---------------------------------------------------------------
     IMAGE REGISTRY — one entry per background photo.
     A page picks its photo with  "image": "<name>"  in its data file
     (or "rotate" to use the rotation list above).

     To add a real photo, put it in img/tierN/, run tools/make_sizes.py, then
     tools/make_image_registry.py (see README.md). Real photos live in js/images.js;
     an entry looks like this:

       "jwst-carina": {
         src: "img/tier1/jwst-carina",         // path WITHOUT the _2pow<nn>.jpg ending
         ladder: [[8, 356], [9, 713], [10, 1426]],  // [n, real width] for each <src>_2pow<nn>.jpg
         alt: "Glowing gas cliffs of the Carina Nebula studded with young stars",
         title: "Cosmic Cliffs, Carina Nebula",
         credit: "NASA, ESA, CSA, STScI",
         license: "CC BY 4.0",
         sourceUrl: "https://webbtelescope.org/...",
         object: "carina",                     // optional: same value on other photos of this target
         psf: { preset: "jwst", rotation: 0 },  // match the spikes in the photo
       },

     src: null means "no photo yet" and draws a placeholder starfield
     (starfield: 1, 2 or 3 picks its color scheme).
     --------------------------------------------------------------- */
  images: {
    "placeholder-jwst": {
      src: null,
      starfield: 1,
      alt: "",
      title: "Placeholder starfield",
      credit: "Placeholder art — add a real image in js/site-data.js",
      license: "",
      sourceUrl: "",
      psf: { preset: "jwst", rotation: 0 },
    },
    "placeholder-hst": {
      src: null,
      starfield: 2,
      alt: "",
      title: "Placeholder starfield",
      credit: "Placeholder art — add a real image in js/site-data.js",
      license: "",
      sourceUrl: "",
      psf: { preset: "hst", rotation: 45 },
    },
    "placeholder-rubin": {
      src: null,
      starfield: 3,
      alt: "",
      title: "Placeholder starfield",
      credit: "Placeholder art — add a real image in js/site-data.js",
      license: "",
      sourceUrl: "",
      psf: { preset: "rubin", rotation: 12 },
    },
  },

  /* ---------------------------------------------------------------
     PSF PRESETS — the diffraction pattern each telescope gives a bright star.
     Units: the star is drawn in a 100×100 box centered on 0,0.
       angle   : direction of a spike in degrees (0 = right, 90 = down)
       length  : how far the spike reaches (50 = edge of the box)
       width   : half-thickness of the spike where it leaves the core
       opacity : 0 (invisible) to 1 (full)
       core    : radius of the bright center
       halo    : radius of the soft glow around it
       hex     : true draws JWST's faint hexagonal core outline
     --------------------------------------------------------------- */
  psfPresets: {
    // JWST: 6 big spikes from the hexagonal mirror segments (two vertical),
    // plus 2 short faint horizontal ones from the secondary-mirror strut.
    jwst: {
      core: 6, halo: 16, hex: true,
      spikes: [
        { angle: -90, length: 48, width: 1.7, opacity: 1 },
        { angle: -30, length: 48, width: 1.7, opacity: 1 },
        { angle:  30, length: 48, width: 1.7, opacity: 1 },
        { angle:  90, length: 48, width: 1.7, opacity: 1 },
        { angle: 150, length: 48, width: 1.7, opacity: 1 },
        { angle: 210, length: 48, width: 1.7, opacity: 1 },
        { angle:   0, length: 26, width: 0.9, opacity: 0.55 },
        { angle: 180, length: 26, width: 0.9, opacity: 0.55 },
      ],
    },
    // Hubble: a 4-spike cross from the secondary-mirror spider.
    hst: {
      core: 6, halo: 15, hex: false,
      spikes: [
        { angle:   0, length: 48, width: 1.5, opacity: 1 },
        { angle:  90, length: 48, width: 1.5, opacity: 1 },
        { angle: 180, length: 48, width: 1.5, opacity: 1 },
        { angle: 270, length: 48, width: 1.5, opacity: 1 },
      ],
    },
    // Rubin: also a 4-spike cross from its spider vanes; thinner and longer.
    rubin: {
      core: 5.5, halo: 17, hex: false,
      spikes: [
        { angle:   0, length: 50, width: 1.1, opacity: 0.95 },
        { angle:  90, length: 50, width: 1.1, opacity: 0.95 },
        { angle: 180, length: 50, width: 1.1, opacity: 0.95 },
        { angle: 270, length: 50, width: 1.1, opacity: 0.95 },
      ],
    },
    // No telescope: just a soft glowing dot.
    none: { core: 7, halo: 22, hex: false, spikes: [] },
  },
};
