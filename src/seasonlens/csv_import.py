"""Explicit CSV parsing and auditable preparation of one daily series."""

import csv
from dataclasses import dataclass
from datetime import date, datetime
import math
from pathlib import Path
import re

import pandas as pd

from .quality import QualityIssue, QualityReport, inspect_series


@dataclass(frozen=True)
class CSVImportResult:
    """Prepared frame and the selected input's report before approved omissions."""

    frame: pd.DataFrame
    report: QualityReport
    source_rows: tuple[int, ...]
    skipped_missing_rows: tuple[int, ...]
    filtered_instrument_rows: tuple[int, ...]
    filtered_date_rows: tuple[int, ...]


class CSVImportError(ValueError):
    """Import failed; inspect report for source locations and reasons."""

    def __init__(self, report: QualityReport):
        self.report = report
        preview = "; ".join(
            f"{issue.code}" + (f" at row {issue.row}" if issue.row is not None else "")
            for issue in report.issues[:5]
        )
        super().__init__(f"CSV import rejected: {preview}")


def import_csv(
    path: str | Path,
    *,
    date_column: str,
    value_column: str,
    date_format: str,
    delimiter: str = ",",
    decimal: str = ".",
    instrument_column: str | None = None,
    instrument: str | None = None,
    missing_values: str = "reject",
    max_date: date | None = None,
    skip_rows: int = 0,
    encoding: str = "utf-8-sig",
) -> CSVImportResult:
    """Read one local series without guessing formats or silently repairing it.

    Header names and the instrument filter match exactly. Physical CSV line
    starts are retained; skip_rows skips that many physical preamble lines.
    The supported dialect follows Python csv.reader in strict mode, with
    doubled quote escaping; this is not a full RFC-conformance validator.
    Only empty/whitespace value cells are missing. Malformed numeric text,
    NaN/Inf text, malformed dates and duplicates are always errors. Zero and
    negative values are valid. Thousands separators are not supported.

    missing_values='skip' explicitly permits omitting blank values, with all
    original line numbers recorded. The report describes selected input
    before those omissions. It does not certify trading-session coverage.
    max_date excludes later rows after validation and records their line
    numbers; it is not inferred from the computer's date. XLSX is not
    supported by this reader. Invalid later observations still reject import.
    """
    for name, value in (("date_column", date_column), ("value_column", value_column), ("date_format", date_format)):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a nonempty string.")
    if date_column == value_column:
        raise ValueError("date_column and value_column must be different.")
    directives = date_format.replace("%%", "")
    if any(token in directives for token in ("%z", "%Z")):
        raise ValueError("date_format must not contain timezone directives (%z or %Z).")
    if "%Y" not in directives or "%d" not in directives or not any(token in directives for token in ("%m", "%b", "%B")):
        raise ValueError("date_format must specify a four-digit year, month and day (%Y, %m/%b/%B, %d).")
    if not isinstance(delimiter, str) or len(delimiter) != 1 or delimiter in "\r\n\0\"":
        raise ValueError("delimiter must be one non-newline, non-quote character.")
    if decimal not in (".", ","):
        raise ValueError("decimal must be '.' or ','.")
    if missing_values not in ("reject", "skip"):
        raise ValueError("missing_values must be 'reject' or 'skip'.")
    if not isinstance(skip_rows, int) or isinstance(skip_rows, bool) or skip_rows < 0:
        raise ValueError("skip_rows must be a nonnegative integer.")
    if max_date is not None and (not isinstance(max_date, date) or isinstance(max_date, datetime)):
        raise ValueError("max_date must be a datetime.date without a time.")
    if (instrument_column is None) != (instrument is None):
        raise ValueError("instrument_column and instrument must be provided together.")
    if instrument_column is not None:
        if not isinstance(instrument_column, str) or not instrument_column or instrument_column in (date_column, value_column):
            raise ValueError("instrument_column must be a distinct nonempty column name.")
        if not isinstance(instrument, str) or not instrument:
            raise ValueError("instrument must be a nonempty string.")

    numeric_pattern = re.compile(
        r"[+-]?(?:[0-9]+(?:" + re.escape(decimal) + r"[0-9]*)?|"
        + re.escape(decimal) + r"[0-9]+)(?:[eE][+-]?[0-9]+)?\Z"
    )
    selected_dates = []
    selected_values = []
    source_rows = []
    instrument_rows = []
    date_rows = []
    parsing_issues = []

    def reject(code, message, row=None):
        raise CSVImportError(QualityReport(len(source_rows), (QualityIssue(row, code, message),)))

    with Path(path).open("r", encoding=encoding, newline="") as stream:
        for _ in range(skip_rows):
            if stream.readline() == "":
                reject("missing_header", "No header after the selected preamble.")
        reader = csv.reader(stream, delimiter=delimiter, strict=True)
        try:
            headers = next(reader)
        except StopIteration:
            reject("missing_header", "CSV must contain a header.")
        except csv.Error:
            reject("malformed_csv", "CSV header could not be parsed.", skip_rows + 1)
        if not headers or any(not header.strip() for header in headers):
            reject("invalid_header", "Column names must be nonempty.", skip_rows + 1)
        if len(headers) != len(set(headers)):
            reject("duplicate_columns", "Column names must be unique.", skip_rows + 1)
        required = [date_column, value_column] + ([instrument_column] if instrument_column else [])
        if any(column not in headers for column in required):
            reject("missing_column", "A selected column is absent from the CSV header.")
        if instrument_column is None and "instrument_id" in headers:
            reject("missing_instrument_selection", "CSV with instrument_id requires an explicit instrument selection.")
        date_index, value_index = headers.index(date_column), headers.index(value_column)
        instrument_index = headers.index(instrument_column) if instrument_column else None
        while True:
            row_number = skip_rows + reader.line_num + 1
            try:
                cells = next(reader)
            except StopIteration:
                break
            except csv.Error:
                reject("malformed_csv", "CSV record could not be parsed.", row_number)
            if len(cells) != len(headers):
                reject("field_count", "Record width does not match the header.", row_number)
            if instrument_index is not None and cells[instrument_index] != instrument:
                instrument_rows.append(row_number)
                continue
            date_text = cells[date_index].strip()
            try:
                parsed_date = datetime.strptime(date_text, date_format)
            except ValueError:
                source_rows.append(row_number)
                parsing_issues.append(QualityIssue(row_number, "invalid_date", "Date does not match the selected format."))
                continue
            # Even a row beyond the cutoff must first be a valid daily date.
            if parsed_date.tzinfo is not None or parsed_date.time() != datetime.min.time():
                source_rows.append(row_number)
                parsing_issues.append(QualityIssue(row_number, "invalid_daily_date", "Dates must be timezone-naive daily observations at midnight."))
                continue
            source_rows.append(row_number)
            selected_dates.append(parsed_date)
            value_text = cells[value_index].strip()
            if not value_text:
                selected_values.append(float("nan"))
            elif numeric_pattern.fullmatch(value_text):
                parsed_value = float(value_text.replace(decimal, "."))
                if not math.isfinite(parsed_value):
                    parsing_issues.append(QualityIssue(row_number, "nonfinite_value", "Value is outside the supported finite numeric range."))
                selected_values.append(parsed_value)
            else:
                parsing_issues.append(QualityIssue(row_number, "invalid_numeric", "Value does not match the selected decimal format."))
                selected_values.append(float("nan"))
    if parsing_issues:
        raise CSVImportError(QualityReport(len(source_rows), tuple(parsing_issues)))
    try:
        frame = pd.DataFrame({"date": pd.to_datetime(selected_dates), "value": pd.Series(selected_values, dtype="float64")})
    except (ValueError, OverflowError):
        reject("unsupported_date_range", "Dates exceed the supported pandas range.")
    report = inspect_series(frame, source_rows=source_rows)
    if report.issues and (missing_values == "reject" or any(issue.code != "missing_value" for issue in report.issues)):
        raise CSVImportError(report)
    within_period = pd.Series(True, index=frame.index) if max_date is None else frame['date'].dt.date <= max_date
    date_rows = [row for row, within in zip(source_rows, within_period) if not within]
    missing_rows = {issue.row for issue in report.issues if issue.code == "missing_value"}
    skipped_rows = tuple(row for row, within in zip(source_rows, within_period) if within and row in missing_rows)
    keep = ~frame["value"].isna() & within_period
    prepared = frame.loc[keep].copy()
    kept_rows = [row for row, accepted in zip(source_rows, keep) if accepted]
    if prepared.empty:
        raise CSVImportError(QualityReport(len(frame), report.issues + (QualityIssue(None, "empty_data", "No observations remain after the selected missing-value policy."),)))
    prepared["_source_row"] = kept_rows
    prepared = prepared.sort_values("date", kind="stable").reset_index(drop=True)
    kept_rows = tuple(int(row) for row in prepared.pop("_source_row"))
    return CSVImportResult(
        frame=prepared, report=report, source_rows=kept_rows,
        skipped_missing_rows=skipped_rows,
        filtered_instrument_rows=tuple(instrument_rows), filtered_date_rows=tuple(date_rows),
    )
