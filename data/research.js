/* =====================================================================
   research.js — the text for research.html.

   This is a JavaScript file laid out like JSON: keep the "quotes", and put
   a comma between items. (Unlike strict JSON, comments like this one and a
   trailing comma after the last item are allowed.) See README.md for every
   field.
   ===================================================================== */
window.PAGE = {
  "title": "Research",
  "kicker": "Sector 02 · Science operations",
  "intro": "Using large simulations to ask astrophysical questions. (Placeholder text — replace with your own.)",
  "image": "rotate",
  "sections": [
    {
      "id": "threads",
      "label": "Research Threads",
      "type": "cards",
      "intro": "One card per research thread. Add an \"href\" to link a card to its papers.",
      "items": [
        {
          "meta": "Thread 01",
          "title": "Research thread one",
          "text": "Placeholder: the question, the method, and the main result in two sentences.",
          "tags": [
            "Simulation",
            "Theory"
          ],
          "href": "publications.html"
        },
        {
          "meta": "Thread 02",
          "title": "Research thread two",
          "text": "Placeholder: a second line of work.",
          "tags": [
            "Numerics"
          ]
        },
        {
          "meta": "Thread 03",
          "title": "Research thread three",
          "text": "Placeholder: a third line of work.",
          "tags": [
            "Observations"
          ]
        }
      ]
    },
    {
      "id": "methods",
      "label": "Methods & Codes",
      "type": "cards",
      "items": [
        {
          "title": "Simulation codes",
          "text": "Placeholder: the codes you develop or use.",
          "tags": [
            "C++",
            "Fortran",
            "Python"
          ]
        },
        {
          "title": "Analysis",
          "text": "Placeholder: how you turn simulation output into science.",
          "tags": [
            "NumPy",
            "yt"
          ]
        }
      ]
    },
    {
      "id": "collaborations",
      "label": "Collaborations",
      "type": "text",
      "paragraphs": [
        "Placeholder: groups, collaborations, and people you work with."
      ]
    }
  ]
};
