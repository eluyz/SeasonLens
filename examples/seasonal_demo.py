"""Generate a local 5/10-year seasonal HTML report from one CSV series."""

import argparse
from datetime import date
from pathlib import Path

from seasonlens import CSVImportError, analyze_seasonality, import_csv, render_seasonal_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    parser.add_argument('--instrument', required=True)
    parser.add_argument('--instrument-column', default='instrument_id')
    parser.add_argument('--date-column', default='date')
    parser.add_argument('--value-column', default='value')
    parser.add_argument('--date-format', default='%Y-%m-%d')
    parser.add_argument('--delimiter', default=',')
    parser.add_argument('--decimal', default='.')
    parser.add_argument('--skip-rows', type=int, default=0)
    parser.add_argument('--skip-missing', action='store_true')
    parser.add_argument('--as-of', type=date.fromisoformat, required=True)
    parser.add_argument('--unit', default='Original input units')
    parser.add_argument('--output', type=Path, default=Path('outputs/seasonal_report.html'))
    args = parser.parse_args()
    try:
        imported = import_csv(
            args.path, date_column=args.date_column, value_column=args.value_column,
            date_format=args.date_format, delimiter=args.delimiter, decimal=args.decimal,
            instrument_column=args.instrument_column, instrument=args.instrument,
            missing_values='skip' if args.skip_missing else 'reject', skip_rows=args.skip_rows,
        )
        profiles = [analyze_seasonality(imported.frame, as_of=args.as_of, window_years=n) for n in (5, 10)]
        html = render_seasonal_report(profiles, title=f'SeasonLens — {args.instrument}', unit=args.unit,
            import_summary={'Prepared observations': len(imported.frame),
                            'Explicitly omitted blank values': len(imported.skipped_missing_rows),
                            'Rows excluded by instrument': len(imported.filtered_instrument_rows)})
        # Explicit output must never replace input, including symlink aliases.
        if args.output.resolve() == Path(args.path).resolve():
            raise ValueError('Output must differ from the input file.')
        if args.output.exists():
            raise ValueError('Output already exists; choose a new path to preserve prior reports.')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also prevents accidentally overwriting a file
        # created after the preceding check.
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(html)
    except CSVImportError as error:
        print(str(error))
        for issue in error.report.issues[:10]:
            print(f'Row {issue.row}: {issue.code}: {issue.message}')
        raise SystemExit(1) from None
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Report saved: {args.output.resolve()}')
    print('Open this HTML file in a browser. Keep reports from restricted inputs private.')


if __name__ == '__main__':
    main()
