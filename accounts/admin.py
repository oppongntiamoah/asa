from django.contrib import admin
from . models import CustomUser, AllowedUser

from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import AllowedUser


# Resource for import-export
class AllowedUserResource(resources.ModelResource):
    class Meta:
        model = AllowedUser
        fields = ("id", "email")   # specify which fields to import/export


# Admin with import-export
@admin.register(AllowedUser)
class AllowedUserAdmin(ImportExportModelAdmin):
    resource_class = AllowedUserResource
    list_display = ("email",)
    search_fields = ("email",)


admin.site.register(CustomUser)
