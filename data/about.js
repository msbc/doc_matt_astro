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
          "when": "Jan 2023 – May 2024",
          "title": "Teaching Assistant Professor / Lecturer",
          "where": "Stevens Institute of Technology",
          "text": "Mentored master’s theses and created content for astrophysics courses."
        },
        {
          "when": "Aug 2020 – Jan 2023",
          "title": "Postdoctoral Researcher",
          "where": "Princeton University",
          "text": "Simulations of core-collapse supernovae and of the kicks and spins of newborn neutron stars."
        },
        {
          "when": "Sep 2017 – Aug 2020",
          "title": "Postdoctoral Researcher",
          "where": "Institute for Advanced Study",
          "text": "Accretion-disk boundary layers, and numerical methods for astrophysical fluids, including equation-of-state tools for Athena++."
        },
        {
          "when": "June 2017",
          "title": "Ph.D., Physics",
          "where": "University of California, Santa Barbara",
          "text": "Dissertation: *Convection Affects Magnetic Turbulence in White Dwarf Accretion Disks*. Adviser: Omer Blaes."
        },
        {
          "when": "June 2011",
          "title": "B.S., Physics (Summa Cum Laude)",
          "where": "University of California, Santa Cruz",
          "text": "Thesis: *The Evolution of Supernovae Embedded in Stellar Groups*. Adviser: Enrico Ramirez-Ruiz."
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
          "text": "Numerical simulations of accretion disks, core-collapse supernovae, and other astrophysical flows, and the numerical methods and microphysics behind them.",
          "tags": [
            "Hydrodynamics",
            "MHD",
            "Accretion disks",
            "Supernovae"
          ]
        },
        {
          "title": "Performance engineering",
          "text": "Making scientific code fast and scalable, for example porting the radiation-hydrodynamics code *Fornax* to GPUs with OpenMP.",
          "tags": [
            "Profiling",
            "GPUs",
            "OpenMP"
          ]
        },
        {
          "title": "Finishing this website",
          "text": "I’m still working on this site, and I hope to add more content soon.",
          "tags": [
            "HTML",
            "CSS",
            "JavaScript"
          ]
        }
      ]
    }
  ]
};
