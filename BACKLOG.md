# Backlog

| ID | Scope | Acceptance | Status |
|---|---|---|---|
| SL-015 | Historical statistical analysis | Fractional-tail risk, exact-interval variance, completed-year stability, no-leakage fixed-model comparison, release-vintage fundamental imports | Implemented and independently reviewed; publication verification recorded in STATUS.md |
| SL-016 | Official fundamental adapter | Verified commodity/geography/unit mapping, publication vintages, reproducible source parsing and redistribution conditions | Open; private normalized CSV and invented examples available |

| ID | Scope | Acceptance | Status |
|---|---|---|---|
| SL-000 | Alternatives and need validation | Identify existing tools and a concrete justified use case | Open |
| SL-001 | Monthly aggregation core | Hand-calculated means/counts, retained gaps, no input mutation, strict preconditions | Complete for experimental checkpoint |
| SL-001A | Automated GitHub checks | Run relevant tests on pushes and pull requests; verify a successful run | Public builder source-push checks verified; broader PR CI remains open |
| SL-002 | Quality-report layer | Explain invalid data and require explicit handling choices | Complete for experimental checkpoint |
| SL-003 | CSV import | Explicit column mapping, separator, decimal and date format | Complete for experimental checkpoint |
| SL-004 | 5/10-year profiles | Equal-year weighting, exact calendar window, actual year count, min/max | Complete for experimental checkpoint |
| SL-005 | CSV/HTML export | Same values and metadata as calculation output | Complete for experimental checkpoint: local HTML, observation CSV and private DB export |
| SL-006 | XLSX import | Explicit worksheet/physical rows/columns/units, cached-formula consent, atomic validation and no transmission | Published; 175 tests and actual six-instrument desktop Chrome import/export verified |
| SL-007 | Local interface | Complete file-to-result workflow with readable errors | Local app implemented; public browser flow verified; physical mobile-device QA open |
| SL-008 | Public v0.1 | Tested install, docs, examples, license, public repository | Planned |
| SL-009 | Pilot | Real independent feedback and documented corrections | Planned |

| SL-010 | Private persistence and direct ECB updater | Atomic unique-date revisions, auditable sources, no silent mixing, explicit backup/recovery | Implemented; hosted schedule and live transport unverified |
| SL-011 | Extended exploration | Daily/SMA/Bollinger, recent five-year prices, returns, matched partial months, normalized index, exact-date PLN conversion, coverage | Implemented; six-line technical and current-inclusive five-year views |
| SL-012 | MATIF continuation-close collector | Verified close definition, underlying expiry/roll/adjustment rules and compatible feed | Open; no automatic futures feed |


SL-001 is a reversible technical spike while SL-000 remains open; implementation does not establish product demand or OSS-program eligibility.

| ID | Scope | Acceptance | Status |
|---|---|---|---|
| SL-013 | Market context and comparisons | Dated snapshot changes, historical percentile, exact-date PLN attribution, common-base index100, Wilder RSI14, unannualized log-change volatility, exact-interval correlations, equal-unit wheat/corn spread, equal-year seasonal quartiles, explicit scenario assumptions | Published; 147 tests, independent mathematical review and desktop Chrome control checks passed |
| SL-014 | Browser-only CSV exploration | Explicit columns/dialect/cutoff, strict rejection before omissions, separate user IDs, no network or persistent storage, actual control and export verification | Published; actual Chrome private import, cutoff, source isolation, CSV export and reload cleanup verified |
