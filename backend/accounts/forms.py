from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from .models import User

INPUT_CLASSES = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm "
    "focus:border-emerald-500 focus:ring-emerald-500"
)


class HoneypotMixin(forms.Form):
    """
    A field real users never see or fill in (hidden off-screen via CSS, not
    type="hidden" — some bots specifically skip hidden inputs, so this is
    tucked out of the viewport instead) but that simple form-filling bots
    routinely fill in along with everything else. Anything in it means
    "not a human" without ever showing a visible challenge to real users.
    """

    website = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={
            "autocomplete": "off", "tabindex": "-1",
            "style": "position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;",
            "aria-hidden": "true",
        }),
    )

    def clean_website(self):
        value = self.cleaned_data.get("website")
        if value:
            raise forms.ValidationError("Bot check failed.")
        return value


class SignUpForm(HoneypotMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "website":
                field.widget.attrs.setdefault("class", INPUT_CLASSES)
        self.fields["email"].required = True
        self.fields["phone_number"].widget.attrs["placeholder"] = "0XX XXX XXXX"


class StyledAuthenticationForm(HoneypotMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "website":
                field.widget.attrs.setdefault("class", INPUT_CLASSES)


class TOTPVerifyForm(forms.Form):
    code = forms.CharField(
        label="6-digit code (or a recovery code)",
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": INPUT_CLASSES, "autocomplete": "one-time-code", "inputmode": "numeric", "autofocus": True,
        }),
    )


class TOTPConfirmForm(forms.Form):
    code = forms.CharField(
        label="Enter the 6-digit code from your app",
        max_length=6,
        widget=forms.TextInput(attrs={"class": INPUT_CLASSES, "autocomplete": "one-time-code", "inputmode": "numeric"}),
    )


class DisableTOTPForm(forms.Form):
    password = forms.CharField(label="Confirm your password", widget=forms.PasswordInput(attrs={"class": INPUT_CLASSES}))


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", INPUT_CLASSES)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", INPUT_CLASSES)
