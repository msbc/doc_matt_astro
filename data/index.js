/* =====================================================================
   index.js — the text for index.html.

   This is a JavaScript file laid out like JSON: keep the "quotes", and put
   a comma between items. (Unlike strict JSON, comments like this one and a
   trailing comma after the last item are allowed.) See README.md for every
   field.
   ===================================================================== */
window.PAGE = {
  "home": true,
  "kicker": "Matt Coleman · Computational Astrophysicist & HPC Specialist",
  "intro": "I help researchers turn computing power into scientific insight—and use it myself to explore the fluid dynamics of the universe.",
  "image": "rotate",
  "sections": [
    {
      "id": "consoles",
      "label": "Consoles",
      "type": "cards",
      "items": [
        {
          "meta": "Sector 02",
          "title": "Research",
          "href": "research.html",
          "text": "My research uses computational hydrodynamics to study astrophysical systems, particularly accretion disks, compact objects, and core-collapse supernovae."
        },
        {
          "meta": "Sector 03",
          "title": "Publications",
          "href": "publications.html",
          "text": "Refereed papers, proceedings, and software, with ADS / arXiv / DOI links."
        },
        {
          "meta": "Sector 04",
          "title": "Computing",
          "href": "computing.html",
          "text": "My work as a Performance Tuning Analyst: profiling, optimization, and HPC support."
        }
      ]
    },
    {
      "id": "status",
      "label": "Status",
      "type": "stats",
      "intro": "Placeholder readouts — edit these in index.html.",
      "items": [
        {
          "label": "Current role",
          "value": "Perf. Tuning Analyst",
          "note": "Details on the [Computing](computing.html) page"
        },
        {
          "label": "Field",
          "value": "Comp. Astrophysics"
        },
        {
          "label": "Toolchain",
          "value": "MPI · OpenMP · GPU"
        },
        {
          "label": "Status",
          "value": "Nominal"
        }
      ]
    }
  ]
};
