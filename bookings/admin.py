# activities/admin.py
from django.contrib import admin
from django.urls import path, reverse
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter
from django.db.models import Count
import csv

from .models import Grade, Activity, StudentProfile, Booking
from .forms import BookingAdminForm
from import_export.admin import ImportExportModelAdmin
from .resources import GradeResource, ActivityResource, StudentProfileResource, BookingResource

@admin.register(Grade)
class GradeAdmin(ImportExportModelAdmin):
    resource_class = GradeResource
    list_display = ('name', 'activities_count')
    search_fields = ('name',)

    def activities_count(self, obj):
        return obj.activities.count()
    activities_count.short_description = "Activities"




@admin.register(Activity)
class ActivityAdmin(ImportExportModelAdmin):
    resource_class = ActivityResource
    list_display = ('name','day', 'time', 'capacity','bookings_count','spots_left','allowed_grades_list')
    list_filter = ('day', 'allowed_grades')
    search_fields = ('name',)
    filter_horizontal = ('allowed_grades', )
    readonly_fields = ('bookings_count','spots_left')
    actions = ['export_activities_csv']

    fieldsets = (
        (None, {'fields': ('name','day', 'time')}),
        ('Capacity & Grades', {'fields': ('capacity','allowed_grades','bookings_count','spots_left')}),
    )

    def allowed_grades_list(self, obj):
        return ", ".join([g.name for g in obj.allowed_grades.all()])
    allowed_grades_list.short_description = "Allowed Grades"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_bookings=Count('bookings'))

    def bookings_count(self, obj):
        return obj.bookings.count()
    bookings_count.short_description = "Bookings"

    # admin action to export activities
    def export_activities_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=activities.csv'
        writer = csv.writer(response)
        writer.writerow(['ID','Name','Day','Capacity','BookingsCount','AllowedGrades'])
        for a in queryset:
            writer.writerow([a.pk, a.name, a.day, a.capacity, a.bookings.count(), ", ".join([g.name for g in a.allowed_grades.all()])])
        return response
    export_activities_csv.short_description = "Export selected activities to CSV"


@admin.register(StudentProfile)
class StudentProfileAdmin(ImportExportModelAdmin):
    resource_class = StudentProfileResource
    list_display = ('name', 'user__email','grade')
    search_fields = ('name',)
    list_filter = ('grade',)

    # def user_link(self, obj):
    #     url = admin.site.reverse('admin:auth_user_change', args=(obj.user.pk,))
    #     return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    # user_link.short_description = "Student"

    # def email(self, obj):
    #     return obj.user.email
    # email.short_description = "Email"


@admin.register(Booking)
class BookingAdmin(ImportExportModelAdmin):
    resource_class = BookingResource
    form = BookingAdminForm
    list_display = ('student__name', 'student_email', "activity", 'student_grade','activity_day','date_created','attended')
    list_filter = ('activity__day','activity__name','attended')
    search_fields = ('student__user__username','student__user__email','activity__name')
    date_hierarchy = 'date_created'
    actions = ['export_bookings_csv','mark_attended']

    # def student_link(self, obj):
    #     url = reverse('admin:auth_user_change', args=(obj.student.user.pk,))
    #     return format_html('<a href="{}">{}</a>', url, obj.student.user.get_full_name() or obj.student.user.username)
    # student_link.short_description = "Student"

    def student_email(self, obj):
        return obj.student.user.email
    student_email.short_description = "Email"

    def student_grade(self, obj):
        return obj.student.grade.name
    student_grade.short_description = "Grade"

    # def activity_link(self, obj):
    #     url = reverse('admin:activities_activity_change', args=(obj.activity.pk,))
    #     return format_html('<a href="{}">{}</a>', url, obj.activity.name)
    # activity_link.short_description = "Activity"

    def activity_day(self, obj):
        return obj.activity.day
    activity_day.short_description = "Day"

    # Export selected bookings to CSV
    def export_bookings_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=bookings.csv'
        writer = csv.writer(response)
        writer.writerow(['BookingID','Student','Email','Grade','Activity','Day','DateCreated','Attended'])
        for b in queryset.select_related('student__user','activity'):
            writer.writerow([b.pk, b.student.user, b.student.user.email, b.student.grade.name, b.activity.name, b.day, b.date_created.isoformat(), b.attended])
        return response
    export_bookings_csv.short_description = "Export selected bookings to CSV"

    # mark selected as attended
    def mark_attended(self, request, queryset):
        updated = queryset.update(attended=True)
        self.message_user(request, f"{updated} booking(s) marked as attended.")
    mark_attended.short_description = "Mark selected bookings as attended"

    # Add a custom report to admin URLs
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('booking-report/', self.admin_site.admin_view(self.booking_report), name='booking_report'),
        ]
        return custom + urls

    def booking_report(self, request):
        # aggregated counts per activity
        activities = Activity.objects.annotate(bookings_count=Count('bookings')).order_by('day','name')
        context = dict(
            self.admin_site.each_context(request),
            activities=activities,
        )
        return TemplateResponse(request, "admin/activities/booking_report.html", context)
