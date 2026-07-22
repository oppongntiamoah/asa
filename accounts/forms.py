from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

INPUT_CLASSES = (
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm "
    "focus:border-emerald-500 focus:ring-emerald-500"
)


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "email", "phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", INPUT_CLASSES)
        self.fields["email"].required = True
        self.fields["phone_number"].widget.attrs["placeholder"] = "0XX XXX XXXX"


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", INPUT_CLASSES)
