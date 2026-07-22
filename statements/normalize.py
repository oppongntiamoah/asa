"""Matches parser-extracted ticker text against known Instrument rows."""
from instruments.models import Instrument

# Broker statements often print the company name rather than the exchange
# ticker — a small alias table bridges the common IC Securities cases.
# Extend as real statements reveal more variants.
TICKER_ALIASES = {
    "MTN GHANA": "MTNGH",
    "GHANA COMMERCIAL BANK": "GCB",
    "ENTERPRISE GROUP": "EGL",
    "TOTAL PETROLEUM GHANA": "TOTAL",
}


def match_instrument(raw_ticker_text: str) -> "Instrument | None":
    text = (raw_ticker_text or "").strip().upper()
    if not text:
        return None

    instrument = Instrument.objects.filter(ticker__iexact=text).first()
    if instrument:
        return instrument

    alias_ticker = TICKER_ALIASES.get(text)
    if alias_ticker:
        return Instrument.objects.filter(ticker__iexact=alias_ticker).first()

    return Instrument.objects.filter(name__iexact=text).first()


def rows_to_extracted_transactions(statement, raw_rows):
    """Converts parser RawStatementRow objects into unsaved ExtractedTransaction instances."""
    from .models import ExtractedTransaction

    extracted = []
    for order, row in enumerate(raw_rows):
        instrument = match_instrument(row.raw_ticker_text)
        confidence = row.confidence
        notes = row.parse_notes

        if instrument is None:
            confidence = "LOW"
            notes = (notes + "; " if notes else "") + f"no matching instrument for '{row.raw_ticker_text}'"

        extracted.append(
            ExtractedTransaction(
                statement=statement,
                raw_ticker_text=row.raw_ticker_text,
                matched_instrument=instrument,
                transaction_type=row.transaction_type,
                quantity=row.quantity,
                price_per_share=row.price_per_share,
                fees=row.fees,
                trade_date=row.trade_date,
                confidence=confidence,
                parse_notes=notes,
                row_order=order,
            )
        )
    return extracted
