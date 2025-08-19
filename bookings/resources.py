# activities/resources.py
from import_export import resources, fields
from import_export.widgets import ManyToManyWidget
from .models import Grade, Activity, StudentProfile, Booking


class GradeResource(resources.ModelResource):
    class Meta:
        model = Grade
        fields = ("id", "name")


class ActivityResource(resources.ModelResource):
    allowed_grades = fields.Field(
        column_name="allowed_grades",
        attribute="allowed_grades",
        widget=ManyToManyWidget(Grade, field="name", separator=","),
    )

    class Meta:
        model = Activity
        fields = (
            "id",
            "name",
            "day",
            "instructor",
            "venue",
            "capacity",
            "allowed_grades",
        )


class StudentProfileResource(resources.ModelResource):
    grade = fields.Field(
        column_name="grade",
        attribute="grade",
        widget=ManyToManyWidget(Grade, field="name"),
    )

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "user",
            "grade",
        )


class BookingResource(resources.ModelResource):
    class Meta:
        model = Booking
        fields = (
            "id",
            "student__name",
            "student__user__email",
            "student__grade__name",
            "activity__name",
            "day",
            "date_created",
            "attended",
        )
