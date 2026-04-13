# HITL Long-Tail Eval

This repository is a synthetic human-in-the-loop (HITL) simulation for thinking about acceptance-rate telemetry, long-tail behavior, user variability, and proxy-metric reliability.

The project now has two layers:

- notebooks for the narrative walkthroughs
- a reusable Python package in `src/hitl_telemetry_sim` for simulation, plotting, and CatBoost-based AUC experiments

## Why This Exists

The central idea is simple: observed acceptance is not the same thing as true model quality.

In these simulations, observed acceptance depends on:

- whether the system output is actually correct
- whether the human accepts correct outputs
- whether the human accepts incorrect outputs
- how requests are routed through system components
- how users and request types are mixed over time

That means a better acceptance rate can come from multiple causes, not all of which reflect better system quality.

## Repository Structure

```text
.
├── .devcontainer/
│   ├── Dockerfile
│   ├── devcontainer.json
│   └── requirements.txt
├── notebooks/
│   ├── 00_simulation_example.ipynb
│   ├── 01_baseline_case.ipynb
│   ├── 02_introducing_human_ambiguity.ipynb
│   ├── 03_introducing_ambiguous_requests.ipynb
│   └── images/
├── src/
│   └── hitl_telemetry_sim/
│       ├── __init__.py
│       ├── simulation.py
│       ├── plotting.py
│       └── catboost.py
├── pyproject.toml
└── README.md
```

## Current Notebook Set

- `notebooks/00_simulation_example.ipynb`
  - quick package-first example
- `notebooks/01_baseline_case.ipynb`
  - baseline case with ideal humans and clean request assumptions
- `notebooks/02_introducing_human_ambiguity.ipynb`
  - introduces imperfect human review behavior
- `notebooks/03_introducing_ambiguous_requests.ipynb`
  - introduces ambiguous or mixed request validity

## Python Package

The reusable package lives in `src/hitl_telemetry_sim`.

Public imports:

```python
from hitl_telemetry_sim import (
    hitl_system_simulation,
    plot_daily_acceptance,
    plot_acceptance_rate_by_request_type,
    plot_acceptance_rate_by_user,
    run_catboost_auc_slice,
)
```

What each piece does:

- `hitl_system_simulation`
  - creates the simulation object, users, and components
- `sim.run_simulation(...)`
  - runs the simulation and stores telemetry on `sim.telemetry`
- `plot_daily_acceptance(...)`
  - daily acceptance plot
- `plot_acceptance_rate_by_request_type(...)`
  - rolling acceptance plot by request type
- `plot_acceptance_rate_by_user(...)`
  - rolling acceptance plot by user
- `run_catboost_auc_slice(...)`
  - repeated CatBoost AUC experiments for a telemetry slice and selected feature columns

## Fastest Way To Run This Repo

The recommended path is Docker via the VS Code dev container. It is the quickest way to get a working notebook environment with the correct Python, Jupyter kernel, package install, and editor extensions.

### Option 1: VS Code Dev Container

Prerequisites:

- Git
- Docker Desktop
- VS Code
- VS Code Dev Containers / Containers support

Steps:

1. Clone the repo:

```bash
git clone git@github.com:fernandes-alexandreg/hitl-telemetry-sim.git
cd hitl-telemetry-sim
```

2. Open the folder in VS Code.

3. Reopen the folder in the container.

Useful command from the VS Code command palette:

```text
Dev Containers: Reopen in Container
```

4. Wait for the image build to finish.

The dev container:

- installs the Python dependencies from `.devcontainer/requirements.txt`
- runs `pip install -e .`
- installs a `python3` Jupyter kernel
- preinstalls the VS Code Python and Jupyter extensions

5. Open one of the notebooks in `notebooks/` and run cells.

If you want a clean starting point, begin with:

- `notebooks/00_simulation_example.ipynb`
- then `notebooks/01_baseline_case.ipynb`

## Plain Docker Workflow

If you do not want to use VS Code, you can still run the repo with Docker directly.

### Build The Image

From the repo root:

```bash
docker build -f .devcontainer/Dockerfile -t hitl-telemetry-sim .
```

### Start Jupyter With The Repo Mounted

On macOS or Linux:

```bash
docker run --rm -it \
  -p 8888:8888 \
  -v "$PWD":/workspace \
  -w /workspace \
  hitl-telemetry-sim \
  bash -lc "pip install -e . && jupyter notebook --ip 0.0.0.0 --port 8888 --no-browser --allow-root"
```

On PowerShell:

```powershell
docker run --rm -it `
  -p 8888:8888 `
  -v ${PWD}:/workspace `
  -w /workspace `
  hitl-telemetry-sim `
  bash -lc "pip install -e . && jupyter notebook --ip 0.0.0.0 --port 8888 --no-browser --allow-root"
```

Then open the Jupyter URL shown in the container logs in your browser.

Why the bind mount matters:

- the Docker image includes the package and dependencies
- your notebooks live in the repo workspace
- mounting the repo into `/workspace` makes the notebooks visible inside the container

## Minimal Python Usage

You can also use the package outside notebooks once your environment is installed:

```python
from hitl_telemetry_sim import (
    hitl_system_simulation,
    plot_daily_acceptance,
    run_catboost_auc_slice,
)

sim = hitl_system_simulation(seed=7)

sim.run_simulation(
    n_items_per_day=1000,
    simulation_duration=455,
    sprint_every_days=7,
    sprint_stop_day=425,
    components_per_sprint=1,
    improvement_rate=0.4,
    min_path_length=2,
)

fig = plot_daily_acceptance(sim.telemetry)

results = run_catboost_auc_slice(
    telemetry_df=sim.telemetry,
    date_slice=(425, 455),
    feature_columns=["request_type"],
)

print(results["mean_auc"], results["std_auc"])
```

## Simulation Defaults

The current package defaults are intentionally simple:

- `n_components=6`
- `n_users=100`
- component success initialized in `(0.5, 0.8)`
- humans are perfect by default:
  - accept correct in `(1.0, 1.0)`
  - accept incorrect in `(0.0, 0.0)`
- request validity parameter `pr=1.0`
- simulation defaults:
  - `simulation_duration=455`
  - `sprint_every_days=7`
  - `sprint_stop_day=425`
  - `components_per_sprint=1`
  - `improvement_rate=0.4`
  - `min_path_length=2`

Telemetry is stored in two forms:

- `sim.raw_telemetry`
  - event-level raw records including `featuresDict`
- `sim.telemetry`
  - cleaned telemetry with expanded component columns and pseudo `request_type`

## Main Dependencies

The environment is built around:

- `numpy`
- `pandas`
- `plotly`
- `scikit-learn`
- `catboost`
- `jupyter`
- `notebook`
- `ipykernel`

## Notes And Limits

- CatBoost GPU is not a practical path on macOS in this repo; the documented workflow is CPU-first.
- The package is installed editable with `pip install -e .`, so source changes are reflected directly in the container environment.
- `notebooks/catboost_info/` is treated as generated CatBoost output rather than source code.

## Suggested Entry Order

If you are new to the repo:

1. Start with `notebooks/00_simulation_example.ipynb`
2. Read `notebooks/01_baseline_case.ipynb`
3. Move to `notebooks/02_introducing_human_ambiguity.ipynb`
4. Finish with `notebooks/03_introducing_ambiguous_requests.ipynb`

If you want to work directly from code instead of notebook cells, start in `src/hitl_telemetry_sim`.
