"""
Parser for IC Securities "Account Statement" PDFs.

Real IC statements are NOT a bordered table — pdfplumber's extract_tables()
returns fragmented single-row garbage against them (verified against a real
sample). The actual "Transaction History" section is a narrative cash ledger:
one line per date with a free-text description, ending in Credit/Debit
columns. Only a subset of lines represent buy/sell equity transactions,
e.g.:

    29/12/2025 Bought 16 MTNGH at 4.20 for a consideration of 67.20 and
    total charges of 1.68                                    0.00  -68.88

Everything else on the statement — "Funding for Purchase of shares",
"Transfer/Payout to client payment account", commission lines, MoMo/bank
contributions, withdrawals — is cash-ledger noise with no bearing on
holdings, and is deliberately NOT surfaced for review; importing every cash
movement as a "transaction to confirm" would bury the handful of real ones.

Two categories of *equity-relevant* activity don't fit the "Bought X TICKER
at Y" sentence, though, and silently dropping them would misrepresent the
user's holdings (verified against the same real sample):
  - IPO / new-issue allocations, e.g. "Purchase of Shares (IPO) - MTNGH"
    paired with "New Issue / IPO 10 of MTNGH" on a separate line.
  - IPO subscription debits/refunds, e.g. "Debit for Kasapreko IPO
    subscription" — cash reserved for an application; may or may not have
    become shares, and the ticker isn't always spelled in caps in the
    description (the sample has "Kasapreko", not "KASA").
  - In-kind transfers into the account, e.g. "Deposited 4,056 of KPLC".
These are emitted as LOW-confidence stub rows with the original line
preserved in parse_notes, so the user completes them manually on the review
screen rather than losing the activity entirely.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

import pdfplumber

from .base import BrokerParser, ExtractionResult, RawStatementRow

LINE_RE = re.compile(r"^(?P<date>\d{2}/\d{2}/\d{4})\s+(?P<rest>.*)$")

TRADE_RE = re.compile(
    r"(?P<side>Bought|Sold)\s+(?P<qty>[\d,]+)\s+(?P<ticker>[A-Z]{2,10})\s+at\s+"
    r"(?P<price>\d*\.\d+|\d+)\s+for a consideration of\s+(?P<consideration>[\d,.]+)"
    r"\s+and total charges of\s+(?P<fees>[\d,.]+)",
    re.IGNORECASE,
)

# Lines mentioning these are equity-relevant even when they don't match
# TRADE_RE, and get flagged for manual review rather than dropped.
EQUITY_KEYWORDS_RE = re.compile(
    r"\b(IPO|New Issue|Deposited|Rights Issue|Bonus Shares|Subscription)\b", re.IGNORECASE
)

POSSIBLE_TICKER_RE = re.compile(r"\b[A-Z]{2,10}\b")
TICKER_GUESS_STOPWORDS = {"OF", "IC", "GHS", "IPO", "NRT", "ACH", "EFTRB", "EFTMB"}


class ICSecuritiesParser(BrokerParser):
    broker_code = "IC_SECURITIES"

    def extract(self) -> ExtractionResult:
        result = ExtractionResult()
        found_transaction_history = False

        try:
            with pdfplumber.open(self.file_obj) as pdf:
                if not pdf.pages:
                    raise ValueError("Empty PDF")
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if "Transaction History" not in text:
                        continue  # e.g. the "Account Portfolio" summary page — not the ledger
                    found_transaction_history = True
                    self._parse_page(text, result)
        except Exception as exc:
            raise ValueError(f"Could not read PDF as IC Securities statement: {exc}") from exc

        if not found_transaction_history:
            raise ValueError(
                "No 'Transaction History' section found — this doesn't look like an "
                "IC Securities account statement."
            )
        if not result.rows:
            result.warnings.append("No transaction rows found in the Transaction History section.")
        return result

    def _parse_page(self, text: str, result: ExtractionResult) -> None:
        for raw_line in text.splitlines():
            line_match = LINE_RE.match(raw_line.strip())
            if not line_match:
                continue  # headers, footers, disclaimers, running totals — none start with a date

            trade_date = self._parse_date(line_match.group("date"))
            description = line_match.group("rest")

            trade_match = TRADE_RE.search(description)
            if trade_match:
                result.rows.append(self._row_from_trade(trade_date, trade_match))
            elif EQUITY_KEYWORDS_RE.search(description):
                result.rows.append(self._row_from_unmatched_equity_line(trade_date, description))
            # else: ordinary cash-ledger line (funding, transfer, commission, contribution) — skip

    def _row_from_trade(self, trade_date, match) -> RawStatementRow:
        side = "BUY" if match.group("side").lower() == "bought" else "SELL"
        return RawStatementRow(
            raw_ticker_text=match.group("ticker"),
            transaction_type=side,
            quantity=self._parse_decimal(match.group("qty")),
            price_per_share=self._parse_decimal(match.group("price")),
            fees=self._parse_decimal(match.group("fees")) or Decimal("0"),
            trade_date=trade_date,
            confidence="HIGH",
        )

    def _row_from_unmatched_equity_line(self, trade_date, description) -> RawStatementRow:
        ticker_guess = ""
        for word in POSSIBLE_TICKER_RE.findall(description):
            if word not in TICKER_GUESS_STOPWORDS:
                ticker_guess = word
                break
        return RawStatementRow(
            raw_ticker_text=ticker_guess,
            transaction_type="",
            quantity=None,
            price_per_share=None,
            fees=Decimal("0"),
            trade_date=trade_date,
            confidence="LOW",
            parse_notes=f'possible IPO/transfer activity, not auto-parsed — verify and complete manually: "{description.strip()}"',
        )

    @staticmethod
    def _parse_date(value: str):
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _parse_decimal(value: str):
        cleaned = (value or "").replace(",", "").strip()
        try:
            return Decimal(cleaned) if cleaned else None
        except InvalidOperation:
            return None
