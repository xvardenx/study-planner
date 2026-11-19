# One-day study decisions

The decision layer compares six actions for **today**. It returns a total
number of study hours and their allocation among three concepts. The hours are
not calendar events or continuous blocks; a later scheduling component can
split them into sessions. This step does not plan future days.

| Action | Total hours |
| --- | ---: |
| `rest` | 0 |
| `light_review` | 1 |
| `standard_study` | 2 |
| `focused_study` | 3 |
| `extended_study` | 4 |
| `intensive_study` | 5 |

## Assumed action effects

Hours are allocated one at a time among concepts below high mastery, starting
with the lowest mastery. Ties favor the harder concept, then its lower concept
number. The order repeats for additional hours. With three eligible concepts,
the four-hour action allocates 2, 1, and 1 hours, and the five-hour action
allocates 2, 2, and 1 hours. If all concepts are already
high, the hours are allocated as review time, ordered by difficulty.

Each concept can advance at most one mastery level from one day's action. The
handcrafted chance of advancing depends on the number of hours allocated to
that concept:

| Hours on concept | 0 | 1 | 2 | 3 | 4 | 5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Chance of one-level gain | 0% | 45% | 75% | 85% | 92% | 96% |

Already-high mastery stays high. Gains for different concepts are assumed
independent. Stress can change by one level, with no change otherwise:

| Action | Change | Chance |
| --- | --- | ---: |
| Rest | Down | 15% |
| Light review | Up | 0% |
| Standard study | Up | 5% |
| Focused study | Up | 10% |
| Extended study | Up | 17.5% |
| Intensive study | Up | 25% |

Stress stays within low, medium, and high. These probabilities are planning
assumptions, not effects learned by the Bayesian network. In particular,
re-querying the network with projected evidence does not establish that the
action *causes* the projected change.

## Expected utility

For every possible post-action mastery and stress state, the decision layer
queries the existing `P(ExamSuccess=success | concepts, stress, days)` model.
It weights each result by that state's assumed probability. Let `h` be the
action's total hours, and encode stress as low=0, medium=1, high=2. The
handcrafted utility, in points, is:

```text
EU(action) = 100 × E[P(success | projected evidence)]
             − 5 × E[stress index]
             − 0.15 × h²
             − 0.03 × starting stress index × h²
             − 0.3 × h if the exam is urgent (1–2 days away)
```

The first term values exam success; the second values lower stress even beyond
its effect on exam success. The quadratic term represents the burden of longer
study commitments. The starting-stress term adds fatigue from studying while
already stressed, including at the highest stress state where stress cannot
increase further. The final term discourages last-minute cramming. These
weights are illustrative preferences and are not fitted to student data.

To ensure that otherwise identical students are never assigned more hours as
starting stress rises, the low-stress recommendation sets the maximum hours
for medium stress, and the medium-stress recommendation sets the maximum for
high stress. All six actions are scored, but the recommendation maximizes
utility only among actions within this limit and any supplied calendar capacity.
The same calendar capacity applies at every stress level used to derive the
stress limit; exact ties favor fewer hours.

`study_planner.planning.evaluate_daily_actions(difficulties, masteries, stress,
days_remaining, *, available_study_hours=None)` returns a `DailyDecision` with
the baseline success chance,
all six action evaluations, the recommendation, and any stress-based study
hour limit. Each evaluation contains
the action, its total hours, its three concept-hour allocations, expected exam
success chance, expected stress index, and expected utility. Inputs use the
same state labels and validation as the existing inference API.

## Comprehensive scenario replay

Run `uv run study-planner run-comp progressing` for daily inference, action
selection, and assigned sessions through the day before the exam. `pipeline.py`
coordinates these steps and returns `DailyPlan` results; `scenarios.py` loads
and validates observations, while the CLI renders the results without repeating
inference. No calendar events are written.

Comprehensive JSON files in `scenarios/comprehensive/` contain `start_date`,
`exam_date`, three `concept_difficulties`, and a `days` list. Each record has:

```json
{
  "date": "2026-11-16",
  "concept_masteries": ["low", "low", "low"],
  "stress": "medium",
  "study_window": {"start": "09:00", "end": "18:00"},
  "busy_blocks": [{"start": "12:00", "end": "14:00"}]
}
```

Use ISO dates and local `HH:MM` times within the same date. Provide exactly one
record for every day from the start date through the day before the exam;
records are sorted by date. Evidence and calendar fields are validated before
inference starts. Invalid records identify the relevant field and date where
available. Exam day is excluded because inference requires positive days remaining.
Timezone conversion and Google Calendar integration are outside this offline replay.

Mastery and stress are supplied observations for each date. They are not
simulated from previous sessions, and improvements must not be attributed to
the scheduled hours. The runner calculates days remaining from actual dates.

Capacity counts whole one-hour sessions in each free gap after clipping and
merging busy intervals. Disconnected sub-hour gaps do not combine into an hour.
Selection respects both capacity and the stress limit while retaining all six
action scores. Available time is a maximum, not a requirement to fill the day.
Omitting `available_study_hours` preserves unconstrained calendar behavior.

The scheduler interleaves concepts in the decision layer's priority order,
favors 30-minute breaks, and reduces breaks before sacrificing study hours.
The full recommended allocation must fit the calendar snapshot used for
selection; a shortfall raises a pipeline consistency error. The CLI shows each
date's evidence, action comparison, capacity, recommended and scheduled hours,
and session start/end times with concept numbers. Rest days explicitly report
that no sessions are assigned.

The progressing example restricts the first day to two available hours, which
changes its recommendation relative to a decision without a calendar limit.
