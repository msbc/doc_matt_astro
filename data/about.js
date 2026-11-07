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
        "I’m an astrophysicist by training, and these days I work as the *Performance Tuning Analyst* in Princeton University’s Research Computing department. I help researchers get more out of modern supercomputers by tuning scientific codes and supporting their work on Princeton’s clusters.",
        "You can learn more about my current work on the [Computing](computing.html) page.",
        "My [research](research.html) background is in computational astrophysics, especially the magnetohydrodynamics of accretion disks and other astrophysical flows. I’ve worked across theoretical astrophysics and numerical simulation, studying topics including cataclysmic variables, compact objects, core-collapse supernovae, and computational methods.",
        "Visit my [research](research.html) page for more details, and my [publications](publications.html) page for a list of my work.",
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
          "where": "Princeton University",
          "text": "HPC facilitation and support for researchers using Princeton’s supercomputing clusters, specializing in profiling and optimizing research software on HPC systems."
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
