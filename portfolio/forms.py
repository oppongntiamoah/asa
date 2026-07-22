from django import forms

from instruments.models import Instrument

from .models import Transaction

INPUT_CLASSES = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm "
    "focus:border-emerald-500 focus:ring-emerald-500"
)


class TransactionForm(forms.ModelForm):
    instrument = forms.ModelChoiceField(
        queryset=Instrument.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )

    class Meta:
        model = Transaction
        fields = ["instrument", "transaction_type", "quantity", "price_per_share", "fees", "trade_date", "broker", "notes"]
        widgets = {
            "transaction_type": forms.Select(attrs={"class": INPUT_CLASSES}),
            "quantity": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.0001", "min": "0"}),
            "price_per_share": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.0001", "min": "0"}),
            "fees": forms.NumberInput(attrs={"class": INPUT_CLASSES, "step": "0.01", "min": "0"}),
            "trade_date": forms.DateInput(attrs={"class": INPUT_CLASSES, "type": "date"}),
            "broker": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "notes": forms.TextInput(attrs={"class": INPUT_CLASSES}),
        }
