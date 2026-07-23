"""
Import/export for the Instrument master list via django-import-export,
wired into Django admin (Instruments -> Import). Built against the real
GSE "Main Market Companies" listing export: columns Symbol, Company,
Date Listed (DD/MM/YYYY, sometimes blank), Stated Capital, Issued Shares,
Authorised Shares.

Only Symbol/Company/Date Listed map onto Instrument today — the capital/
shares columns are left unimported. Their source formatting is too
inconsistent to parse reliably (mixed currency prefixes, "." and ","
both used as thousands separators, occasional typos like "GH(" in the raw
export) and Instrument has no field for them yet; revisit if a real use
case (e.g. market-cap calculations) needs them.

ticker is the import key (import_id_fields) so re-running an import with
an updated export updates existing rows instead of duplicating them.
"""
from datetime import datetime

from import_export import fields, resources, widgets

from .models import Instrument


class FlexibleDateWidget(widgets.Widget):
    """Blank-tolerant DD/MM/YYYY parser — several rows in the real export
    have no listing date recorded."""

    def clean(self, value, row=None, **kwargs):
        value = (value or "").strip()
        if not value:
            return None
        try:
            return datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            return None

    def render(self, value, obj=None, **kwargs):
        return value.strftime("%d/%m/%Y") if value else ""


class InstrumentResource(resources.ModelResource):
    ticker = fields.Field(attribute="ticker", column_name="Symbol")
    name = fields.Field(attribute="name", column_name="Company")
    listed_date = fields.Field(attribute="listed_date", column_name="Date Listed", widget=FlexibleDateWidget())

    class Meta:
        model = Instrument
        import_id_fields = ["ticker"]
        fields = ["ticker", "name", "listed_date"]
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        symbol = row.get("Symbol")
        if symbol:
            row["Symbol"] = symbol.strip().upper()
