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

Note the wrap: the "...and total charges of X" clause lands on the next
physical PDF line, not the dated line itself — confirmed by generating a
real PDF with the description split across two drawString calls and
running it through pdfplumber (a hand-typed single-line test string had
been hiding this). Since the continuation line doesn't start with a date,
_parse_page() would otherwise skip it as unrecognized boilerplate and the
TRADE_RE match against the dated line alone would fail, silently dropping
a real trade. BOUGHT_SOLD_START_RE detects this specific case (a
Bought/Sold line that doesn't fully match TRADE_RE) and pulls in the next
line before giving up on it.

Everything else on the statement — "Funding for Purchase of shares",
"Transfer/Payout to client payment account", commission lines, MoMo/bank
contributions, withdrawals — is cash-ledger noise with no bearing on
holdings, and is deliberately NOT surfaced for review; importing every cash
movement as a "transaction to confirm" would bury the handful of real ones.

IPO / new-issue allocations are the one category of *equity-relevant*
activity that doesn't fit the "Bought X TICKER at Y" sentence, and — unlike
ordinary cash noise — dropping them would misrepresent the user's holdings.
They print as two SEPARATE ledger lines for the same allocation (verified
against a real sample, MTN Ghana's 2018 IPO):

    04/09/2018 Purchase of Shares (IPO) - MTNGH                7.50   0.00
    04/09/2018 New Issue / IPO 10 of MTNGH

The first carries the amount debited (7.50), the second the share count
(10) — neither line alone has enough to build a real transaction (price
per share = 7.50 / 10 = 0.75, which is exactly MTNGH's real IPO price).
_merge_ipo_fragments() pairs same-date/same-ticker fragments across the
whole document and reconstructs one complete BUY row from the pair, so it
survives normalize.py's "missing a field" exclusion instead of landing on
the review screen as two dead stub rows the user has to fill in from the
original PDF by hand. A fragment that can't be unambiguously paired (no
match, or more than one candidate for the same date+ticker) still falls
back to a LOW-confidence stub with the original line preserved in
parse_notes — nothing is silently dropped or guessed at over-confidently.

Other in-kind, non-IPO transfers (e.g. "Deposited 4,056 of KPLC") don't
carry a quantity+amount pair to reconstruct from, so they stay stub rows.
"""
import re
from collections import defaultdict
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

# Matches just the start of a trade sentence, used to detect a Bought/Sold
# line whose "...and total charges of X" clause got wrapped onto the next
# physical PDF line (real statements do this — see module docstring) so
# the continuation can be pulled in instead of the row silently vanishing.
BOUGHT_SOLD_START_RE = re.compile(r"^\s*(Bought|Sold)\b", re.IGNORECASE)

# The two IPO-allocation line shapes — see module docstring. Each only
# carries half of what's needed for a real transaction; _merge_ipo_fragments
# stitches same-date/same-ticker pairs together after the whole document has
# been scanned.
IPO_PURCHASE_RE = re.compile(
    r"Purchase of Shares\s*\(IPO\)\s*-\s*(?P<ticker>[A-Z]{2,10})\b.*?(?P<amount>[\d,]+\.\d{2})",
    re.IGNORECASE,
)
IPO_ALLOTMENT_RE = re.compile(
    r"New Issue\s*/\s*IPO\s+(?P<qty>[\d,]+)\s+of\s+(?P<ticker>[A-Z]{2,10})",
    re.IGNORECASE,
)

# Lines mentioning these are equity-relevant even when they don't match
# TRADE_RE or the IPO patterns above, and get flagged for manual review
# rather than dropped.
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
        ipo_amounts = defaultdict(list)  # (date, ticker) -> [Decimal amount, ...]
        ipo_qtys = defaultdict(list)  # (date, ticker) -> [Decimal quantity, ...]

        try:
            with pdfplumber.open(self.file_obj) as pdf:
                if not pdf.pages:
                    raise ValueError("Empty PDF")
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if "Transaction History" not in text:
                        continue  # e.g. the "Account Portfolio" summary page — not the ledger
                    found_transaction_history = True
                    self._parse_page(text, result, ipo_amounts, ipo_qtys)
        except Exception as exc:
            raise ValueError(f"Could not read PDF as IC Securities statement: {exc}") from exc

        if not found_transaction_history:
            raise ValueError(
                "No 'Transaction History' section found — this doesn't look like an "
                "IC Securities account statement."
            )

        self._merge_ipo_fragments(ipo_amounts, ipo_qtys, result)

        if not result.rows:
            result.warnings.append("No transaction rows found in the Transaction History section.")
        return result

    def _parse_page(self, text: str, result: ExtractionResult, ipo_amounts: dict, ipo_qtys: dict) -> None:
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line_match = LINE_RE.match(lines[i].strip())
            if not line_match:
                i += 1
                continue  # headers, footers, disclaimers, running totals — none start with a date

            trade_date = self._parse_date(line_match.group("date"))
            description = line_match.group("rest")

            # A long "Bought/Sold ... for a consideration of ... and total
            # charges of ..." sentence can wrap onto the next physical PDF
            # line (verified against a real sample — see module docstring).
            # The wrapped continuation never starts with its own date, so
            # pull it in before giving up on this being a trade line —
            # otherwise a real trade silently vanishes instead of landing
            # on the review screen.
            if BOUGHT_SOLD_START_RE.match(description) and not TRADE_RE.search(description):
                if i + 1 < len(lines) and not LINE_RE.match(lines[i + 1].strip()):
                    description = description + " " + lines[i + 1].strip()
                    i += 1

            trade_match = TRADE_RE.search(description)
            ipo_purchase_match = None if trade_match else IPO_PURCHASE_RE.search(description)
            ipo_allotment_match = None if (trade_match or ipo_purchase_match) else IPO_ALLOTMENT_RE.search(description)

            if trade_match:
                result.rows.append(self._row_from_trade(trade_date, trade_match))
            elif ipo_purchase_match:
                key = (trade_date, ipo_purchase_match.group("ticker").upper())
                amount = self._parse_decimal(ipo_purchase_match.group("amount"))
                if amount is not None:
                    ipo_amounts[key].append(amount)
            elif ipo_allotment_match:
                key = (trade_date, ipo_allotment_match.group("ticker").upper())
                qty = self._parse_decimal(ipo_allotment_match.group("qty"))
                if qty is not None:
                    ipo_qtys[key].append(qty)
            elif EQUITY_KEYWORDS_RE.search(description):
                result.rows.append(self._row_from_unmatched_equity_line(trade_date, description))
            # else: ordinary cash-ledger line (funding, transfer, commission, contribution) — skip

            i += 1

    def _merge_ipo_fragments(self, ipo_amounts: dict, ipo_qtys: dict, result: ExtractionResult) -> None:
        for key in set(ipo_amounts) | set(ipo_qtys):
            trade_date, ticker = key
            amounts = ipo_amounts.get(key, [])
            qtys = ipo_qtys.get(key, [])

            if len(amounts) == 1 and len(qtys) == 1 and qtys[0]:
                total_amount, quantity = amounts[0], qtys[0]
                result.rows.append(RawStatementRow(
                    raw_ticker_text=ticker,
                    transaction_type="BUY",
                    quantity=quantity,
                    price_per_share=(total_amount / quantity),
                    fees=Decimal("0"),
                    trade_date=trade_date,
                    confidence="LOW",
                    parse_notes=(
                        f"IPO allocation reconstructed from two statement lines: "
                        f"GHS {total_amount} for {quantity} shares. Verify against your statement."
                    ),
                ))
                continue

            # Ambiguous (no match, or more than one candidate for this
            # date+ticker) — don't guess which amount pairs with which
            # quantity; fall back to a stub per fragment so nothing is
            # silently dropped or mis-paired.
            for amount in amounts:
                result.rows.append(RawStatementRow(
                    raw_ticker_text=ticker, transaction_type="", quantity=None, price_per_share=None,
                    fees=Decimal("0"), trade_date=trade_date, confidence="LOW",
                    parse_notes=(
                        f"IPO purchase debit of GHS {amount} for {ticker} — couldn't confidently "
                        f"match to a share allotment line; verify and complete manually."
                    ),
                ))
            for qty in qtys:
                result.rows.append(RawStatementRow(
                    raw_ticker_text=ticker, transaction_type="BUY", quantity=qty, price_per_share=None,
                    fees=Decimal("0"), trade_date=trade_date, confidence="LOW",
                    parse_notes=(
                        f"IPO allotment of {qty} shares of {ticker} — couldn't confidently match to "
                        f"a purchase amount line; verify the price and complete manually."
                    ),
                ))

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
