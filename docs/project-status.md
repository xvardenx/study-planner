# Project and bug status

[README](../README.md#documentation-and-requirement-coverage) ·
[Architecture and file structure](architecture.md)

Last verified: 2026-11-26. This report describes the repository's current
implementation against the [original requirements](../README.md#requirements).
The project is an offline prototype; the full calendar API deliverable is incomplete.

## Requirement status

| Original requirement | Status | Explanation and implementation evidence |
| --- | --- | --- |
| Model difficulty of at least three concepts with roughly ten variables | Implemented | [Bayesian specification](bayesian-model.md); [network](../src/study_planner/inference/network.py); [BN tests](../tests/unit/test_bayesian_network.py) |
| Handcraft variables and CPTs and explain parameters | Implemented and documented | [States and evidence](bayesian-model.md#state-definitions-and-evidence), [CPT formulas](bayesian-model.md#handcrafted-cpts), and [network](../src/study_planner/inference/network.py) |
| Identify the inference query and use a built-in algorithm | Implemented | [Inference task](bayesian-model.md#inference-task); [engine](../src/study_planner/inference/engine.py) uses pgmpy variable elimination to query exam success |
| Define at least three actions | Implemented | [Six actions](decision-model.md); [decision layer](../src/study_planner/planning/decision.py) |
| Define utility balancing exam success and stress using query results | Implemented | [Expected utility](decision-model.md#expected-utility); [decision tests](../tests/unit/test_decision.py) |
| Compute each action's expected utility and choose the best action | Implemented with constraints | All six actions are scored; selection maximizes utility subject to the documented stress limit and optional calendar capacity, with ties favoring fewer hours; [decision layer](../src/study_planner/planning/decision.py) |
| Incorporate the chosen action into a calendar API | Incomplete | [Offline scheduler](../src/study_planner/calendar/schedule.py) places sessions using supplied busy blocks; there is no API client or event read/write flow |
| Demonstrate different student scenarios and adaptive actions | Implemented offline | [Verified examples](#verified-example-results); [CLI integration tests](../tests/test_scenario_cli.py); [decision tests](../tests/unit/test_decision.py) also isolate difficulty changes |
| Dynamically schedule using current mastery and exam dates | Implemented offline | [Replay](decision-model.md#comprehensive-scenario-replay) recalculates each day from supplied observations; [pipeline](../src/study_planner/pipeline.py) and [tests](../tests/unit/test_pipeline.py) |
| Provide requested documentation, project/bug status, and feature-to-file explanation | Documented | [README documentation index](../README.md#documentation-and-requirement-coverage), this report, and [architecture](architecture.md) |

## Verified example results

The following commands completed successfully on 2026-11-26:

| Command | Observed behavior |
| --- | --- |
| `uv run study-planner all` | `advanced`: rest (0 hours); `mixed`: extended study (4 hours); `stressed`: focused study (3 hours); `struggling`: extended study (4 hours) |
| `uv run study-planner run mixed` | Displays only the mixed scenario, its baseline success probability, all six action scores, and a four-hour recommendation |
| `uv run study-planner run-comp progressing` | Replays November 16–21, 2026, before the November 22 exam; recommended and scheduled hours are 2, 3, 3, 3, 3, 2 |

The advanced and struggling examples establish contrasting student behavior;
they differ in more than concept difficulty. The decision unit tests separately
check that changing difficulty while holding other evidence fixed can change the
recommended action. The mixed/stressed pair holds other evidence fixed to
demonstrate a stress-dependent recommendation.

The replay's first day has two hours of capacity and receives two sessions.
Later days display session times and concept assignments. Changes in supplied
mastery must not be interpreted as measured learning caused by these sessions.

## Known bugs and limitations

No confirmed bugs documented as of the verification date. This is not a claim
that the software is bug-free. Record newly confirmed bugs here with reproduction
steps, affected behavior, and resolution status.

- Calendar API integration is a missing feature. Google client dependencies in
  `pyproject.toml` do not mean authentication or event operations are implemented.
- CPTs, action effects, and utility weights are handcrafted assumptions, not
  fitted or empirically validated predictions of student outcomes.
- The ten-variable network is a repeated static model for three concepts and one
  exam. It does not learn or link student states across days.
- Replay uses supplied daily mastery, stress, study windows, and busy blocks.
  It does not simulate later evidence from previously scheduled sessions.
- Replay uses local same-day times and one-hour sessions, excludes exam day,
  and does not perform timezone conversion or optimize a multi-day policy.
- A stress-based limit can exclude the action with the highest raw utility.
  This constraint is part of the [selection policy](decision-model.md#expected-utility).

## Remaining deliverables

1. Implement calendar API authentication, read actual availability, and write
   selected study sessions as calendar events. Keep credentials outside tracked
   files, following [repository rules](../AGENTS.md).
2. Demonstrate the full inference → decision → calendar API flow with contrasting
   concept difficulties and resulting actions; the current examples demonstrate
   only the offline flow.
3. Add integration verification for that API flow and update this status report,
   the README summary, and architecture documentation when it is delivered.

Documentation is organized around linked repository documents so the README
remains concise. The supplied deliverable does not explicitly specify whether
all explanatory text must appear inline; this organization assumes reviewers
can follow repository links.

## Verification

On 2026-11-26, the test suite passed all 77 tests. The three example commands
listed above also completed successfully. These checks cover the offline model,
decisions, scheduling, validation, and CLI; they do not exercise a calendar API.

Run the [README checks](../README.md#setup-and-verification) and example commands
when updating this report. Record their date and actual outcome; passing offline
tests does not establish calendar API completion.
