# activities/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Booking, Activity
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser, AllowedUser
from .models import StudentProfile

class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get('student')
        activity = cleaned.get('activity')
        if not student or not activity:
            return cleaned

        # 1) check grade allowed
        if student.grade not in activity.allowed_grades.all():
            raise ValidationError("This student's grade is not allowed for the chosen activity.")

        # 2) check capacity (if creating)
        if self.instance.pk is None:
            current_count = activity.bookings.count()
            if current_count >= activity.capacity:
                raise ValidationError("Activity capacity reached; cannot create booking.")

        # 3) check unique day booking
        existing = Booking.objects.filter(student=student, day=activity.day)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError(f"Student already has a booking on {activity.day}.")
        return cleaned


class DaySelectionForm(forms.Form):
    def __init__(self, day, grade, *args, **kwargs):
        super().__init__(*args, **kwargs)
        activities = Activity.objects.filter(day=day, allowed_grades=grade)
        choices = [('', 'Skip this day')]
        for act in activities:
            label = f"{act.name} — {act.instructor or 'No instructor'} @ {act.venue or 'No venue'}"
            if act.capacity > 0:
                label += f" (Spots left: {act.spots_left()})"
            else:
                label += " (Unlimited)"
            choices.append((act.id, label))
        self.fields['activity'] = forms.ChoiceField(
            label=f"Select activity for {day}",
            choices=choices,
            widget=forms.RadioSelect,
            required=False
        )






class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not AllowedUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is not allowed to register.")
        return email


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["name", "grade"]