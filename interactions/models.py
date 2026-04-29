from django.conf import settings
from django.db import models

from videos.models import VideoPost


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    video = models.ForeignKey(VideoPost, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "video"], name="unique_like_per_user_video")
        ]
        indexes = [models.Index(fields=["video", "created_at"])]


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    video = models.ForeignKey(
        VideoPost,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["video", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]
