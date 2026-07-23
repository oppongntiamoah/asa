import logging

from .models import ExtractedTransaction, StatementUpload
from .normalize import rows_to_extracted_transactions
from .parsers.registry import get_parser_class

logger = logging.getLogger(__name__)


def parse_statement(statement_id: int):
    """
    Enqueued via Django-Q2 right after upload so the request/response cycle
    isn't blocked on PDF extraction. See PRODUCT_DESIGN.md §4.1.
    """
    statement = StatementUpload.objects.get(pk=statement_id)
    statement.status = StatementUpload.PARSING
    statement.save(update_fields=["status"])

    try:
        parser_class = get_parser_class(statement.broker)
        parser = parser_class(statement.file)
        result = parser.extract()
    except Exception as exc:
        logger.exception("Statement parse failed for statement_id=%s", statement_id)
        statement.status = StatementUpload.FAILED
        statement.parse_error = (
            "We couldn't process this file — it may be password-protected, a scanned "
            "image, or not match the expected IC Securities layout. Manual entry is "
            "always available from Add Transaction."
        )
        statement.save(update_fields=["status", "parse_error"])
        return

    extracted_rows = rows_to_extracted_transactions(statement, result.rows)
    ExtractedTransaction.objects.bulk_create(extracted_rows)
    statement.status = StatementUpload.NEEDS_REVIEW
    statement.save(update_fields=["status"])
