from rest_framework import serializers

from interactions.models import VideoBookmark
from interactions.services import get_or_set_count
from users.media_urls import file_field_absolute_url

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
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = VideoPost
        fields = (
            "id",
            "user",
            "username",
            "video_url",
            "thumbnail_url",
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

    def get_video_url(self, obj):
        request = self.context.get("request")
        return file_field_absolute_url(request, obj.video_url)

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        return file_field_absolute_url(request, obj.thumbnail)

    def get_likes_count(self, obj):
        return get_or_set_count(obj, "likes", "likes")

    def get_comments_count(self, obj):
        return get_or_set_count(obj, "comments", "comments")


class VideoProfileGridSerializer(serializers.ModelSerializer):
    """Contrat pour GET /api/users/{id}/videos (grille profil)."""

    user = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = VideoPost
        fields = (
            "id",
            "caption",
            "video_url",
            "thumbnail_url",
            "likes_count",
            "comments_count",
            "views_count",
            "created_at",
            "user",
        )
        read_only_fields = fields

    def get_user(self, obj):
        return {"id": obj.user_id, "username": obj.user.username}

    def get_video_url(self, obj):
        request = self.context.get("request")
        return file_field_absolute_url(request, obj.video_url)

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        return file_field_absolute_url(request, obj.thumbnail)

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
        fields = ("id", "video_url", "thumbnail", "sound", "caption", "latitude", "longitude")
        read_only_fields = ("id",)


class VideoBookmarkRowSerializer(serializers.ModelSerializer):
    video = VideoPostSerializer(read_only=True)

    class Meta:
        model = VideoBookmark
        fields = ("id", "video", "created_at")
        read_only_fields = fields
