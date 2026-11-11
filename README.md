# Study Planner System

## Project Description

**Use a calendar API to build a personalized, Bayesian study planning system.** The system should take as input upcoming exam dates and dynamically schedule study sessions based on the user's mastery of course concepts. These scheduling needs should be modeled using a Bayesian network that considers variables like concept difficulty, current stress level, and days remaining until the exam. The system's decision-making process must use a utility function that balances exam success against student stress. The system will choose between three or more specific actions (e.g., (i) schedule an intense, mandatory 5-hour study block today, (ii) schedule a light 1-hour review session, or (iii) clear the calendar for a rest day). To demonstrate your system works as intended, you'll need to simulate different types of student scenarios (e.g., a struggling student vs. an advanced student) and show that the system adapts its scheduling behavior accordingly.

### Requirements

Create a simple Bayes net with variables that model difficulty of 3+ concepts and develops a study plan that maximizes exam success and minimizes last minute cramming stress (use additional variables in your model as needed, but keep your network to ~10 variables or less). Handcraft the model variables and CPTs clearly with an explanation of the parameters, identify the inference task and which variable(s) you query (be sure to document this), define 3+ specific actions for the system, define a utility function that expresses exam success and stress while depending on the query variables, use a built-in inference algorithm to make your query, compute the expected utility of each system action, take the best action, incorporate this into the calendar API and demonstrate this with different concept difficulties that will result in the system taking different actions.

---

## Example scenarios

Run every example or select one by its filename without `.json`:

```bash
uv run study-planner all
uv run study-planner run mixed
```

Available examples are `advanced`, `mixed`, `stressed`, and `struggling`.
