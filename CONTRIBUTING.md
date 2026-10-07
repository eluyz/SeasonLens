# Contributing

SeasonLens is at an early experimental stage. Improvements should preserve auditable calculations and visible missing data.

## Report a problem

Open a GitHub issue with the behavior you expected, the behavior you observed, your Python/pandas versions and a small reproducible example. Use synthetic data or data you have permission to share. Do not include company, client, licensed-market or personal data without the relevant rights.

## Propose a change

Check SPEC.md and BACKLOG.md first. Discuss changes to calculation definitions before implementing them. Keep pull requests focused and describe the problem, resulting behavior and validation.

Install the project following README.md. Run:

```bash
python -m unittest discover -s tests -v
```

For mathematical changes, include a small independently calculated expected result. Preserve zero/negative values, missing months and intervening years. Do not silently interpolate, discard duplicates or change calendar-year windows.

Documentation, comments, commit messages and contributions should use English. Contributions are made under the project's MIT license.
