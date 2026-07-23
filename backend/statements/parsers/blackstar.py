"""
Parser for Black Star Advisors "Client Account Statement" (valuation report)
PDFs.

Structurally the opposite problem from IC Securities: pdfplumber's
extract_tables() works cleanly here (real gridlines), verified against a
real sample — the "PORTFOLIO HOLDINGS" page is a sequence of per-asset-class
tables shaped like:

    ['Cash']                                              <- section header (single cell)
    ['Description (ID/ISIN)', 'Quantity', 'Yield', 'Price', 'Total Cost', 'Value', 'Currency']
    ['Cash GHS', '1,000', '-', '1.0000', '1,000.00', '1,000.00', 'GHS']
    ['Total', None, None, None, None, '1,000.00', '']

But the *document type* is fundamentally different from a transaction
ledger: it's a point-in-time valuation (current quantity + average cost per
holding), not a record of individual buy/sell events with dates. There is
no trade_date, no per-lot price, and no way to recover realized P&L history
from this alone.

Rather than fabricate a trade_date (e.g. the statement's "as of" date) and
present a holdings-snapshot row as if it were a real transaction — which
would silently corrupt dividend-eligibility and realized P&L math built on
trade_date — every non-cash holding row is emitted as a LOW-confidence stub
with quantity and average cost (Total Cost / Quantity, which is more
reliable than the "Price" column — that's the *current* market price, not
what was paid) pre-filled, and transaction_type/trade_date left for the
user to complete on the review screen. Cash rows are skipped entirely;
SikaTrack tracks equity positions, not brokerage cash balances.
"""
from decimal import Decimal, InvalidOperation

import pdfplumber

from .base import BrokerParser, ExtractionResult, RawStatementRow

HOLDINGS_HEADER = "PORTFOLIO HOLDINGS"
COLUMN_HEADER_FIRST_CELL = "Description (ID/ISIN)"


def _parse_decimal(value) -> "Decimal | None":
    cleaned = (value or "").replace(",", "").strip()
    if not cleaned or cleaned == "-":
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


class BlackstarParser(BrokerParser):
    broker_code = "BLACKSTAR"

    def extract(self) -> ExtractionResult:
        result = ExtractionResult()
        found_holdings_page = False

        try:
            with pdfplumber.open(self.file_obj) as pdf:
                if not pdf.pages:
                    raise ValueError("Empty PDF")
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if HOLDINGS_HEADER not in text:
                        continue
                    found_holdings_page = True
                    self._parse_holdings_tables(page.extract_tables(), result)
        except Exception as exc:
            raise ValueError(f"Could not read PDF as a Black Star Advisors statement: {exc}") from exc

        if not found_holdings_page:
            raise ValueError(
                "No 'PORTFOLIO HOLDINGS' section found — this doesn't look like a "
                "Black Star Advisors account statement."
            )
        if not result.rows:
            result.warnings.append(
                "No equity holdings found — this account may be entirely in cash as of the statement date."
            )
        return result

    def _parse_holdings_tables(self, tables, result: ExtractionResult) -> None:
        current_section = None
        for table in tables:
            for row in table:
                cells = [c.strip() if c else "" for c in row]
                first_cell = cells[0] if cells else ""

                if all(not c for c in cells[1:]) and first_cell:
                    current_section = first_cell  # e.g. "Cash", "Equities", "Fixed Income"
                    continue
                if first_cell == COLUMN_HEADER_FIRST_CELL or first_cell == "Total" or not first_cell:
                    continue
                if current_section and current_section.lower() == "cash":
                    continue  # cash balance, not a security — out of scope for the portfolio tracker

                result.rows.append(self._row_from_holding(cells))

    def _row_from_holding(self, cells) -> RawStatementRow:
        description = cells[0] if cells else ""
        ticker_guess = description.split()[0] if description.split() else ""

        quantity = _parse_decimal(cells[1]) if len(cells) > 1 else None
        total_cost = _parse_decimal(cells[4]) if len(cells) > 4 else None
        avg_cost_per_share = (total_cost / quantity) if quantity and total_cost is not None else None

        return RawStatementRow(
            raw_ticker_text=ticker_guess,
            transaction_type="",
            quantity=quantity,
            price_per_share=avg_cost_per_share,
            fees=Decimal("0"),
            trade_date=None,
            confidence="LOW",
            parse_notes=(
                f'holdings snapshot, not a transaction — "{description}": quantity and average cost are '
                f"pre-filled from the statement, but pick a transaction type and the date you actually "
                f"bought these shares (or your best estimate) before confirming"
            ),
        )
