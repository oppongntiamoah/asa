"""
Parses a daily GSE closing-price CSV into PriceBar rows.

Matches the actual GSE "Daily Shares & ETFs" export format, e.g.:

    "Daily Date","Share Code","Year High (GH¢)","Year Low (GH¢)",
    "Previous Closing Price - VWAP (GH¢)","Opening Price (GH¢)",
    "Last Transaction Price (GH¢)","Closing Price - VWAP (GH¢)",
    "Price Change (GH¢)","Closing Bid Price (GH¢)","Closing Offer Price (GH¢)",
    "Total Shares Traded","Total Value Traded (GH¢)"

Notably: the trade date is a per-row column (not supplied at upload time),
numbers use comma thousands-separators ("1,983,924.88"), and some ticker
codes carry GSE annotation asterisks (e.g. "PBC**", "**ALW**") that must be
stripped before matching against Instrument.ticker. The feed has no daily
high/low (only Year High/Low, which is a different figure) — high_price/
low_price are left null from this source.

Unknown tickers are skipped and logged as errors rather than silently
creating placeholder Instrument rows — a typo'd or newly-listed ticker in
the CSV should never invent a phantom listed company; add it to Instrument
via admin first.
"""
import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from instruments.models import Instrument, PriceBar, PriceIngestBatch

TICKER_ANNOTATION_RE = re.compile(r"[^A-Z0-9]")

# Header aliases: several plausible spellings map to the same logical field,
# since GSE's export header wording has shifted before and may again.
DATE_HEADERS = {"daily date", "date"}
TICKER_HEADERS = {"share code", "ticker", "symbol"}
OPEN_HEADERS = {"opening price (gh¢)", "opening price", "open"}
CLOSE_HEADERS = {"closing price - vwap (gh¢)", "closing price (vwap)", "closing price", "close"}
VOLUME_HEADERS = {"total shares traded", "volume"}


@dataclass
class IngestResult:
    row_count: int = 0
    error_count: int = 0
    errors: list[str] = field(default_factory=list)
    batch: PriceIngestBatch | None = None


def _clean_ticker(raw: str) -> str:
    return TICKER_ANNOTATION_RE.sub("", (raw or "").strip().upper())


def _parse_decimal(value: str) -> Decimal | None:
    cleaned = (value or "").replace(",", "").replace("GHS", "").replace("GH¢", "").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_int(value: str) -> int | None:
    cleaned = (value or "").replace(",", "").strip()
    return int(cleaned) if cleaned.lstrip("-").isdigit() else None


def _parse_row_date(value: str) -> date | None:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((value or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def _resolve_columns(fieldnames: list[str]) -> dict:
    normalized = {name.strip().lower(): name for name in fieldnames or []}

    def find(candidates):
        for candidate in candidates:
            if candidate in normalized:
                return normalized[candidate]
        return None

    return {
        "date": find(DATE_HEADERS),
        "ticker": find(TICKER_HEADERS),
        "open": find(OPEN_HEADERS),
        "close": find(CLOSE_HEADERS),
        "volume": find(VOLUME_HEADERS),
    }


def ingest_price_csv(file_obj, trade_date: date | None = None, uploaded_by=None, source: str = "csv_upload") -> IngestResult:
    """
    Reads file_obj as CSV and upserts one PriceBar per recognized ticker.
    trade_date is used only as a fallback when a row has no parseable date
    of its own — the real GSE export carries the date per row, so the
    common case ignores this argument entirely.
    """
    raw = file_obj.read()
    text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
    reader = csv.DictReader(io.StringIO(text))
    columns = _resolve_columns(reader.fieldnames)

    result = IngestResult()
    instruments_by_ticker = {i.ticker.upper(): i for i in Instrument.objects.all()}
    batch_dates = set()

    if not columns["ticker"] or not columns["close"]:
        result.errors.append(
            "CSV is missing a recognizable ticker or closing price column — check the header row."
        )
        result.batch = PriceIngestBatch.objects.create(
            source=source, trade_date=trade_date or date.today(),
            row_count=0, error_count=1, error_log=result.errors[0], uploaded_by=uploaded_by,
        )
        return result

    for line_number, row in enumerate(reader, start=2):
        ticker = _clean_ticker(row.get(columns["ticker"], ""))
        if not ticker:
            continue
        result.row_count += 1

        row_date = _parse_row_date(row.get(columns["date"], "")) if columns["date"] else None
        effective_date = row_date or trade_date
        if effective_date is None:
            result.error_count += 1
            result.errors.append(f"line {line_number}: no trade date found for '{ticker}'")
            continue
        batch_dates.add(effective_date)

        instrument = instruments_by_ticker.get(ticker)
        if instrument is None:
            result.error_count += 1
            result.errors.append(f"line {line_number}: unknown ticker '{ticker}'")
            continue

        close_price = _parse_decimal(row.get(columns["close"], ""))
        if close_price is None:
            result.error_count += 1
            result.errors.append(f"line {line_number}: missing/invalid close price for '{ticker}'")
            continue

        PriceBar.objects.update_or_create(
            instrument=instrument,
            trade_date=effective_date,
            defaults={
                "close_price": close_price,
                "open_price": _parse_decimal(row.get(columns["open"], "")) if columns["open"] else None,
                "high_price": None,  # not present in the GSE daily export (only annual high/low is)
                "low_price": None,
                "volume": _parse_int(row.get(columns["volume"], "")) if columns["volume"] else None,
                "source": source,
            },
        )

    result.batch = PriceIngestBatch.objects.create(
        source=source,
        trade_date=trade_date or (max(batch_dates) if batch_dates else date.today()),
        row_count=result.row_count,
        error_count=result.error_count,
        error_log="\n".join(result.errors),
        uploaded_by=uploaded_by,
    )
    return result
