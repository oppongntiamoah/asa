# activities/models.py
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


class Grade(models.Model):
    name = models.CharField(max_length=10, unique=True)
    def __str__(self):
        return self.name
    

class Activity(models.Model):
    DAYS = [
        ('Monday','Monday'),('Tuesday','Tuesday'),('Wednesday','Wednesday'),
        ('Thursday','Thursday'),('Friday','Friday'),('Saturday','Saturday'),
        ('Sunday','Sunday'),
    ]
    name = models.CharField(max_length=150)
    day = models.CharField(max_length=10, choices=DAYS)
    allowed_grades = models.ManyToManyField(Grade, related_name='activities')
    instructor = models.CharField(max_length=150, blank=True, null=True)
    venue = models.CharField(max_length=150, blank=True, null=True)
    capacity = models.PositiveIntegerField(default=0, help_text="0 = Unlimited capacity")
    
    time = models.CharField(max_length=50)

    class Meta:
        ordering = ['day','name']
        unique_together = ('name','day')
        verbose_name_plural = "Activities"

    def __str__(self):
        return f"{self.name} ({self.day})"

    def bookings_count(self):
        return self.bookings.count()
    bookings_count.short_description = "Bookings"

    def spots_left(self):
        """Return spots left, or 'Unlimited' if capacity is 0."""
        if self.capacity == 0:
            return "Unlimited"
        return self.capacity - self.bookings.count()
    spots_left.short_description = "Spots left"



class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="students",
    )
    
    name = models.CharField(max_length=250, help_text="Full Name")
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.name} ({self.grade})"

    def email(self):
        return self.user.email
    
    

class Booking(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='bookings')
    day = models.CharField(max_length=10)
    date_created = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'day')
        ordering = ['-date_created']

    def save(self, *args, **kwargs):
        if self.activity:
            self.day = self.activity.day
            if self.activity.capacity != 0 and self.activity.bookings.count() >= self.activity.capacity:
                raise ValueError(f"{self.activity} is already full.")
        super().save(*args, **kwargs)

    
    def can_modify(self):
        """Returns True if booking can be unbooked/changed."""
        return timezone.now() - self.date_created <= timedelta(days=100)

    def __str__(self):
        return f"{self.student} → {self.activity} on {self.day}"
