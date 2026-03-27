<<<<<<< HEAD
# HITL Long-Tail Eval

This project is a small synthetic simulation of human-in-the-loop (HITL) evaluation. The goal is to show how an observed product metric such as human acceptance rate can diverge from true system quality, especially when performance varies across users and long-tail failure modes are present.

The current implementation lives in [notebooks/01_minimal_hitl_simulation.ipynb](notebooks/01_minimal_hitl_simulation.ipynb). The notebook is structured as a short walkthrough: it introduces the formulation, shows a single-user example, builds a heterogeneous user population, simulates daily telemetry over time, and then compares hidden true quality against the observed acceptance metric.

## Core Idea

The notebook separates:

- System quality: how often the model is actually correct.
- Human behavior: how often a user accepts correct or incorrect outputs.
- Observed telemetry: the acceptance events you would see in production.

This matters because acceptance is only a proxy. A higher acceptance rate can reflect a better model, but it can also reflect user leniency, user mix shifts, or a failure to catch incorrect outputs.

## Formulation

The notebook models each user with a 2x2 human-response matrix:

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

## What The Notebook Does

The notebook currently walks through five stages:

1. A simple sanity check with a near-perfect human evaluator.
2. A simulated user ensemble of 100 users, each with different `p_ac` and `p_ai`.
3. A year-plus simulation of daily traffic with a system-quality curve that improves over time.
4. A comparison of hidden true system quality vs observed acceptance rate.
5. A user-level scatter plot showing how reviewer heterogeneity and low per-user daily sample sizes create noisy telemetry.

The generated telemetry includes:

- `Date`: simulation day
- `User`: sampled user id
- `isAccepted`: whether the output was accepted
- `hiddenSystemState`: the true system correctness rate used by the simulator
- `acceptProbability`: the per-request acceptance probability after combining system quality and user behavior

The notebook then produces two main views with Plotly:

- a line chart comparing hidden true system quality against observed acceptance
- a scatter plot of daily acceptance rate by user

## Simulation Assumptions

The current defaults in the notebook are:

- `n_users = 100`
- `n_items_per_day = 1000`
- `simulation_duration = 455` days
- `p_ac ~ Uniform(0.8, 1.0)`
- `p_ai ~ Uniform(0.0, 0.2)`
- `seed = 7` for reproducibility

System quality evolves according to a hand-crafted function:

```text
log(x / 365 + 1) + 0.3 + (x / 365) * exp(-((2x / 365)^2))
```

and is capped at `1.0`.

This is not meant to be a realistic production model. It is a compact toy environment for thinking about metric interpretation under reviewer heterogeneity.

## Why This Is Useful

This notebook is a good starting point for exploring questions like:

- When does acceptance rate track true quality well?
- When does user variability mask quality changes?
- How much can a proxy metric improve even if long-tail failures remain?
- How sensitive are conclusions to the mix of strict and lenient reviewers?
- How much of the observed noise comes from user heterogeneity versus sparse per-user samples?

The structure is deliberately simple enough to extend with richer assumptions, including:

- segment-specific user populations
- rare catastrophic failure modes
- changing user mix over time
- selective review policies
- disagreement between proxy metrics and ground-truth evaluation

## Running The Notebook

This repository includes a dev container configured for notebook work. After opening the repo in the container, open [notebooks/01_minimal_hitl_simulation.ipynb](notebooks/01_minimal_hitl_simulation.ipynb) and run the cells from top to bottom.

The container installs:

- `jupyter`
- `notebook`
- `pandas`
- `numpy`
- `scikit-learn`
- `plotly`
- `ipykernel`

The VS Code Python and Jupyter extensions are also configured in the dev container, so the notebook should be executable immediately after the container rebuilds.

## Current Status

Right now the repo is best understood as an exploratory research notebook rather than a packaged library. The next natural steps would be:

- move the simulation code into reusable Python modules
- parameterize the scenario setup
- add summary plots for true quality vs observed acceptance
- introduce explicit long-tail slices and rare-event analysis
- compare proxy metrics against a hidden ground-truth metric

## Repository Layout

```text
.
├── .devcontainer/
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── requirements.txt
├── notebooks/
│   └── 01_minimal_hitl_simulation.ipynb
└── README.md
```

## Summary

The notebook demonstrates a simple but important idea: in HITL systems, observed acceptance is a joint product of model quality and human behavior. If you want to reason about long-tail risk or proxy-metric reliability, you need to model both.
=======
# hitl-telemetry-sim
Simulation of human-in-the-loop system telemetry showing why acceptance rate is a proxy metric, not a direct measure of model quality.
>>>>>>> origin/main
