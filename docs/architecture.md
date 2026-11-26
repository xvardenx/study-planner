# Architecture and file structure

[README](../README.md#documentation-and-requirement-coverage) ·
[Project and bug status](project-status.md) ·
[Bayesian model](bayesian-model.md) · [Decision model](decision-model.md)

The original plan requires a Bayesian model, utility-based action selection,
calendar integration, and contrasting student demonstrations. The repository
implements the first two and an offline scheduling pipeline. Calendar API
integration is still outstanding.

## Feature-to-file map

Paths below are relative to the repository root. Links lead to the implementation
or evidence for each feature rather than listing generated caches or environments.

| Location | Responsibility and connection to the original plan |
| --- | --- |
| [`src/study_planner/inference/network.py`](../src/study_planner/inference/network.py) | Defines the ten-variable, three-concept network and handcrafted CPTs |
| [`src/study_planner/inference/engine.py`](../src/study_planner/inference/engine.py) | Validates evidence, buckets days remaining, and queries exam success with variable elimination |
| [`src/study_planner/planning/decision.py`](../src/study_planner/planning/decision.py) | Allocates hours, models assumed action effects, evaluates six actions, and selects by utility with stress/capacity constraints |
| [`src/study_planner/calendar/schedule.py`](../src/study_planner/calendar/schedule.py) | Calculates days to exam and free capacity, then places concept-specific one-hour sessions around busy blocks; this is an offline scheduler, not a calendar API adapter |
| [`src/study_planner/scenarios.py`](../src/study_planner/scenarios.py) | Loads student examples, validates comprehensive daily observations, and exposes scenario evaluation |
| [`src/study_planner/pipeline.py`](../src/study_planner/pipeline.py) | Coordinates daily evidence, feasible decisions, and scheduling into `DailyPlan` results |
| [`src/study_planner/cli.py`](../src/study_planner/cli.py) | Implements `all`, `run`, and `run-comp` and renders evidence, action comparisons, recommendations, and sessions |
| [`scenarios/`](../scenarios/) | Four single-day JSON examples for advanced, mixed, stressed, and struggling students |
| [`scenarios/comprehensive/`](../scenarios/comprehensive/) | Dated replay fixture with exam date, daily observations, study windows, and busy blocks |
| [`tests/unit/`](../tests/unit/) | Checks network/CPT behavior, expected utility and selection, scheduling, scenario validation, and pipeline consistency |
| [`tests/test_scenario_cli.py`](../tests/test_scenario_cli.py) | Verifies contrasting example recommendations and CLI/replay output, including rest days and invalid input |
| [`tests/test_environment.py`](../tests/test_environment.py) | Checks runtime dependency imports; this does not test external calendar connectivity |
| [`docs/`](./) and [`README.md`](../README.md) | Explain the model, decisions, status, and feature mapping; README supplies setup and demonstration commands |
| [`pyproject.toml`](../pyproject.toml) and [`uv.lock`](../uv.lock) | Declare Python/runtime/development requirements, CLI entry point, tool configuration, and locked dependencies |
| [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) and [`AGENTS.md`](../AGENTS.md) | Define automated checks and contributor rules, including credential handling |

Package `__init__.py` files provide package entry points and exports; the feature
logic lives in the modules listed above.

## Data flow

```text
Scenario JSON → validation → daily evidence + calendar snapshot
                                 │                  │
                                 │             free capacity
                                 ▼                  │
                    baseline inference              │
                    + projected action outcomes     │
                                 │                  │
                    repeated BN success queries     │
                                 ▼                  ▼
                    expected utility → feasible recommendation
                                              │
                                  concept-hour allocation
                                              ▼
                              offline session placement → CLI output
```

Single-day `all` and `run` commands evaluate evidence without a calendar capacity
or session placement. `run-comp` loads every pre-exam day's observations, computes
exact days remaining and capacity, then evaluates actions with that capacity.
The same calendar snapshot is used to place the recommended allocation. A
placement shortfall raises a pipeline consistency error.

The [Bayesian specification](bayesian-model.md#inference-task) explains the success
query. The [decision model](decision-model.md#expected-utility) explains how
projected outcomes feed utility and how constraints affect selection. The
[replay specification](decision-model.md#comprehensive-scenario-replay) defines
input validation, session placement, and break preferences.

Each replay day uses independently supplied mastery and stress observations.
Scheduled sessions do not generate the next day's evidence. No component in
this flow authenticates with Google Calendar or reads/writes external events;
see [remaining deliverables](project-status.md#remaining-deliverables).
