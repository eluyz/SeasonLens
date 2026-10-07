# Backlog

| ID | Scope | Acceptance | Status |
|---|---|---|---|
| SL-000 | Alternatives and need validation | Identify existing tools and a concrete justified use case | Open |
| SL-001 | Monthly aggregation core | Hand-calculated means/counts, retained gaps, no input mutation, strict preconditions | Complete for experimental checkpoint |
| SL-001A | Automated GitHub checks | Run relevant tests on pushes and pull requests; verify a successful run | Planned |
| SL-002 | Quality-report layer | Explain invalid data and require explicit handling choices | Complete for experimental checkpoint |
| SL-003 | CSV import | Explicit column mapping, separator, decimal and date format | Complete for experimental checkpoint |
| SL-004 | 5/10-year profiles | Equal-year weighting, exact calendar window, actual year count, min/max | Complete for experimental checkpoint |
| SL-005 | CSV/HTML export | Same values and metadata as calculation output | Complete for experimental checkpoint: local HTML, observation CSV and private DB export |
| SL-006 | XLSX import | Select one sheet, no macro execution, clear formula-value handling | Planned |
| SL-007 | Local interface | Complete file-to-result workflow with readable errors | Implemented locally; full-browser/mobile QA pending |
| SL-008 | Public v0.1 | Tested install, docs, examples, license, public repository | Planned |
| SL-009 | Pilot | Real independent feedback and documented corrections | Planned |

| SL-010 | Private persistence and direct ECB updater | Atomic unique-date revisions, auditable sources, no silent mixing, explicit backup/recovery | Implemented; hosted schedule and live transport unverified |
| SL-011 | Extended exploration | Daily/SMA, returns, matched partial months, normalized index, exact-date PLN conversion, coverage | Implemented; synthetic demo and private snapshot |
| SL-012 | MATIF continuation-close collector | Verified close definition, underlying expiry/roll/adjustment rules and compatible feed | Open; no automatic futures feed |


SL-001 is a reversible technical spike while SL-000 remains open; implementation does not establish product demand or OSS-program eligibility.
