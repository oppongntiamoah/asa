from django.contrib import admin

from .models import ExtractedTransaction, StatementUpload


class ExtractedTransactionInline(admin.TabularInline):
    model = ExtractedTransaction
    extra = 0


@admin.register(StatementUpload)
class StatementUploadAdmin(admin.ModelAdmin):
    list_display = ("user", "broker", "status", "uploaded_at", "confirmed_at")
    list_filter = ("broker", "status")
    search_fields = ("user__username",)
    inlines = [ExtractedTransactionInline]
