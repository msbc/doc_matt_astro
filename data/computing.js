/* =====================================================================
   computing.js — the text for computing.html.

   This is a JavaScript file laid out like JSON: keep the "quotes", and put
   a comma between items. (Unlike strict JSON, comments like this one and a
   trailing comma after the last item are allowed.) See README.md for every
   field.
   ===================================================================== */
window.PAGE = {
  "title": "Computing",
  "kicker": "Sector 04 · Engineering",
  "intro": "Making research software run faster, scale further, and use the hardware it's given.",
  "image": "rotate",
  "sections": [
    {
      "id": "role",
      "label": "Performance Tuning Analyst",
      "type": "text",
      "paragraphs": [
        "Placeholder — describe your current role here. As a Performance Tuning Analyst at *Your institution*, I work with researchers to profile their codes, find the bottlenecks, and make them faster on our clusters.",
        "Typical work: profiling CPU and GPU codes, improving parallel scaling, porting to accelerators, and teaching good performance habits."
      ]
    },
    {
      "id": "at-a-glance",
      "label": "At a Glance",
      "type": "stats",
      "intro": "Placeholder readouts — swap in real numbers.",
      "items": [
        {
          "label": "Codes tuned",
          "value": "00+",
          "note": "Research groups helped"
        },
        {
          "label": "Typical speedup",
          "value": "0×–0×"
        },
        {
          "label": "Core-hours saved",
          "value": "0.0 M",
          "note": "Per year, estimated"
        },
        {
          "label": "Workshops taught",
          "value": "00"
        }
      ]
    },
    {
      "id": "what-i-do",
      "label": "What I Do",
      "type": "cards",
      "items": [
        {
          "meta": "Diagnose",
          "title": "Profiling & analysis",
          "text": "Placeholder: find where time and memory actually go, on CPUs and GPUs."
        },
        {
          "meta": "Scale",
          "title": "Parallel scaling",
          "text": "Placeholder: MPI and threading fixes so codes use more of the machine efficiently."
        },
        {
          "meta": "Accelerate",
          "title": "GPU porting",
          "text": "Placeholder: moving hot loops to accelerators and keeping them fed."
        },
        {
          "meta": "Teach",
          "title": "Consulting & training",
          "text": "Placeholder: one-on-one consultations, office hours, and workshops."
        }
      ]
    },
    {
      "id": "systems",
      "label": "Systems",
      "type": "cards",
      "intro": "The machines I work on. Placeholder — one card per cluster.",
      "items": [
        {
          "meta": "CPU cluster",
          "title": "Cluster name",
          "text": "Placeholder: nodes, cores per node, interconnect.",
          "tags": [
            "Slurm",
            "InfiniBand"
          ]
        },
        {
          "meta": "GPU cluster",
          "title": "Cluster name",
          "text": "Placeholder: GPU model and count.",
          "tags": [
            "CUDA",
            "NVLink"
          ]
        }
      ]
    },
    {
      "id": "toolkit",
      "label": "Toolkit",
      "type": "cards",
      "items": [
        {
          "title": "Languages",
          "tags": [
            "C",
            "C++",
            "Fortran",
            "Python"
          ]
        },
        {
          "title": "Parallel models",
          "tags": [
            "MPI",
            "OpenMP",
            "CUDA",
            "HIP"
          ]
        },
        {
          "title": "Profilers",
          "tags": [
            "Nsight",
            "VTune",
            "perf",
            "HPCToolkit"
          ]
        },
        {
          "title": "Libraries",
          "tags": [
            "BLAS/LAPACK",
            "FFTW",
            "HDF5",
            "PETSc"
          ]
        }
      ]
    },
    {
      "id": "case-studies",
      "label": "Case Studies",
      "type": "cards",
      "intro": "Example numbers — replace with real (shareable) results.",
      "items": [
        {
          "meta": "Hydro code · GPU port",
          "title": "Placeholder case study",
          "before": "38 h",
          "after": "9 h",
          "gain": "4.2×",
          "text": "Placeholder: what was slow, what you changed, and why it worked."
        },
        {
          "meta": "MPI scaling",
          "title": "Another case study",
          "before": "64 nodes",
          "after": "512 nodes",
          "gain": "8× scale",
          "text": "Placeholder: e.g. fixing a communication bottleneck to unlock strong scaling."
        }
      ]
    },
    {
      "id": "training",
      "label": "Training & Talks",
      "type": "timeline",
      "items": [
        {
          "when": "Year",
          "title": "Placeholder workshop or talk",
          "where": "Venue",
          "text": "Placeholder: one line on what it covered."
        }
      ]
    },
    {
      "id": "open-source",
      "label": "Open Source",
      "type": "cards",
      "items": [
        {
          "meta": "Repository",
          "title": "Project name",
          "href": "https://github.com/msbc",
          "text": "Placeholder: a tool, patch, or contribution worth showing."
        }
      ]
    }
  ]
};
