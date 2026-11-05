/* =====================================================================
   about.js — the text for about.html.

   This is a JavaScript file laid out like JSON: keep the "quotes", and put
   a comma between items. (Unlike strict JSON, comments like this one and a
   trailing comma after the last item are allowed.) See README.md for every
   field.
   ===================================================================== */
window.PAGE = {
  "title": "About",
  "kicker": "Sector 01 · Personnel file",
  "intro": "Computational astrophysicist and HPC specialist.",
  "image": "rotate",
  "sections": [
    {
      "id": "bio",
      "label": "Bio",
      "type": "text",
      "paragraphs": [
        "Placeholder bio — replace with your own. I'm a computational astrophysicist who works where astrophysics meets high-performance computing: writing, running, and speeding up large simulations.",
        "These days I'm a *Performance Tuning Analyst*, helping researchers make their codes run faster on modern clusters. See the [Computing](computing.html) page for more."
      ]
    },
    {
      "id": "path",
      "label": "Flight Path",
      "type": "timeline",
      "items": [
        {
          "when": "Present",
          "title": "Performance Tuning Analyst",
          "where": "Your institution",
          "text": "Profiling and optimizing research software on HPC systems."
        },
        {
          "when": "Year – Year",
          "title": "Postdoctoral Researcher",
          "where": "Institution",
          "text": "Placeholder: what you worked on."
        },
        {
          "when": "Year",
          "title": "Ph.D., Astrophysics",
          "where": "University",
          "text": "Thesis: *Placeholder thesis title*."
        }
      ]
    },
    {
      "id": "interests",
      "label": "Interests",
      "type": "cards",
      "items": [
        {
          "title": "Astrophysical simulation",
          "text": "Placeholder: numerical methods and the physics they capture.",
          "tags": [
            "Hydrodynamics",
            "MHD"
          ]
        },
        {
          "title": "Performance engineering",
          "text": "Placeholder: making scientific code fast and scalable.",
          "tags": [
            "Profiling",
            "GPUs"
          ]
        },
        {
          "title": "Astrophotography",
          "text": "Placeholder: the pictures that make it all worth it.",
          "tags": [
            "HST",
            "JWST",
            "Rubin"
          ]
        }
      ]
    }
  ]
};
