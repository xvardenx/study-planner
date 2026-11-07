# One-day study decisions

The decision layer compares five actions for **today**. It returns a total
number of study hours and their allocation among three concepts. The hours are
not calendar events or continuous blocks; a later scheduling component can
split them into sessions. This step does not plan future days.

| Action | Total hours |
| --- | ---: |
| `rest` | 0 |
| `light_review` | 1 |
| `standard_study` | 2 |
| `focused_study` | 3 |
| `intensive_study` | 5 |

## Assumed action effects

Hours are allocated one at a time among concepts below high mastery, starting
with the lowest mastery. Ties favor the harder concept, then its lower concept
number. The order repeats for additional hours. With three eligible concepts,
the five-hour action allocates 2, 2, and 1 hours. If all concepts are already
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
             − 0.3 × h if the exam is urgent (1–2 days away)
```

The first term values exam success; the second values lower stress even beyond
its effect on exam success. The quadratic term represents the burden of longer
study commitments, and the final term discourages last-minute cramming.
These weights are illustrative preferences and are not fitted to student data.
The highest-utility action wins; exact ties favor fewer hours.

`study_planner.planning.evaluate_daily_actions(difficulties, masteries, stress,
days_remaining)` returns a `DailyDecision` with the baseline success chance,
all five action evaluations, and the recommendation. Each evaluation contains
the action, its total hours, its three concept-hour allocations, expected exam
success chance, expected stress index, and expected utility. Inputs use the
same state labels and validation as the existing inference API.
