# Study Planner System

## Project Description

**Use a calendar API to build a personalized, Bayesian study planning system.** The system should take as input upcoming exam dates and dynamically schedule study sessions based on the user's mastery of course concepts. These scheduling needs should be modeled using a Bayesian network that considers variables like concept difficulty, current stress level, and days remaining until the exam. The system's decision-making process must use a utility function that balances exam success against student stress. The system will choose between three or more specific actions (e.g., (i) schedule an intense, mandatory 5-hour study block today, (ii) schedule a light 1-hour review session, or (iii) clear the calendar for a rest day). To demonstrate your system works as intended, you'll need to simulate different types of student scenarios (e.g., a struggling student vs. an advanced student) and show that the system adapts its scheduling behavior accordingly.

### Requirements

Create a simple Bayes net with variables that model difficulty of 3+ concepts and develops a study plan that maximizes exam success and minimizes last minute cramming stress (use additional variables in your model as needed, but keep your network to ~10 variables or less). Handcraft the model variables and CPTs clearly with an explanation of the parameters, identify the inference task and which variable(s) you query (be sure to document this), define 3+ specific actions for the system, define a utility function that expresses exam success and stress while depending on the query variables, use a built-in inference algorithm to make your query, compute the expected utility of each system action, take the best action, incorporate this into the calendar API and demonstrate this with different concept difficulties that will result in the system taking different actions.

---

## Setup and verification

From a repository checkout, use Python 3.11 or newer and
[uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

Run the repository checks with:

```bash
uv run pre-commit run --all-files
uv run pre-commit run --all-files --hook-stage pre-push
```

The pre-push checks include the test suite. See [AGENTS.md](AGENTS.md) for
contributor rules and the additional commands required after code changes.

## Project status

Bayesian inference, six-action utility evaluation, contrasting student examples,
and offline daily session scheduling are implemented. Calendar API integration
is outstanding: examples read local JSON observations and busy blocks, and do
not read or write Google Calendar events.

See [project and bug status](docs/project-status.md) for requirement coverage,
verified example results, limitations, and remaining deliverables.

## Documentation and requirement coverage

The linked documents contain the detailed explanations for the requirements above.

| Requirement or deliverable | Documentation |
| --- | --- |
| Three concepts, approximately ten variables, and handcrafted CPT parameters | [Bayesian network specification](docs/bayesian-model.md) |
| Inference task, query variable, and built-in inference algorithm | [Inference task](docs/bayesian-model.md#inference-task) |
| Three or more actions and their assumed effects | [One-day study decisions](docs/decision-model.md) |
| Utility function, expected utility, and best feasible action selection | [Expected utility](docs/decision-model.md#expected-utility) |
| Different student scenarios and resulting actions | [Example scenarios](#example-scenarios) and [verified results](docs/project-status.md#verified-example-results) |
| Calendar scheduling and API integration status | [Offline replay](docs/decision-model.md#comprehensive-scenario-replay) and [remaining deliverables](docs/project-status.md#remaining-deliverables) |
| Project/bug status and feature-to-file explanation | [Project status](docs/project-status.md) and [architecture and file structure](docs/architecture.md) |

## Example scenarios

Run every example or select one by its filename without `.json`:

```bash
uv run study-planner all
uv run study-planner run mixed
uv run study-planner run-comp progressing
```

Available examples are `advanced`, `mixed`, `stressed`, and `struggling`.

`run-comp progressing` replays each dated observation before the exam, chooses
an action that fits the day's calendar, and displays assigned study sessions.
See [the decision model](docs/decision-model.md#comprehensive-scenario-replay)
for the input format and scheduling assumptions.
