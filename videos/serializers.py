from rest_framework import serializers

from interactions.services import get_or_set_count

from .models import VideoPost


class VideoPostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = VideoPost
        fields = (
            "id",
            "user",
            "username",
            "video_url",
            "caption",
            "latitude",
            "longitude",
            "created_at",
            "views_count",
            "likes_count",
            "comments_count",
        )
        read_only_fields = ("id", "user", "created_at", "views_count")

    def get_likes_count(self, obj):
        return get_or_set_count(obj, "likes", "likes")

    def get_comments_count(self, obj):
        return get_or_set_count(obj, "comments", "comments")


class VideoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoPost
        fields = ("id", "video_url", "caption", "latitude", "longitude")
        read_only_fields = ("id",)
