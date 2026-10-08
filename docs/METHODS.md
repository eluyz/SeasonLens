# Market analysis methods

## Statistical analysis

Full input and output definitions are in [SCIENCE_SPEC.md](SCIENCE_SPEC.md). Risk, FX and forecast evaluation use the explicitly selected one-year, five-year or full-history period. Horizons count observed intervals; missing sessions are never inserted. Buyer losses are price rises and seller losses are price falls. Historical VaR uses the empirical quantile; Expected Shortfall integrates the upper tail including its fractional boundary weight. A minimum of five equivalent tail observations is required. Multi-observation horizons overlap and are dependent. Current-budget exposure applies the signed historical change to the latest quote times quantity; it is not futures holding P&L.

Commodity/FX risk matches the start and end dates of each original source's log changes. Sample variances use ddof=1. Euler contributions are cov(component, combined), algebraically own variance plus covariance. They can be negative or above 100%; shares are undefined for zero or numerically unresolved combined variability.

Return seasonality uses actual last observed monthly quotes and the immediately preceding calendar month's quote, requiring positive endpoints. Missing calendar months break changes. The current year is excluded; each completed year contributes at most one change per month. The declared calendar midpoint fixes the early/late split. Leave-one-out means expose single-year sensitivity. A seeded non-circular moving two-year block bootstrap resamples whole year vectors together, retaining missingness. Its approximate 95% interval concerns the historical mean under these assumptions, requires at least eight contributing years and 90% valid replicates, and is not a future-price interval or significance verdict.

Walk-forward comparison trains only through each origin, scores later observations through the cutoff, and uses identical samples for last-price, expanding-history drift and trailing-20-mean models. At least 200 training observations and at most 252 recent eligible origins per horizon are used. MAE/RMSE are in selected units; skill is 1 minus error divided by the naive baseline error, undefined for a zero baseline. Earlier history supplies training even when evaluation is restricted to a shorter period. No model tuning, profitability claim or automatic future forecast is supplied.

Fundamental estimates are separate from prices. [Normalized imports](FUNDAMENTALS.md) retain publication date, commodity, geography, marketing year and units. Stocks-to-use is 100 × ending stocks / total use; revisions compare releases of the same declared balance. Future publication dates are excluded after full validation. USER_FILE imports and SYNTHETIC examples are never labelled official USDA observations.

Method references: [Acerbi and Tasche on Expected Shortfall](https://arxiv.org/abs/cond-mat/0105191), [Forecasting: Principles and Practice on rolling-origin evaluation](https://otexts.com/fpp3/tscv.html), [forecasting baselines](https://otexts.com/fpp3/simple-methods.html) and [time-series bootstrap concepts](https://otexts.com/fpp3/bootstrap.html). These references explain general methods; they do not validate a predictive relationship for these instruments or the invented examples.

SeasonLens describes the supplied observations. Built-in browser samples are invented; a user CSV has its own declared units and cutoff. Observation counts do not certify complete trading sessions. No missing date is filled, and no price series is silently repaired or roll-adjusted.

## Market snapshot and historical position

The reference price is the last available observation on or before the explicit analysis cutoff. Show its actual date. The daily change uses the immediately previous observation, which is not necessarily the previous calendar or trading day. Calendar-month and year-to-date comparisons use the last available observation on or before their stated target date; display the actual baseline date. Missing baselines remain unavailable.

For positive prices, a percentage change is `100 × (last / baseline − 1)`. Distance from SMA200 uses the mean of the latest 200 observations, with a complete warmup window. Zero or negative levels remain valid level inputs but are not interpreted as positive-price percentage returns.

Historical position uses the stated trailing calendar-year window. The empirical percentile is `100 × (count below the reference + 0.5 × count equal to the reference) / count`. Equal observations therefore receive a midpoint rank. The reference observation is included; minimum, maximum, actual date window and observation count are shown. Percentiles describe supplied nominal levels, not fundamental value or forecasts.

## Momentum and volatility

RSI uses Wilder's 14-observation convention. The first value requires 15 prices: initialize average gains and losses with the first 14 price differences, then update each as `(previous average × 13 + new amount) / 14`. All-flat changes give RSI50; gains without losses give100 and losses without gains give0. Its plot uses the meaningful0–100 domain and labels the30/70 reference lines. These thresholds are descriptive guides.

Realized volatility uses `100 × sample standard deviation of ln(price / previous price)` over exactly20 or60 observed changes, with `ddof=1` and complete windows. It is **not annualized**. Price changes can span gaps in the supplied observations; there is no invented weekend or trading-session calendar. Nonpositive prices do not support logarithmic changes.

## Commodity and currency attribution

For a commodity in EUR/t and a separately identified PLN-per-EUR series, use observations on exactly matching dates. There is no carry-forward of either series. Given start/end values `P0`, `P1`, `F0`, `F1`, the change in the converted benchmark is:

```text
Commodity component = (P1 − P0) × F0
Currency component  = P0 × (F1 − F0)
Interaction          = (P1 − P0) × (F1 − F0)
Total PLN/t change   = P1 × F1 − P0 × F0
```

The three components add to the total. Percentage-point contributions divide each component by `P0 × F0`, then multiply by100. Example:200EUR/t at4PLN/EUR becomes210EUR/t at4.2PLN/EUR:800→882PLN/t; components40+40+2=82PLN/t. Display endpoint dates and whether the FX observations are invented, reference rates or explicitly selected user inputs. Converted values are indicative benchmarks, not executable quotes.

## Comparisons, correlations and spreads

Index-100 comparisons use a common observed starting date in the selected range. Every series is divided by its own value on that date and multiplied by100. Show the shared base date and coverage; no filling or total-return claim is made.

Correlations compare price changes rather than nominal price levels. Changes are matched by both their start and end dates, so a one-day move is not paired with a multi-day move ending on the same date. Show window size, actual paired count and dates. Constant changes have an undefined correlation. The three built-in FX series are algebraically dependent: USD/PLN=EUR/PLN÷EUR/USD. Their correlations are not evidence of three independent markets.

The wheat/corn spread is wheat price minus corn price on a matching date in identical units. It is a difference between two supplied commodity benchmarks, not a calendar spread between delivery contracts. Show its units and actual coverage.

## Seasonal distribution and scenarios

Seasonal distribution summaries use one monthly arithmetic mean per completed baseline year, giving each available year equal weight. Median and25th/75th percentiles describe the distribution of **yearly monthly means**, not daily lows/highs or a prediction interval. Show contributing years and daily observation counts; keep current partial months separate from completed-year summaries.

The scenario calculator evaluates declared hypothetical commodity price, PLN-per-EUR rate and tonnage. Benchmark PLN/t is price×FX; benchmark value is price×FX×tonnes. Label all assumptions and differences. This calculator does not infer a forecast or a delivered purchase price.

## Continuous futures and input definitions

Supplied futures prices can be continuation series with unknown roll rules. Switching underlying contracts can create a discontinuity; an indexed continuation-price chart is not an investable futures return. A roll adjustment requires actual contract definitions and prices, not guessed corrections. Seasonal nominal prices can also reflect inflation and changing market regimes.

Close-only input cannot produce genuine intraday candlesticks or ATR, which need open/high/low/close information. A futures term structure requires prices for specific delivery contracts. These views are outside the current close-only scope.
