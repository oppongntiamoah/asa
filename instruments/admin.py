from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from import_export.admin import ImportExportModelAdmin

from .ingest.csv_ingest import ingest_price_csv
from .models import Instrument, PriceBar, PriceIngestBatch
from .resources import InstrumentResource


@admin.register(Instrument)
class InstrumentAdmin(ImportExportModelAdmin):
    resource_classes = [InstrumentResource]
    list_display = ("ticker", "name", "sector", "is_active", "listed_date")
    search_fields = ("ticker", "name")
    list_filter = ("sector", "is_active")


@admin.register(PriceBar)
class PriceBarAdmin(admin.ModelAdmin):
    list_display = ("instrument", "trade_date", "close_price", "source")
    list_filter = ("source", "trade_date")
    search_fields = ("instrument__ticker",)
    autocomplete_fields = ("instrument",)


class PriceCSVUploadForm(forms.Form):
    file = forms.FileField(
        label="Daily closing price CSV",
        help_text="GSE daily export — the trade date is read from the file's own Daily Date column.",
    )
    trade_date_override = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Trade date (only if the file has no date column)",
    )


@admin.register(PriceIngestBatch)
class PriceIngestBatchAdmin(admin.ModelAdmin):
    list_display = ("trade_date", "source", "row_count", "error_count", "uploaded_by", "created_at")
    readonly_fields = ("source", "trade_date", "row_count", "error_count", "error_log", "raw_file", "uploaded_by", "created_at")
    change_list_template = "admin/instruments/priceingestbatch/change_list.html"

    def has_add_permission(self, request):
        return False  # creation only happens via the upload view below

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("upload-csv/", self.admin_site.admin_view(self.upload_csv), name="instruments_priceingestbatch_upload"),
        ]
        return custom + urls

    def upload_csv(self, request):
        if request.method == "POST":
            form = PriceCSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                result = ingest_price_csv(
                    form.cleaned_data["file"],
                    trade_date=form.cleaned_data["trade_date_override"],
                    uploaded_by=request.user,
                )
                if result.error_count:
                    messages.warning(
                        request,
                        f"Ingested {result.row_count} rows with {result.error_count} errors. "
                        f"See the batch record for details.",
                    )
                else:
                    messages.success(request, f"Ingested {result.row_count} price rows.")
                return redirect("admin:instruments_priceingestbatch_changelist")
        else:
            form = PriceCSVUploadForm()
        return render(request, "admin/instruments/priceingestbatch/upload_csv.html", {"form": form})
