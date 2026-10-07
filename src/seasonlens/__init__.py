"""SeasonLens: inspectable calculations for seasonal time series."""

from .monthly import MonthlyResult, aggregate_monthly
from .quality import QualityIssue, QualityReport, inspect_series
from .csv_import import CSVImportError, CSVImportResult, import_csv
from .seasonal import SeasonalResult, analyze_seasonality
from .report import render_seasonal_report
from .analytics import (moving_averages, monthly_returns, normalized_seasonality,
                        partial_month_comparison, convert_eur_to_pln)
from .storage import (SeriesMetadata, initialize_database, upsert_series,
                      upsert_many, read_series, list_series, freshness,
                      export_series, backup_database)
from .dashboard import render_dashboard
from .comparison import technical_analysis, recent_year_prices

__all__ = [
    "MonthlyResult", "aggregate_monthly", "QualityIssue", "QualityReport",
    "inspect_series", "CSVImportError", "CSVImportResult", "import_csv",
    "SeasonalResult", "analyze_seasonality", "render_seasonal_report",
    "moving_averages", "monthly_returns", "normalized_seasonality",
    "partial_month_comparison", "convert_eur_to_pln", "SeriesMetadata",
    "initialize_database", "upsert_series", "upsert_many", "read_series",
    "list_series", "freshness", "export_series", "backup_database", "render_dashboard", "technical_analysis", "recent_year_prices",
]
