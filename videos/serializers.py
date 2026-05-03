from rest_framework import serializers

from interactions.models import VideoBookmark
from interactions.services import get_or_set_count

from .models import Sound, VideoPost


class SoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sound
        fields = ("id", "title", "file", "created_at")
        read_only_fields = ("id", "created_at")


class VideoPostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    sound = SoundSerializer(read_only=True)

    class Meta:
        model = VideoPost
        fields = (
            "id",
            "user",
            "username",
            "video_url",
            "sound",
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
    sound = serializers.PrimaryKeyRelatedField(
        queryset=Sound.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = VideoPost
        fields = ("id", "video_url", "sound", "caption", "latitude", "longitude")
        read_only_fields = ("id",)


class VideoBookmarkRowSerializer(serializers.ModelSerializer):
    video = VideoPostSerializer(read_only=True)

    class Meta:
        model = VideoBookmark
        fields = ("id", "video", "created_at")
        read_only_fields = fields
