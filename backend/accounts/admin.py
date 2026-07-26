from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserSession


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("phone_number",)}),
    )
    list_display = ("username", "email", "phone_number", "is_staff", "created_at")


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "user_agent_short", "created_at", "last_seen")
    list_filter = ("created_at",)
    search_fields = ("user__username", "ip_address", "user_agent")
    readonly_fields = ("session_key", "user_agent", "ip_address", "created_at", "last_seen")
    autocomplete_fields = ("user",)

    @admin.display(description="User agent")
    def user_agent_short(self, obj):
        return obj.user_agent[:60]
