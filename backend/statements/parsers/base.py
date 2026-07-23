from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class RawStatementRow:
    """What every parser must produce, regardless of broker PDF layout."""

    raw_ticker_text: str
    transaction_type: str  # "BUY" or "SELL" (or "" if unrecognized)
    quantity: "Decimal | None"
    price_per_share: "Decimal | None"
    fees: Decimal
    trade_date: "date | None"
    confidence: str  # "HIGH" or "LOW"
    parse_notes: str = ""


@dataclass
class ExtractionResult:
    rows: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class BrokerParser(ABC):
    """
    One subclass per broker. Each broker's PDF layout differs enough
    (column order, headers, date formats, fee line items) that a shared
    "generic PDF table parser" fights every broker instead of fitting any
    of them — hence one class per broker rather than a config-driven
    generic parser.
    """

    broker_code: str  # must match StatementUpload.BROKER_CHOICES

    def __init__(self, file_obj):
        self.file_obj = file_obj

    @abstractmethod
    def extract(self) -> ExtractionResult:
        """Parse self.file_obj and return structured rows. Must not raise
        for row-level issues (flag as LOW confidence instead) — only raise
        for whole-document failures (unreadable/wrong-broker PDF), which the
        caller catches and routes to StatementUpload.FAILED."""
        raise NotImplementedError
