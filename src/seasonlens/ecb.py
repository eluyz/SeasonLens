"""Direct ECB reference-rate XML; vendor-close histories remain separate."""

from datetime import date, datetime
import math
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

import pandas as pd

from .storage import SeriesMetadata, upsert_many

DAILY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
RECENT_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
HISTORY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml"
ECB_PROVENANCE = "ECB euro foreign exchange reference rates; USD_PLN derived from same-date PLN per EUR / USD per EUR."
MAX_BYTES = 16 * 1024 * 1024
ECB_NAMESPACE = "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"


def parse_ecb_xml(content: bytes | str) -> dict[str, pd.DataFrame]:
    """Require both positive finite PLN/EUR and USD/EUR quotes on every date."""
    if not isinstance(content, (bytes, str)) or len(content) > MAX_BYTES:
        raise ValueError("ECB XML content is invalid or exceeds the size limit.")
    upper = content.upper()
    if (b"<!DOCTYPE" in upper or b"<!ENTITY" in upper) if isinstance(upper, bytes) else ("<!DOCTYPE" in upper or "<!ENTITY" in upper):
        raise ValueError("XML document types and entities are unsupported.")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError("ECB XML is malformed.") from exc
    if root.tag != "{http://www.gesmes.org/xml/2002-08-01}Envelope":
        raise ValueError("ECB XML must use the expected reference-rate envelope.")
    rows = []
    seen = set()
    for node in root.iter():
        if node.tag != f"{{{ECB_NAMESPACE}}}Cube" or "time" not in node.attrib:
            continue
        try:
            day = date.fromisoformat(node.attrib["time"])
            if node.attrib["time"] != day.isoformat():
                raise ValueError
        except ValueError as exc:
            raise ValueError("ECB observation date is invalid.") from exc
        if day in seen:
            raise ValueError("ECB XML contains duplicate observation dates.")
        seen.add(day)
        quotes = {}
        for child in node:
            if child.tag != f"{{{ECB_NAMESPACE}}}Cube":
                continue
            currency = child.attrib.get("currency")
            if currency not in ("PLN", "USD"):
                continue
            if currency in quotes:
                raise ValueError("ECB XML contains a duplicate currency quote.")
            try:
                value = float(child.attrib["rate"])
            except (KeyError, ValueError) as exc:
                raise ValueError("ECB rate is invalid.") from exc
            if not math.isfinite(value) or value <= 0:
                raise ValueError("ECB rates must be positive and finite.")
            quotes[currency] = value
        if set(quotes) != {"PLN", "USD"}:
            raise ValueError("ECB date lacks matching PLN and USD reference rates.")
        derived = quotes["PLN"] / quotes["USD"]
        if not math.isfinite(derived) or derived <= 0:
            raise ValueError("Derived USD_PLN exceeds the supported numeric range.")
        rows.append((day, quotes["PLN"], quotes["USD"], derived))
    if not rows:
        raise ValueError("ECB XML contains no reference-rate observations.")
    rows.sort()
    try:
        days = pd.to_datetime([item[0] for item in rows])
    except (ValueError, OverflowError) as exc:
        raise ValueError("ECB dates exceed the supported datetime range.") from exc
    return {name: pd.DataFrame({"date": days, "value": [item[position] for item in rows]}) for name, position in (("EUR_PLN", 1), ("EUR_USD", 2), ("USD_PLN", 3))}


def fetch_ecb_rates(*, history: bool = False, timeout: float = 20) -> dict[str, pd.DataFrame]:
    if not isinstance(history, bool):
        raise ValueError("history must be boolean.")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number.")
    # A rolling 90-day refresh catches missed nightly runs and recent revisions.
    request = Request(HISTORY_URL if history else RECENT_URL, headers={"User-Agent": "SeasonLens/0.0.1"})
    with urlopen(request, timeout=timeout) as response:
        content = response.read(MAX_BYTES + 1)
    return parse_ecb_xml(content)


def ecb_metadata() -> dict[str, SeriesMetadata]:
    return {
        "EUR_PLN": SeriesMetadata("EUR_PLN", "EUR/PLN — ECB reference", "PLN per EUR", "ECB_REFERENCE", "ECB daily reference: PLN per 1 EUR", ECB_PROVENANCE),
        "EUR_USD": SeriesMetadata("EUR_USD", "EUR/USD — ECB reference", "USD per EUR", "ECB_REFERENCE", "ECB daily reference: USD per 1 EUR", ECB_PROVENANCE),
        "USD_PLN": SeriesMetadata("USD_PLN", "USD/PLN — ECB derived", "PLN per USD", "ECB_REFERENCE", "Same-date derived PLN per 1 USD: EUR_PLN / EUR_USD", ECB_PROVENANCE),
    }


def update_ecb(path, *, history: bool = False, timeout: float = 20, as_of: date | None = None):
    if as_of is None:
        as_of = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    if not isinstance(as_of, date) or isinstance(as_of, datetime):
        raise ValueError("ECB update cutoff must be a datetime.date.")
    frames = fetch_ecb_rates(history=history, timeout=timeout)
    if any((frame["date"].dt.date > as_of).any() for frame in frames.values()):
        raise ValueError("ECB response contains observations after the update cutoff.")
    metadata = ecb_metadata()
    return upsert_many(path, [(metadata[name], frame) for name, frame in frames.items()])
