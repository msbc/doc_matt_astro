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
  "intro": "Using large simulations to ask astrophysical questions about accretion disks, compact objects, and core-collapse supernovae.",
  "image": "rotate",
  "sections": [
    {
      "id": "threads",
      "label": "Research Threads",
      "type": "cards",
      "items": [
        {
          "meta": "Thread 01",
          "title": "Accretion disks",
          "text": "How magnetized turbulence, convection, and waves transport angular momentum in accretion disks, including those of cataclysmic variables and their boundary layers.",
          "tags": [
            "MHD",
            "Convection",
            "Boundary layers",
            "Cataclysmic variables"
          ],
          "href": "publications.html"
        },
        {
          "meta": "Thread 02",
          "title": "Core-collapse supernovae & compact objects",
          "text": "Three-dimensional supernova explosions, the kicks and spins of newborn neutron stars, gravitational-wave signatures, and the nucleosynthesis and early evolution of magnetars.",
          "tags": [
            "Supernovae",
            "Neutron stars",
            "High-energy astrophysics"
          ]
        },
        {
          "meta": "Thread 03",
          "title": "Computational methods",
          "text": "Numerical tools for astrophysical fluids: equation-of-state modules and Riemann solvers for realistic, non-ideal fluids.",
          "tags": [
            "Numerics",
            "Microphysics",
            "Radiative transfer"
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
          "text": "I’ve contributed to the open-source MHD code Athena++ and ported the radiation-hydrodynamics code Fornax to GPUs using OpenMP. My simulations have run on national supercomputers, including TACC Frontera and the XSEDE systems Stampede2 and Comet.",
          "tags": [
            "Athena++",
            "Fornax",
            "C++",
            "Python"
          ]
        },
        {
          "title": "Analysis",
          "text": "I still need to put stuff here.",
          "tags": [
            "Python",
            "Numpy",
            "Matplotlib",
            "Jupyter"
          ]
        }
      ]
    },
    {
      "id": "collaborations",
      "label": "Collaborations",
      "type": "text",
      "paragraphs": [
        "My work has been shaped by long collaborations with Omer Blaes (UC Santa Barbara), Roman Rafikov (Cambridge), Adam Burrows (Princeton), and Todd Thompson (Ohio State), along with many coauthors on the [publications](publications.html) page."
      ]
    }
  ]
};
