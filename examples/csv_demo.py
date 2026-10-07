"""Run local CSV-to-monthly analysis; use synthetic inputs for public output."""

import argparse
from datetime import date

from seasonlens import CSVImportError, aggregate_monthly, import_csv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    parser.add_argument('--date-column', default='date')
    parser.add_argument('--value-column', default='value')
    parser.add_argument('--date-format', default='%Y-%m-%d')
    parser.add_argument('--delimiter', default=',')
    parser.add_argument('--decimal', default='.')
    parser.add_argument('--instrument-column', default='instrument_id')
    parser.add_argument('--instrument', required=True)
    parser.add_argument('--skip-missing', action='store_true')
    parser.add_argument('--max-date', type=date.fromisoformat)
    args = parser.parse_args()
    try:
        result = import_csv(
            args.path, date_column=args.date_column, value_column=args.value_column,
            date_format=args.date_format, delimiter=args.delimiter, decimal=args.decimal,
            instrument_column=args.instrument_column, instrument=args.instrument,
            missing_values='skip' if args.skip_missing else 'reject', max_date=args.max_date,
        )
    except CSVImportError as error:
        print(str(error))
        for issue in error.report.issues[:10]:
            print(f'Row {issue.row}: {issue.code}: {issue.message}')
        if len(error.report.issues) > 10:
            print(f'{len(error.report.issues) - 10} additional issues are available in the report.')
        raise SystemExit(1) from None
    print(f'Imported observations: {len(result.frame)}')
    print(f'Explicitly skipped blank values: {len(result.skipped_missing_rows)}')
    print(f'Rows excluded by instrument: {len(result.filtered_instrument_rows)}')
    print(f'Rows excluded by cutoff: {len(result.filtered_date_rows)}')
    monthly = aggregate_monthly(result.frame)
    print('\nMonthly means (original input units)')
    print(monthly.means.to_string())
    print('\nObservation counts (not trading-session completeness)')
    print(monthly.counts.to_string())


if __name__ == '__main__':
    main()
