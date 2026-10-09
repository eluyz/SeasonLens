# Wheat and EUR/PLN: from a workbook to a report

Use the [public demo](https://eluyz.github.io/SeasonLens/) with the [invented XLSX template](https://eluyz.github.io/SeasonLens/seasonlens-import-template.xlsx). This walkthrough is also available as a [mobile-friendly web page](https://eluyz.github.io/SeasonLens/walkthrough.html). Allow roughly 5–10 minutes on a desktop; column mapping can take longer on a phone.

The goal is to import **only wheat and EUR/PLN from the same workbook**, check a PLN-per-tonne conversion, understand the short history and save a report. All workbook observations are invented. They are not MATIF closes, central-bank rates or a forecast.

## 1. Open the example file

Start in a fresh demo tab so there are exactly six built-in sample instruments. Expand **Start here — explore, import or create a report**, then choose **Download example XLSX template**. You can also use the template link above.

Choose **Open private import**, select `seasonlens-import-template.xlsx` under **Excel workbook or CSV file**, set **Analysis cutoff** to **2026-10-06**, then choose **Open and preview file**. Opening the workbook does not import it.

## 2. Declare rows and two instruments

Check these settings even if they already have the right values:

| Field | Value |
| --- | --- |
| Worksheet | Prices |
| Header row | 1 |
| First data row | 4 |
| Date column | A · Date |
| Analysis cutoff | 2026-10-06 |
| Text date format | YYYY-MM-DD |
| Decimal separator for text prices | . |

Row 2 declares units. Row 3 contains deliberately invented live-example values dated 2026-10-07; it must remain outside the selected history. The preview still shows this physical row for checking. Numeric/date cells in this template need no text parsing or formula consent. Leave **Explicitly skip empty price cells, with row counts** and **Use stored results of Excel formulas (may be stale)** unchecked.

In **Choose instruments from price columns**, check **only B and E**. Leave C, D, F and G unchecked. Declare:

| Column | Instrument title | Units | Role |
| --- | --- | --- | --- |
| B | Wheat sample | EUR/t | Wheat |
| E | EUR/PLN sample | PLN per EUR | EUR/PLN |

Column names do not assign roles. Selecting EUR/PLN as the role sets its suggested units; verify **PLN per EUR** explicitly.

## 3. Validate, review, then add

Choose **Validate selected instruments**. The review should show **two instruments**, each with:

- **210 observations**, from **2025-12-17** through **2026-10-06**;
- **0 blank values skipped** and **0 future rows excluded**;
- no observation from row 3. That row is outside the selected physical data range, rather than counted as a future-row omission.

Nothing has been added yet. Choose **Add validated instruments to this tab** once. The instrument selector now has **eight entries**: the original six samples and two private imports. The import is labelled **USER_FILE**, despite containing invented example values. This label describes how the data entered the app, not an official provider.

Changing any import setting invalidates the review and requires validation again.

## 4. Check wheat in PLN per tonne

Open **Analysis options**. Under **Instrument**, choose **Wheat sample · private Excel**, not the built-in wheat. Under **Display units**, choose **PLN/t**.

Check **Analysis cutoff: 2026-10-06**, **Observations: 210**, **Last observation: 2026-10-06**, and the conversion note showing **210 exact-date positive pairs** with no commodity observations left unconverted. Only the declared EUR/PLN series from this same import is eligible; the app does not substitute sample FX or carry a rate forward.

The workbook's last historical row, **213**, provides an independent arithmetic check:

```text
213.29 EUR/t × 4.2051 PLN per EUR = 896.905779 PLN/t
```

That is approximately **896.91 PLN/t**, or **89,690.58 PLN** for 100 tonnes. The whole-unit reference beside **Monthly average prices** displays **897**; this is display rounding, not lost calculation precision. For a full-precision check, use **Export selected observations (CSV)** and inspect the final `date` and `value`: date **2026-10-06**, value approximately **896.905779** (the binary floating-point export can show `896.9057789999999`). The CSV also contains the technical indicator columns.

## 5. Read the charts without filling the gaps

Use **View monthly averages** and **View five-year prices** in Start here.

**Monthly average prices** averages observed daily prices within each month. In PLN/t it averages the daily converted products; it does not multiply a monthly wheat average by a monthly FX average. Commodity table prices display whole units, while calculations retain their precision. Colors compare each unrounded monthly mean with the last daily price; they are not buying or selling signals.

**Monthly average prices — last five years including this year** keeps **2022–2026**, even though the template begins in December 2025. Years 2022–2024 and January–November 2025 have no observations. November–December 2026 are after the cutoff. Dashes and chart gaps are expected; they do not mean zero. The dashed period average gives each available yearly monthly mean equal weight. October 2026 is partial, with four observations. Short history cannot establish a reliable seasonal pattern.

For **Technical analysis — last 12 months**, retain **Daily chart range: Last 12 months** and all six line checkboxes. The chart has price, SMA20, SMA100, SMA200 and two Bollinger bands. Only the supplied history is plotted; it is less than 12 months. Full windows are required: the first 19 observations lack SMA20/Bollinger, the first 99 lack SMA100, and the first 199 lack SMA200. Only **11 SMA200 values** are available. These are observation windows, not calendar-day or exchange-session guarantees. Earlier supplied history warms indicators before the displayed range; absent history is never fabricated.

## 6. Check historical risk and coverage

Open **Historical risk and stress episodes** under **Historical risk and statistical analysis**. Keep:

| Control | Value |
| --- | --- |
| Risk, FX and forecast evaluation period | Last 5 calendar years |
| Perspective | Buyer — rising prices are adverse |
| Observed-interval horizon | 1 observed interval |
| Tail confidence | 95% |
| Quantity in tonnes | 100 |

The sample has **209 one-interval changes**. At 95%, the equivalent tail size is **10.45 observations**, enough for the app's minimum of five. Changing **Tail confidence** to **99%** leaves only **2.09**, so VaR and Expected Shortfall become unavailable. That is a coverage safeguard, not an error. Switch back to **95%** before building the default report.

A buyer treats price rises as adverse; a seller treats falls as adverse. The displayed budget scenario applies historical percentage changes to the current benchmark and quantity. It is not transaction profit/loss or a prediction. Five calendar years is the requested window, not a claim that this workbook contains five years of observations.

Optionally open **Commodity and FX contributions to PLN price risk**. With these two imported series there are **209 exact matching intervals**. The variance decomposition includes covariance and describes this sample; its shares are not proof of causation or hedge effectiveness. Completed-year seasonality needs more history: this template cannot support its historical-mean uncertainty intervals.

## 7. Build and save the report

Confirm the private wheat is selected in **PLN/t**, cutoff **2026-10-06**, with the risk settings above. Choose **Open report builder** in Start here. Keep the four initially checked sections:

- **Market snapshot and data coverage**;
- **Monthly average prices and five-year comparison**;
- **Technical chart with selected lines**;
- **Historical risk and stress episodes**.

Choose **Build report preview**. Check **Wheat sample**, **PLN/t**, **2026-10-06** and **USER_FILE** in its metadata. **Download HTML** saves a standalone report with the selected results and charts. **Print / Save PDF** uses the browser's print dialog; choose Save as PDF if offered. PDF saving, pagination and mobile support depend on the browser. The downloaded HTML is the fallback. The snapshot stays fixed; choose **Back to analysis** and rebuild after changing settings.

Reports omit the original observation arrays and application code, but their visible tables, prices and declared sources can still be private. Sharing the report shares those results.

## Finish and known limits

Save anything you want to keep before reloading. Reloading removes both imported instruments and returns the demo to its six built-in samples; no browser import is saved to SQLite. Display preferences may persist, but imported observations do not. For persistent private history, use the local app described in the [getting-started guide](GETTING_STARTED.md) and [README](../README.md).

This exercise performs no live-data collection or automatic refresh. Its 210 dates are invented weekday observations, not a checked exchange calendar. It does not establish predictive skill, five-year coverage or real-market suitability. On small screens, wide tables and charts scroll within their frames; column mapping is easier on a larger screen. Physical-phone, Safari and native PDF-dialog behavior remain platform checks.
