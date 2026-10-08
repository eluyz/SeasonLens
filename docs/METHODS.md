# Market analysis methods

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
