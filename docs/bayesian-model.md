# Bayesian network specification

The course model has ten variables. It represents three concepts for one exam.
Each call estimates exam success from the student's current evidence. The
planning loop will call the same network again on later days with updated
mastery, stress, and time evidence. This is a repeated static BN, not a
time-linked dynamic BN.

| Variables | States | Parents | Meaning |
| --- | --- | --- | --- |
| `Difficulty1`–`Difficulty3` | easy, medium, hard | none | Difficulty of each concept |
| `Mastery1`–`Mastery3` | low, medium, high | none | Current mastery of each concept |
| `Readiness` | low, medium, high | all six concept variables | Uncertain overall preparation |
| `Stress` | low, medium, high | none | Current stress |
| `DaysToExam` | urgent, near, distant | none | Calendar time until the exam |
| `ExamSuccess` | failure, success | Readiness, Stress, DaysToExam | Exam outcome |

The parent relationships are:

```text
Difficulty1–3 ─┐
               ├──> Readiness ──┐
Mastery1–3 ────┘                 ├──> ExamSuccess
Stress ──────────────────────────┤
DaysToExam ──────────────────────┘
```

## State definitions and evidence

Difficulty and mastery are ordinal labels supplied by a scenario. Their
assessment criteria should be kept consistent across scenarios; they are not
automatically measured by the network. Exact positive integer days remaining
becomes `urgent` for 1–2 days, `near` for 3–7 days, and `distant` for 8 or more.
Exam day or a past exam is invalid input. The initial interface requires all
three difficulties, all three masteries, current stress, and days remaining.

The eight root variables have uniform priors (`1/3` per state). Because all
roots are observed in the initial interface, these priors do not influence its
posterior predictions. They make the BN complete; they are not claims about
the real-world frequency of difficulty, mastery, stress, or exam dates.

## Handcrafted CPTs

For each concept, encode difficulty as easy=0, medium=1, hard=2 and mastery as
low=0, medium=1, high=2. Calculate the concept score `2 × mastery − difficulty`
and average the three scores to obtain `s`. For readiness states low, medium,
and high, use centers `c = −1, 1, 3`, respectively. Give each state an
unnormalized weight `exp(−(s − c)² / (2 × 1.25²))`, then divide each weight by
their sum. This fully specifies the 729 columns of `P(Readiness | concepts)`.
It assumes mastery improves readiness and difficulty reduces it; the width
parameter 1.25 prevents a completely certain readiness prediction.

For example, three hard concepts with low mastery produce `s = −2` and
approximately `P(Readiness) = (0.928, 0.072, 0.000)` for low, medium, high.
Three easy concepts with high mastery produce `s = 4` and the reverse ordering.
These values are illustrative handcrafted parameters, not fitted estimates.

For `P(ExamSuccess=success | Readiness, Stress, DaysToExam)`, let `r` be the
readiness index (low=0, medium=1, high=2), `t` the stress index (low=0,
medium=1, high=2), and `d` the time effect (urgent=−0.5, near=0,
distant=0.35). The success log-odds are

```text
L = −0.5 + 1.1 × (r − 1) − 0.35 × (t − 1) + d
P(success) = 1 / (1 + exp(−L))
P(failure) = 1 − P(success)
```

For medium readiness, medium stress, and a near exam, `L = −0.5`, so
`P(success) ≈ 0.378` and `P(failure) ≈ 0.622`. Higher readiness increases
success; greater stress and proximity to the exam decrease it, with the other
parents fixed. These coefficients are model assumptions that should be
revisited if empirical evidence becomes available.

## Inference task

Use `pgmpy` variable elimination to query
`P(ExamSuccess | Difficulty1–3, Mastery1–3, Stress, DaysToExam)` and return
the probability of `success`. For instance, compare a student with medium
mastery and stress five days out under all-easy versus all-hard concepts:
the predicted success chances are approximately 0.499 and 0.287, respectively.
The harder scenario has a lower posterior success probability. An
action will be evaluated by applying its explicitly assumed mastery/stress
changes to the evidence and repeating this query. The BN does not learn or
identify causal action effects.

The future scheduling component retains exact dates. Free hours determine
whether a proposed study action fits, and preferred study times rank open
slots; neither is currently a BN variable. This keeps the model within the
course's roughly ten-variable limit while allowing time-aware scheduling.
