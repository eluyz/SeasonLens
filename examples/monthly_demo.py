"""Synthetic example; these values are not real market data."""

import pandas as pd

from seasonlens import aggregate_monthly


def main():
    data = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-03", "2026-02-01"]),
            "value": [100.0, 120.0, 200.0],
        }
    )
    result = aggregate_monthly(data)
    print("SYNTHETIC DATA — monthly means")
    print(result.means.to_string())
    print("\nObservation counts (not calendar completeness)")
    print(result.counts.to_string())


if __name__ == "__main__":
    main()
