# Decisions

## 2026-10-07 — First checkpoint

- Scope: monthly arithmetic means and observation counts only. Importers, multi-year profiles and UI are separate tasks.
- Use prepared datetime/numeric columns to keep parsing out of the mathematical core.
- Retain all intervening years and all 12 months so missing data stay visible.
- Use pandas 2.2.3, available in the development environment, and pin it for this experimental checkpoint.
- Use standard-library unittest for the first independent acceptance cases because pytest is not available in the current environment. This revises the plan's proposed testing tool, not its mathematical acceptance criteria.
- Research of existing tools and confirmation of the product's value remain necessary before expanding toward a public application.
- The first checkpoint was stored as an archive before repository setup. The owner has now connected the public repository eluyz/SeasonLens. Source files will be maintained there; no release tag or background runner is configured.
- Independent review exposed numeric overflow and unsupported long-double inputs. Reject these explicitly; do not silently emit infinite means or expose pandas' internal type error.
- Use English for all repository documentation, code comments, issue text and commit messages. Coordination with the owner continues in Polish.
