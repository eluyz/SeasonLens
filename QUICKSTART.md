# First SeasonLens checkpoint

Version 0.0.1 contains a project skeleton and monthly aggregation core. It is not yet a file-upload application.

Follow README.md for installation. Run `python examples/monthly_demo.py` from the project directory after installing the package.

The example contains invented observations. January 2024 should have a mean of 110 and two observations. Year 2025 should remain entirely missing. February 2026 should have a mean of 200 and one observation.

Run `python -m unittest discover -s tests -v` to check the mathematical and input-validation cases. The current checkpoint has nine tests.

The next tasks are validating the project's need, automated repository checks, quality reporting and explicit CSV import. See BACKLOG.md for acceptance criteria. No background executor or OSS-program application has been configured.
