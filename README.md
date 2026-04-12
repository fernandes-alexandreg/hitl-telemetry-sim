# HITL Long-Tail Eval

This project is a small synthetic simulation of human-in-the-loop (HITL) evaluation. The goal is to show how an observed product metric such as human acceptance rate can diverge from true system quality, especially when performance varies across users and long-tail failure modes are present.

The repository currently contains a series of notebooks that progressively build up the simulation setup, from a minimal single-system example to more composite and ambiguity-aware scenarios.

## Core Idea

The notebooks separate:

- System quality: how often the model is actually correct.
- Human behavior: how often a user accepts correct or incorrect outputs.
- Observed telemetry: the acceptance events you would see in production.

This matters because acceptance is only a proxy. A higher acceptance rate can reflect a better model, but it can also reflect user leniency, user mix shifts, routing effects, or a failure to catch incorrect outputs.

## Formulation

The basic setup models each user with a 2x2 human-response matrix:

```text
H = [
  [p_ac,       p_ai      ],
  [1 - p_ac,   1 - p_ai  ]
]
```

Where:

- `p_ac` is the probability that a user accepts a correct output.
- `p_ai` is the probability that a user accepts an incorrect output.

The system is modeled as a state vector:

```text
p_s = [
  [p_s,c      ],
  [1 - p_s,c  ]
]
```

Where:

- `p_s,c` is the probability that the system output is correct.

Multiplying the human matrix by the system state gives observed outcomes:

```text
H @ p_s
```

The top entry is the observed acceptance probability:

```text
P(accept) = p_ac * p_s,c + p_ai * (1 - p_s,c)
```

That equation is the main point of the project. The observed rate is a blend of true correctness and human response behavior, so it is not a clean measure of model quality on its own.

## Notebooks

The current notebook set is:

- [notebooks/01_minimal_hitl_simulation.ipynb](notebooks/01_minimal_hitl_simulation.ipynb): minimal HITL simulation and proxy-metric framing
- [notebooks/02_composite_system_hitl_sim.ipynb](notebooks/02_composite_system_hitl_sim.ipynb): composite system simulation with request-type slices
- [notebooks/02b_composite_system_hitl_sim.ipynb](notebooks/02b_composite_system_hitl_sim.ipynb): a follow-on composite-system variant
- [notebooks/03_composite_human_ambiguity_hitl_sim.ipynb](notebooks/03_composite_human_ambiguity_hitl_sim.ipynb): composite human ambiguity scenario

The first notebook is the cleanest entry point if you are new to the repo.

## What The Simulations Show

Across the notebook series, the project explores questions like:

- When does acceptance rate track true quality well?
- When does user variability mask quality changes?
- How much can a proxy metric improve even if long-tail failures remain?
- How much of the observed noise comes from user heterogeneity versus sparse per-user samples?
- How do routing choices, request types, and composite systems affect observed telemetry?

The structure is deliberately simple enough to extend with richer assumptions, including:

- segment-specific user populations
- rare catastrophic failure modes
- changing user mix over time
- selective review policies
- disagreement between proxy metrics and ground-truth evaluation

## Running The Notebooks

This repository includes a dev container configured for notebook work. After opening the repo in the container, open any notebook in the `notebooks/` directory and run the cells from top to bottom.

The container installs:

- `jupyter`
- `notebook`
- `pandas`
- `numpy`
- `scikit-learn`
- `plotly`
- `ipykernel`
- `catboost`

The VS Code Python and Jupyter extensions are also configured in the dev container, so the notebooks should be executable immediately after the container rebuilds.

## Repository Layout

```text
.
├── .devcontainer/
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── requirements.txt
├── notebooks/
│   ├── 01_minimal_hitl_simulation.ipynb
│   ├── 02_composite_system_hitl_sim.ipynb
│   ├── 02b_composite_system_hitl_sim.ipynb
│   └── 03_composite_human_ambiguity_hitl_sim.ipynb
└── README.md
```

## Summary

The notebooks demonstrate a simple but important idea: in HITL systems, observed acceptance is a joint product of model quality and human behavior. If you want to reason about long-tail risk or proxy-metric reliability, you need to model both.
