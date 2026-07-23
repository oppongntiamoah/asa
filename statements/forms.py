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
            # Not surfaced as an editable field on the (already dense) review
            # screen — hidden so the parser's already-extracted fee value
            # still gets submitted, rather than being silently dropped.
            "fees": forms.HiddenInput(),
            "trade_date": forms.DateInput(attrs={"class": "text-sm rounded border-gray-300", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ExtractedTransaction.fees has a model-level default of 0 but isn't
        # blank=True (fees on a *committed* portfolio.Transaction shouldn't
        # silently default), so the ModelForm treats it as required by
        # default. On this form it must never block submission — every row
        # was failing formset validation with "fees: This field is
        # required" because the field wasn't rendered anywhere for the
        # browser to submit a value for.
        self.fields["fees"].required = False


ExtractedTransactionFormSet = forms.modelformset_factory(
    ExtractedTransaction, form=ExtractedTransactionForm, extra=0
)
