from django.contrib import admin

from .models import VideoPost


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "caption", "created_at", "views_count")
    search_fields = ("caption", "user__username")
    list_filter = ("created_at",)
