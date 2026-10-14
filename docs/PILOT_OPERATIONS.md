# Running the SeasonLens pilot

Recruit 3–5 people who handle price/FX history or reports. Include at least one person who has not seen the app. Invite them individually yourself; this document does not send messages or enrol anyone. Use only the invented workbook for this test. The initial pilot tests usability and practical relevance, not analytical profitability.

## Send the test

Share **https://eluyz.github.io/SeasonLens/pilot/**.

Polish invitation to copy:

> Testuję SeasonLens — bezpłatne narzędzie do analizy historii cen i walut. Czy możesz wykonać trzy krótkie zadania z tej instrukcji: https://eluyz.github.io/SeasonLens/pilot/#pl ? Zarezerwuj około 15–25 minut. Nie trzeba instalować aplikacji ani podawać własnych danych; użyj wymyślonego przykładu z instrukcji. Najbardziej pomoże mi informacja, gdzie utkniesz i czy użył(a)byś tego do konkretnego zadania. Odpowiedzi możesz przesłać mi prywatnie; formularz GitHuba jest opcjonalny i publiczny.

English invitation to copy:

> I am testing SeasonLens, a free tool for exploring price and currency history. Could you try the three tasks here: https://eluyz.github.io/SeasonLens/pilot/#en ? Allow around 15–25 minutes. No installation or data of your own is needed; use the invented example in the instructions. Please tell me where you get stuck and whether you would use it for a specific task. You can reply privately to me; the GitHub form is optional and public.

Ask each tester to perform the three tasks independently first. If you help, record which task needed help; do not reclassify the result as independent. They may stop or skip any task. Feedback is optional. Allow roughly 15–25 minutes and record actual time rather than enforcing a promise.

The live app needs an internet connection to open. The frozen browser ZIP includes `pilot/index.html`, local guides and the invented workbook; extract the complete folder. Sending a GitHub issue still needs internet and an account. Public GitHub feedback is tied to that account. A private text reply to the inviter is an alternative; no original workbook or report needs to be shared.

## Record outcomes

Use local tester labels such as T01 rather than names/emails in the public project. Keep private replies private unless the tester agrees to an anonymised summary. For each tester record:

| Field | Values |
|---|---|
| Build | Release version, or online demo plus test date |
| Device/browser | Broad type and browser, no device identifiers |
| Each task | Independent / with help / not completed / not attempted |
| Time | Self-reported approximate minutes or unknown |
| Main obstacle | Task and plain description without private data |
| Return intent | Yes / maybe / no and general purpose |

Report invitations, responses and attempts separately. Task success = independently completed / attempted for that task; also show the raw numerator/denominator and helped completions. Skipped tasks are not failed attempts. Intended reuse is a self-report, not demonstrated return usage. Three to five testers provide qualitative findings, not a representative adoption estimate.

Fix reproducible blocking problems first, then repeated terminology/navigation obstacles. Retest affected tasks with invented data and record the repair in an issue/changelog. Do not invent quotes, testimonials, outcomes or completed pilot milestones.

## What existing GitHub statistics mean

- Stars, forks and public feedback show repository activity, not completed analyses.
- Release asset download counters include our own verification, repeat downloads and possible automation. Do not sum four assets and call the total users.
- Repository Traffic views/clones are separate authenticated owner statistics with limited history. They do not measure visits or analysis actions on the GitHub Pages app.
- No automatic app-event analytics is configured in this pilot. A completed feedback report is stronger evidence than a page visit but still self-reported. Absence of feedback does not prove nobody used the app.

After the pilot, prepare an evidence summary with date, build, cohort size, task outcomes, limitations and the changes made. Decide whether participants have a recurring task worth supporting before expanding the feature set.
