from django.contrib import admin

from .models import Comment, Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "video", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "video", "created_at")
    search_fields = ("text", "user__username")
