from django import forms

from .models import ExtractedTransaction, StatementUpload

INPUT_CLASSES = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm "
    "focus:border-emerald-500 focus:ring-emerald-500"
)


class StatementUploadForm(forms.ModelForm):
    class Meta:
        model = StatementUpload
        fields = ["broker", "file"]
        widgets = {
            "broker": forms.Select(attrs={"class": INPUT_CLASSES}),
            "file": forms.ClearableFileInput(attrs={"class": INPUT_CLASSES, "accept": ".pdf"}),
        }


class ExtractedTransactionForm(forms.ModelForm):
    class Meta:
        model = ExtractedTransaction
        fields = [
            "matched_instrument", "transaction_type", "quantity",
            "price_per_share", "fees", "trade_date", "is_excluded",
        ]
        widgets = {
            "matched_instrument": forms.Select(attrs={"class": "text-sm rounded border-gray-300"}),
            "transaction_type": forms.Select(attrs={"class": "text-sm rounded border-gray-300"}),
            "quantity": forms.NumberInput(attrs={"class": "text-sm rounded border-gray-300 w-24", "step": "0.0001"}),
            "price_per_share": forms.NumberInput(attrs={"class": "text-sm rounded border-gray-300 w-24", "step": "0.0001"}),
            "fees": forms.NumberInput(attrs={"class": "text-sm rounded border-gray-300 w-20", "step": "0.01"}),
            "trade_date": forms.DateInput(attrs={"class": "text-sm rounded border-gray-300", "type": "date"}),
        }


ExtractedTransactionFormSet = forms.modelformset_factory(
    ExtractedTransaction, form=ExtractedTransactionForm, extra=0
)
