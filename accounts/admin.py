from django.contrib import admin
from . models import CustomUser, AllowedUser


admin.site.register(CustomUser)
admin.site.register(AllowedUser)