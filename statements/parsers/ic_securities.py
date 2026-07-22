"""
Parser for IC Securities statements. Uses pdfplumber since IC statements are
text-based PDFs (not scanned images) as of the broker's current export
format — revisit if that changes (would need OCR).

NOTE: the expected column layout below is a best-guess skeleton pending
verification against real sample statements (see PRODUCT_DESIGN.md §9,
week 6) — get 3-5 real anonymized IC statements before trusting this in
production, and adjust _parse_row's column order to match.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pdfplumber

from .base import BrokerParser, ExtractionResult, RawStatementRow

DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")


class ICSecuritiesParser(BrokerParser):
    broker_code = "IC_SECURITIES"

    def extract(self) -> ExtractionResult:
        result = ExtractionResult()

        try:
            with pdfplumber.open(self.file_obj) as pdf:
                if not pdf.pages:
                    raise ValueError("Empty PDF")
                for page in pdf.pages:
                    for table in page.extract_tables():
                        self._parse_table(table, result)
        except Exception as exc:
            raise ValueError(f"Could not read PDF as IC Securities statement: {exc}") from exc

        if not result.rows:
            result.warnings.append(
                "No transaction rows found — layout may not match expected IC Securities format."
            )
        return result

    def _parse_table(self, table, result: ExtractionResult) -> None:
        if not table:
            return
        _header, *body_rows = table
        for row in body_rows:
            if not row or not any(row):
                continue
            result.rows.append(self._parse_row(row))

    def _parse_row(self, row) -> RawStatementRow:
        """
        Expected IC Securities column order:
        [Trade Date, Description/Ticker, Buy/Sell, Quantity, Price, Fees, Net Amount]
        """
        try:
            cells = [c.strip() if c else "" for c in row]
            trade_date_str, ticker_text, side, qty_str, price_str, fees_str = cells[:6]

            notes = []
            trade_date = self._parse_date(trade_date_str)
            if trade_date is None:
                notes.append("unparseable trade date")

            quantity = self._parse_decimal(qty_str)
            if quantity is None:
                notes.append("unparseable quantity")

            price = self._parse_decimal(price_str)
            if price is None:
                notes.append("unparseable price")

            fees = self._parse_decimal(fees_str) or Decimal("0")

            txn_type = "BUY" if "buy" in side.lower() else ("SELL" if "sell" in side.lower() else "")
            if not txn_type:
                notes.append(f"unrecognized side '{side}'")

            return RawStatementRow(
                raw_ticker_text=ticker_text,
                transaction_type=txn_type,
                quantity=quantity,
                price_per_share=price,
                fees=fees,
                trade_date=trade_date,
                confidence="LOW" if notes else "HIGH",
                parse_notes="; ".join(notes),
            )
        except (IndexError, ValueError):
            return RawStatementRow(
                raw_ticker_text=" ".join(c for c in row if c) if row else "",
                transaction_type="",
                quantity=None,
                price_per_share=None,
                fees=Decimal("0"),
                trade_date=None,
                confidence="LOW",
                parse_notes="row did not match expected column layout",
            )

    @staticmethod
    def _parse_date(value: str):
        if not DATE_RE.fullmatch(value):
            return None
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _parse_decimal(value: str):
        cleaned = value.replace(",", "").replace("GHS", "").strip()
        try:
            return Decimal(cleaned) if cleaned else None
        except InvalidOperation:
            return None
