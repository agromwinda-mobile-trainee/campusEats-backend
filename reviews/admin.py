from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "place_name", "rating", "created_at")
    search_fields = ("place_name", "user__username")
    list_filter = ("rating", "created_at")
