from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required
from .models import Activity, Booking, StudentProfile
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomUserCreationForm, StudentProfileForm

from .forms import DaySelectionForm
from django.db.models import Count, F, FloatField, ExpressionWrapper

from django.db.models import Count, Q

@login_required
def dashboard(request):
    # Restrict access to staff (or superuser) only
    if not request.user.is_admin:
        return redirect('booking_wizard', step=0)  

    # Total students (users registered with profile)
    total_students = StudentProfile.objects.count()

    # Students by grade
    students_by_grade = (
        StudentProfile.objects.values('grade')
        .annotate(total=Count('id'))
        .order_by('grade')
    )

    # Activities with bookings
    activities = (
        Activity.objects
        .annotate(num_bookings=Count('bookings'))
        .filter(num_bookings=0)   # only activities with 0 bookings
        .order_by('day', 'name')
    )

    

    # Top 5 activities by percentage booked (excluding unlimited capacity)
    top_activities = (
        Activity.objects
        .annotate(
            num_bookings=Count('bookings'),
            booking_percentage=ExpressionWrapper(
                (F('num_bookings') * 100.0) / F('capacity'),
                output_field=FloatField()
            )
        )
        .exclude(capacity__isnull=True)        # exclude unlimited
        .exclude(capacity=0)                   # exclude capacity=0 to avoid division by zero
        .order_by('-booking_percentage')[:5]   # top 5
    )

    # Unlimited capacity: just rank by number of bookings
    unlimited_activities = (
        Activity.objects
        .filter(capacity=0)
        .annotate(num_bookings=Count('bookings'))
        .order_by('-num_bookings')[:5]
    )


    # --- New Stats ---
    # Count bookings per student
    bookings_per_student = (
        Booking.objects.values('student')
        .annotate(total_bookings=Count('id'))
    )

    # Students who booked all 7 days
    booked_all_7 = bookings_per_student.filter(total_bookings=7).count()

    # Students who booked exactly 3
    booked_exactly_3 = bookings_per_student.filter(total_bookings=3).count()

    # Students who booked >3 and <7
    booked_between = bookings_per_student.filter(total_bookings__gt=3, total_bookings__lt=7).count()

    return render(request, 'activities/report.html', {
        'total_students': total_students,
        'students_by_grade': students_by_grade,
        'activities': activities,
        'booked_all_7': booked_all_7,
        'booked_exactly_3': booked_exactly_3,
        'booked_between': booked_between,
        'top_activities': top_activities,
        'unlimited_activities': unlimited_activities,
    })




from django.core.exceptions import ObjectDoesNotExist

@login_required
def activity_list(request):
    student = None
    bookings = []
    booked_ids = set()
    booking_map = {}

    try:
        student = StudentProfile.objects.get(user=request.user)
        bookings = Booking.objects.filter(student=student).select_related('activity')
        booked_ids = set(b.activity_id for b in bookings)
        booking_map = {b.activity_id: b for b in bookings}
    except ObjectDoesNotExist:
        # No student profile -> treat as admin
        pass

    days = Activity.DAYS
    grouped = []
    for day_key, day_label in days:
        activities_qs = Activity.objects.filter(day=day_key).order_by('name')

        # If student -> filter by grade
        if student:
            activities_qs = activities_qs.filter(allowed_grades=student.grade)

        grouped.append({
            'day': day_label,
            'activities': activities_qs
        })

    total_booked = len(bookings)

    return render(request, 'activities/activity_list.html', {
        'grouped_activities': grouped,
        'total_booked': total_booked,
        'student': student,
        'booked_ids': booked_ids,
        'booking_map': booking_map
    })


@login_required
def book_activity(request, pk):
    student = StudentProfile.objects.get(user=request.user)
    activity = get_object_or_404(Activity, pk=pk)

    # Check if already booked this day
    existing_booking = Booking.objects.filter(student=student, day=activity.day).first()
    if existing_booking:
        if not existing_booking.can_modify():
            messages.error(request, "You cannot change this booking (time limit exceeded).")
            return redirect('activity_list')
        else:
            # Optional: Allow replacing within 30 min by deleting the old booking
            existing_booking.delete()

    # Total limit
    total_booked = Booking.objects.filter(student=student).count()
    if total_booked >= 7:
        messages.error(request, "You can only book up to 7 activities for the week.")
        return redirect('activity_list')

    # Grade check
    if student.grade not in activity.allowed_grades.all():
        messages.error(request, "You are not allowed to book this activity.")
        return redirect('activity_list')

    # Capacity check
    if activity.capacity > 0 and activity.bookings.count() >= activity.capacity:
        messages.error(request, "This activity is full.")
        return redirect('activity_list')

    Booking.objects.create(student=student, activity=activity)
    messages.success(request, f"Booked: {activity.name} on {activity.day}")
    return redirect('activity_list')






@login_required
def unbook_activity(request, pk):
    student = StudentProfile.objects.get(user=request.user)
    booking = Booking.objects.filter(student=student, activity_id=pk).first()

    if not booking:
        messages.error(request, "You have not booked this activity.")
        return redirect('activity_list')

    # Check if booking is locked
    if not booking.can_modify():
        messages.error(request, "You can no longer unbook this activity (time limit exceeded).")
        return redirect('activity_list')

    # Count how many bookings the student currently has
    total_booked = Booking.objects.filter(student=student).count()

    # Prevent unbooking if it would go below 3
    if total_booked <= 3:
        messages.error(request, "You must have at least 3 bookings. Cannot unbook further.")
        return redirect('activity_list')

    booking.delete()
    messages.success(request, "Booking removed.")
    return redirect('activity_list')





@login_required
def booking_wizard(request, step=0):
    student = StudentProfile.objects.get(user=request.user)

    # Prevent entering booking wizard if already booked
    existing_bookings = Booking.objects.filter(student=student)
    if existing_bookings.exists():
        messages.warning(request, "You have already made your bookings.")
        return redirect("activity_list")

    # First step: reset choices
    if step == 0:
        request.session['booking_choices'] = {}

    days = Activity.DAYS
    if step >= len(days):
        # All steps completed → finalize booking
        selections = request.session.get('booking_choices', {})
        chosen_days = [day for day, act in selections.items() if act]

        # Rule: Must choose exactly 3 activities
        if len(chosen_days) < 3:
            messages.error(request, "You must select at least 3 activities in total.")
            return redirect('booking_wizard', step=0)

        # Save bookings
        for activity_id in selections.values():
            if activity_id:  # skip empty
                Booking.objects.get_or_create(student=student, activity_id=activity_id)

        messages.success(request, "Your activities have been booked successfully!")
        return redirect('activity_list')  # Or summary page

    day_key, day_label = days[step]
    activities = Activity.objects.filter(
        day=day_key,
        allowed_grades=student.grade
    )

    if request.method == "POST":
        choice = request.POST.get("activity")
        choices = request.session.get('booking_choices', {})
        choices[day_key] = choice
        request.session['booking_choices'] = choices
        return redirect('booking_wizard', step=step+1)

    return render(request, 'activities/booking_wizard.html', {
        'step': step,
        'day_label': day_label,
        'activities': activities,
        'total_steps': len(days),
        'current_choices': request.session.get('booking_choices', {})
    })









def register(request):
    if request.method == "POST":
        user_form = CustomUserCreationForm(request.POST)
        profile_form = StudentProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('booking_wizard', step=0)
    else:
        user_form = CustomUserCreationForm()
        profile_form = StudentProfileForm()
    return render(request, "accounts/register.html", {"user_form": user_form, "profile_form": profile_form})
