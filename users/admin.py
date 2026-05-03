from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CampusEatsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Campus Profile",
            {"fields": ("avatar", "avatar_url", "bio", "latitude", "longitude")},
        ),
    )
