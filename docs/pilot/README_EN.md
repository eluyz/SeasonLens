# SeasonLens — a 15–25-minute pilot

**English** · [Polski](README_PL.md) · [Browser instructions](index.html#en)

Goal: find out whether you can import a workbook, interpret a monthly comparison and save a report without help. No programming or account is required. Participation and feedback are voluntary. This is not a forecasting or investment-performance test.

Prepare a browser, about 15–25 minutes and the [XLSX template](../seasonlens-import-template.xlsx). Every price and FX quote in it is **invented**. Do not use company files, client data or actual market observations in this pilot. Use the [public English demo](https://eluyz.github.io/SeasonLens/?lang=en) or, in the downloaded bundle, open the [local index.html](../index.html?lang=en) in a browser. When reading this on GitHub, use the public demo. The browser version needs no Python. Extract the entire downloaded archive first.

Open these instructions and the app in separate tabs. Reload the app first: it should have **six built-in sample instruments**. Choose the **English** tile. Do not reload the app tab before saving your report: imports exist only in that tab's memory. Language preference may survive reloading. Wide tables scroll inside their own frames on a phone; column mapping can take longer. Behavior on your device is part of the test.

Record each task's start time and first obstacle. **Independent** means completing the task using these three task instructions. **With help** means also using the full walkthrough or assistance from another person. If you need help, you can use the [full walkthrough](../walkthrough.html); record that in your feedback. You can stop at a blocker: an incomplete task is also useful evidence.

## Task 1 — import and check the conversion (6–10 minutes)

1. Expand **Start here — explore, import or create a report** and choose **Open private import**. Select `seasonlens-import-template.xlsx` under **Excel workbook or CSV file**, set **Analysis cutoff** to `2026-10-06`, then choose **Open and preview file**.
2. Check the following settings. Row 2 declares units; row 3 contains an invented live example dated 2026-10-07. Historical data begin at row 4.

| Field | Value |
| --- | --- |
| Worksheet | Prices |
| Header row | 1 |
| First data row | 4 |
| Date column | A · Date |
| Analysis cutoff | 2026-10-06 |
| Text date format | YYYY-MM-DD |
| Decimal separator for text prices | . |

3. In **Choose instruments from price columns**, check **only B and E**; uncheck C, D, F and G. Explicitly declare the titles, units and roles:

| Column | Instrument title | Units | Role |
| --- | --- | --- | --- |
| B | Wheat sample | EUR/t | Wheat |
| E | EUR/PLN sample | PLN per EUR | EUR/PLN |

These titles are exact example values. Leave **Explicitly skip empty price cells, with row counts** and **Use stored results of Excel formulas (may be stale)** unchecked.

4. Choose **Validate selected instruments**. Expect two instruments, each with **210 observations**, **2025-12-17** through **2026-10-06**, **0 blank values skipped** and **0 future rows excluded**. Row 3 is outside the selected physical data range, so it does not count as a future-row omission. Previewing and validating do not add observations yet.
5. Choose **Add validated instruments to this tab** once. Expect **eight instruments**: six samples and two imports. Changing an import setting requires validation again.
6. In **Analysis options**, select **Wheat sample · private Excel** and **Display units: PLN/t**. Check 210 exact-date pairs and last observation `2026-10-06`. The reference beside **Monthly average prices** should display **897 PLN/t**, rounded to a whole unit.

Arithmetic check: `213.29 EUR/t × 4.2051 PLN per EUR = 896.905779 PLN/t`. Conversion uses FX from this same import on exact matching dates, without filling gaps. **USER_FILE** describes the import path, not an official market provider. This browser import does not save anything to SQLite.

**Completion:** both instruments added; private wheat selected in PLN/t; 210 observations and reference 897. Record whether help was needed.

## Task 2 — monthly comparison and coverage (4–6 minutes)

1. Choose **View monthly averages**, then **View five-year prices** in Start here. Keep private wheat in PLN/t and cutoff `2026-10-06`.
2. Find the **2022–2026** window. Answer in your own words: why do 2022–2024 have gaps, what do the dashes mean, and does this table demonstrate five years of actual observations?
3. Check December 2025 and October 2026. The template starts only on **2025-12-17**. January–November 2025 have no observations; November–December 2026 are after the cutoff. October 2026 is **partial, with four observations**.
4. Open **Technical analysis — last 12 months**. With all six lines enabled, check why SMA200 appears only at the end. There are **11 available SMA200 values** in 210 observations: the first 199 lack a full window. These windows count observations, not guaranteed calendar days.

A monthly average averages observed daily prices; the dashed period average weights each available yearly monthly average equally. In PLN/t it averages daily price × FX products. **A dash means unavailable, not zero.** Choosing a five-year window does not create the missing history. This short template cannot establish a reliable seasonal pattern. Colors and averages are not trading signals.

**Completion:** you can explain the gaps, partial October and 11 available SMA200 values. Record your explanation in the feedback, even if you needed help.

## Task 3 — save a selected report (4–6 minutes)

1. Keep private wheat, PLN/t, `2026-10-06` and your selected language. Choose **Open report builder** in Start here.
2. Select only three sections: **Market snapshot and data coverage**, **Monthly average prices and five-year comparison**, **Technical chart with selected lines**. Uncheck all others; historical risk is not needed for this task.
3. Choose **Build report preview**. Check three sections and metadata **Wheat sample**, **PLN/t**, **2026-10-06**, **USER_FILE**. The report labels and description should be English; the declared title and machine codes keep their supplied text.
4. Choose **Download HTML**, find the saved file and open it in a browser. Check that it works as a standalone report with the same data and language. Optional technical check if you know how to view page source: the document has `<html lang="en">` (for a Polish test: `pl`). This is not required to complete the pilot.
5. The report is a fixed snapshot: later app language or setting changes do not change the downloaded file. Build a new preview for a new report. PDF saving is optional and depends on the browser print dialog; this pilot checks the HTML download.
6. Only after saving the report, reload the app tab. Both imports should disappear, leaving **six built-in samples**. The selected language may remain.

**Completion:** downloaded HTML opens with three selected sections and correct metadata/language; reloading clears imports. Reports omit original observation arrays but include visible prices and results. Do not submit reports containing actual data to public issues.

## Give feedback (2–3 minutes)

Complete [FEEDBACK_EN.md](FEEDBACK_EN.md) by copying its text into a message. You can send it privately to the person who invited you to the test, without publishing it on GitHub. You need not provide your name, company, email address or private filenames.

Optionally [open a GitHub issue](https://github.com/eluyz/SeasonLens/issues/new/choose). **Issues, your GitHub account and attachments are public.** Publish only if you deliberately choose to share your feedback. Describe reproduction using the invented template; do not attach actual market data, client screenshots, private reports or company filenames. Feedback is manual: these instructions contain no form, tracking or automatic submission.

## How pilot results will be read

Record each task as **independent / with help / incomplete / not attempted**, with time and obstacle. Separately describe a specific task you might use the app for and whether you would use it again. Completing the example does not establish actual-market suitability or independent adoption. Import, coverage understanding and report-saving blockers will be addressed first.
