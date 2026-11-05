/* =====================================================================
   publications.js — the text for publications.html.

   This is a JavaScript file laid out like JSON: keep the "quotes", and put
   a comma between items. (Unlike strict JSON, comments like this one and a
   trailing comma after the last item are allowed.) See README.md for every
   field.
   ===================================================================== */
window.PAGE = {
  "title": "Publications",
  "kicker": "Sector 03 · Archive",
  "intro": "Your full list is always on [NASA ADS](https://ui.adsabs.harvard.edu/). (Placeholder entries below.)",
  "image": "rotate",
  "sections": [
    {
      "id": "refereed",
      "label": "Refereed",
      "type": "pubs",
      "items": [
        {
          "year": 2026,
          "authors": "Coleman, M., Collaborator, A., & Collaborator, B.",
          "title": "Placeholder: title of a first-author paper",
          "venue": "Journal Name, vol, page"
        },
        {
          "year": 2025,
          "authors": "Collaborator, A., Coleman, M., & Collaborator, C.",
          "title": "Placeholder: title of a co-authored paper",
          "venue": "Journal Name, vol, page"
        },
        {
          "year": 2024,
          "authors": "Coleman, M. & Collaborator, D.",
          "title": "Placeholder: an earlier paper",
          "venue": "Journal Name, vol, page"
        }
      ]
    },
    {
      "id": "other",
      "label": "Proceedings & Software",
      "type": "pubs",
      "items": [
        {
          "year": 2025,
          "authors": "Coleman, M.",
          "title": "Placeholder: a conference proceeding or software release",
          "venue": "Venue"
        }
      ]
    }
  ]
};
