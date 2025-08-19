from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required
from .models import Activity, Booking, StudentProfile
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomUserCreationForm, StudentProfileForm

from .forms import DaySelectionForm



@login_required
def activity_list(request):
    student = StudentProfile.objects.get(user=request.user)

    bookings = Booking.objects.filter(student=student).select_related('activity')
    booked_ids = set(b.activity_id for b in bookings)
    booking_map = {b.activity_id: b for b in bookings}

    days = Activity.DAYS
    grouped = []
    for day_key, day_label in days:
        activities = Activity.objects.filter(
            day=day_key,
            allowed_grades=student.grade
        ).order_by('name')
        grouped.append({
            'day': day_label,
            'activities': activities
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
def booking_report(request):
    activities = Activity.objects.all().order_by('day', 'name')
    return render(request, 'activities/report.html', {'activities': activities})


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

    booking.delete()
    messages.success(request, "Booking removed.")
    return redirect('activity_list')




DAYS = [d[0] for d in Activity.DAYS]  # ['Monday', 'Tuesday', ...]

@login_required
def booking_wizard(request, step=0):
    student = StudentProfile.objects.get(user=request.user)

    # First step: reset choices
    if step == 0:
        request.session['booking_choices'] = {}

    if step >= len(DAYS):
        selections = request.session.get('booking_choices', {})
        chosen_days = [day for day, act in selections.items() if act]

        # Rule: Must choose exactly 3 days
        if len(chosen_days) != 3:
            messages.error(request, "You must book exactly 3 activities, one per chosen day.")
            return redirect('booking_wizard', step=0)

        # Save all
        for day, activity_id in selections.items():
            if activity_id:
                # Ensure one per day
                if not Booking.objects.filter(student=student, day=day).exists():
                    activity = Activity.objects.get(id=activity_id)
                    Booking.objects.create(student=student, activity=activity)

        messages.success(request, "Your 3 bookings have been saved!")
        return redirect('activity_list')

    day = DAYS[step]
    form = DaySelectionForm(day, student.grade, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        activity_id = form.cleaned_data['activity']
        choices = request.session.get('booking_choices', {})
        choices[day] = activity_id
        request.session['booking_choices'] = choices
        return redirect('booking_wizard', step=step+1)

    return render(request, 'activities/booking_wizard.html', {
        'form': form,
        'day': day,
        'step': step + 1,
        'total_steps': len(DAYS)
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
            return redirect("activity_list")
    else:
        user_form = CustomUserCreationForm()
        profile_form = StudentProfileForm()
    return render(request, "accounts/register.html", {"user_form": user_form, "profile_form": profile_form})
