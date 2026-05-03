from django.contrib import admin

from .models import Sound, VideoPost


@admin.register(Sound)
class SoundAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "caption", "created_at", "views_count")
    search_fields = ("caption", "user__username")
    list_filter = ("created_at",)
