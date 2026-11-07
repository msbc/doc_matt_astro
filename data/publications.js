/* =====================================================================
   publications.js — the text for publications.html.

   This is a JavaScript file laid out like JSON: keep the "quotes", and put
   a comma between items. (Unlike strict JSON, comments like this one and a
   trailing comma after the last item are allowed.) See README.md for every
   field.

   The paper lists are WRITTEN BY tools/pub_find.py, not by hand: run
       uv run tools/pub_find.py --site
   and it replaces everything between each "pub_find:begin" / "pub_find:end"
   comment pair below (and nothing else). To add a paper that isn't in SciX,
   put an entry in the same list but OUTSIDE those comments. To hide a paper,
   add its bibcode to IGNORE in tools/pub_find.py.
   ===================================================================== */
window.PAGE = {
  "title": "Publications",
  "kicker": "Sector 03 · Archive",
  "intro": "The complete list is on [NASA ADS](https://ui.adsabs.harvard.edu/).",
  "image": "rotate",
  "sections": [
    {
      "id": "refereed",
      "label": "Refereed",
      "type": "pubs",
      "items": [
        // pub_find:begin refereed (written by tools/pub_find.py; edits here are overwritten)
        {
          "year": 2026,
          "authors": "Vartanyan, D., Burrows, A., Teryoshin, L., Wang, T., Kasen, D., Tsang, B. T.-H., & Coleman, M. S. B.",
          "title": "Simulated 3D ⁵⁶Ni Distributions of Type IIp Supernovae",
          "venue": "ApJ, 1005, 64",
          "ads": "2026ApJ..1005...64V",
          "arxiv": "2509.16314",
          "doi": "10.3847/1538-4357/ae5a99"
        },
        {
          "year": 2025,
          "authors": "Prasanna, T., Coleman, M. S. B., Thompson, T. A., Metzger, B. D., Patel, A., & Meyer, B. S.",
          "title": "Heavy Element Nucleosynthesis in Rotating Protomagnetar Winds",
          "venue": "ApJ, 994, 55",
          "ads": "2025ApJ...994...55P",
          "arxiv": "2507.01094",
          "doi": "10.3847/1538-4357/ae093a"
        },
        {
          "year": 2024,
          "authors": "Prasanna, T., Coleman, M. S. B., & Thompson, T. A.",
          "title": "Favorable Conditions for Heavy Element Nucleosynthesis in Rotating Protomagnetar Winds",
          "venue": "ApJ, 973, 91",
          "ads": "2024ApJ...973...91P",
          "arxiv": "2402.06003",
          "doi": "10.3847/1538-4357/ad4d90"
        },
        {
          "year": 2024,
          "authors": "Burrows, A., Wang, T., Vartanyan, D., & Coleman, M. S. B.",
          "title": "A Theory for Neutron Star and Black Hole Kicks and Induced Spins",
          "venue": "ApJ, 963, 63",
          "ads": "2024ApJ...963...63B",
          "arxiv": "2311.12109",
          "doi": "10.3847/1538-4357/ad2353"
        },
        {
          "year": 2023,
          "authors": "Prasanna, T., Coleman, M. S. B., Raives, M. J., & Thompson, T. A.",
          "title": "The early evolution of magnetar rotation - II. Rapidly rotating magnetars: implications for gamma-ray bursts and superluminous supernovae",
          "venue": "MNRAS, 526, 3141",
          "ads": "2023MNRAS.526.3141P",
          "arxiv": "2305.16412",
          "doi": "10.1093/mnras/stad2948"
        },
        {
          "year": 2023,
          "authors": "Raives, M. J., Coleman, M. S. B., & Thompson, T. A.",
          "title": "Magnetized rotating isothermal winds",
          "venue": "MNRAS, 526, 4418",
          "ads": "2023MNRAS.526.4418R",
          "arxiv": "2302.05462",
          "doi": "10.1093/mnras/stad3016"
        },
        {
          "year": 2023,
          "authors": "Vartanyan, D., Burrows, A., Wang, T., Coleman, M. S. B., & White, C. J.",
          "title": "Gravitational-wave signature of core-collapse supernovae",
          "venue": "PhRvD, 107, 103015",
          "ads": "2023PhRvD.107j3015V",
          "arxiv": "2302.07092",
          "doi": "10.1103/PhysRevD.107.103015"
        },
        {
          "year": 2022,
          "authors": "Coleman, M. S. B., & Burrows, A.",
          "title": "Kicks and induced spins of neutron stars at birth",
          "venue": "MNRAS, 517, 3938",
          "ads": "2022MNRAS.517.3938C",
          "arxiv": "2209.02711",
          "doi": "10.1093/mnras/stac2573"
        },
        {
          "year": 2022,
          "authors": "Prasanna, T., Coleman, M. S. B., Raives, M. J., & Thompson, T. A.",
          "title": "The early evolution of magnetar rotation - I. Slowly rotating 'normal' magnetars",
          "venue": "MNRAS, 517, 3008",
          "ads": "2022MNRAS.517.3008P",
          "arxiv": "2208.09042",
          "doi": "10.1093/mnras/stac2651"
        },
        {
          "year": 2022,
          "authors": "Wang, T., Vartanyan, D., Burrows, A., & Coleman, M. S. B.",
          "title": "The essential character of the neutrino mechanism of core-collapse supernova explosions",
          "venue": "MNRAS, 517, 543",
          "ads": "2022MNRAS.517..543W",
          "arxiv": "2207.02231",
          "doi": "10.1093/mnras/stac2691"
        },
        {
          "year": 2022,
          "authors": "Coleman, M. S. B., Rafikov, R. R., & Philippov, A. A.",
          "title": "Boundary layers of accretion discs: wave-driven transport and disc evolution",
          "venue": "MNRAS, 512, 2945",
          "ads": "2022MNRAS.512.2945C",
          "arxiv": "2111.03068",
          "doi": "10.1093/mnras/stac732"
        },
        {
          "year": 2022,
          "authors": "Vartanyan, D., Coleman, M. S. B., & Burrows, A.",
          "title": "The collapse and three-dimensional explosion of three-dimensional massive-star supernova progenitor models",
          "venue": "MNRAS, 510, 4689",
          "ads": "2022MNRAS.510.4689V",
          "arxiv": "2109.10920",
          "doi": "10.1093/mnras/stab3702"
        },
        {
          "year": 2022,
          "authors": "White, C. J., Burrows, A., Coleman, M. S. B., & Vartanyan, D.",
          "title": "On the Origin of Pulsar and Magnetar Magnetic Fields",
          "venue": "ApJ, 926, 111",
          "ads": "2022ApJ...926..111W",
          "arxiv": "2111.01814",
          "doi": "10.3847/1538-4357/ac4507"
        },
        {
          "year": 2022,
          "authors": "Coleman, M. S. B., Rafikov, R. R., & Philippov, A. A.",
          "title": "Boundary layers of accretion discs: Discovery of vortex-driven modes and other waves",
          "venue": "MNRAS, 509, 440",
          "ads": "2022MNRAS.509..440C",
          "arxiv": "2103.12119",
          "doi": "10.1093/mnras/stab2962"
        },
        {
          "year": 2020,
          "authors": "Coleman, M. S. B.",
          "title": "An Extension of the Athena++ Framework for General Equations of State",
          "venue": "ApJS, 248, 7",
          "ads": "2020ApJS..248....7C",
          "arxiv": "1909.05274",
          "doi": "10.3847/1538-4365/ab82ff"
        },
        {
          "year": 2019,
          "authors": "Chen, Z., Coleman, M. S. B., Blackman, E. G., & Frank, A.",
          "title": "Solving the Riemann problem for realistic astrophysical fluids",
          "venue": "JCoPh, 388, 490",
          "ads": "2019JCoPh.388..490C",
          "arxiv": "1903.04568",
          "doi": "10.1016/j.jcp.2019.03.016"
        },
        {
          "year": 2018,
          "authors": "Coleman, M. S. B., Blaes, O., Hirose, S., & Hauschildt, P. H.",
          "title": "Convection Enhances Magnetic Turbulence in AM CVn Accretion Disks",
          "venue": "ApJ, 857, 52",
          "ads": "2018ApJ...857...52C",
          "arxiv": "1803.04381",
          "doi": "10.3847/1538-4357/aab6a7"
        },
        {
          "year": 2017,
          "authors": "Coleman, M. S. B., Yerger, E., Blaes, O., Salvesen, G., & Hirose, S.",
          "title": "Convective quenching of field reversals in accretion disc dynamos",
          "venue": "MNRAS, 467, 2625",
          "ads": "2017MNRAS.467.2625C",
          "arxiv": "1701.08177",
          "doi": "10.1093/mnras/stx268"
        },
        {
          "year": 2016,
          "authors": "Coleman, M. S. B., Kotko, I., Blaes, O., Lasota, J.-P., & Hirose, S.",
          "title": "Dwarf nova outbursts with magnetorotational turbulence",
          "venue": "MNRAS, 462, 3710",
          "ads": "2016MNRAS.462.3710C",
          "arxiv": "1608.01321",
          "doi": "10.1093/mnras/stw1908"
        },
        {
          "year": 2014,
          "authors": "Hirose, S., Blaes, O., Krolik, J. H., Coleman, M. S. B., & Sano, T.",
          "title": "Convection Causes Enhanced Magnetic Turbulence in Accretion Disks in Outburst",
          "venue": "ApJ, 787, 1",
          "ads": "2014ApJ...787....1H",
          "arxiv": "1403.3096",
          "doi": "10.1088/0004-637X/787/1/1"
        },
        // pub_find:end refereed
      ]
    },
    {
      "id": "other",
      "label": "Other",
      "type": "pubs",
      "items": [
        // pub_find:begin other (written by tools/pub_find.py; edits here are overwritten)
        {
          "year": 2023,
          "authors": "Wang, T., Burrows, A., Vartanyan, D., Coleman, M., & White, C.",
          "title": "The Gravitational-Wave Signature of Core-Collapse Supernovae",
          "venue": "APS, T14.006",
          "ads": "2023APS..APRT14006W"
        },
        {
          "year": 2022,
          "authors": "Burrows, A., & Coleman, M.",
          "title": "The Character of Three-Dimensional Core-Collapse Simulation Results",
          "venue": "EPJWC, 260, 07001",
          "ads": "2022EPJWC.26007001B",
          "doi": "10.1051/epjconf/202226007001"
        },
        {
          "year": 2017,
          "authors": "Coleman, M. S. B.",
          "title": "Convection Affects Magnetic Turbulence in White Dwarf Accretion Disks",
          "venue": "PhD thesis, University of California, Santa Barbara",
          "ads": "2017PhDT........73C"
        },
        // pub_find:end other
      ]
    }
  ]
};
