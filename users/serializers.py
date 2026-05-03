from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .media_urls import user_avatar_absolute_url
from .models import User


class CurrentUserSerializer(serializers.ModelSerializer):
    """GET/PATCH /me et réponse enrichie après inscription."""

    avatar = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)
    followers_count = serializers.IntegerField(read_only=True, default=0)
    following_count = serializers.IntegerField(read_only=True, default=0)
    videos_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "bio",
            "avatar",
            "followers_count",
            "following_count",
            "videos_count",
            "created_at",
            "latitude",
            "longitude",
        )
        read_only_fields = (
            "id",
            "email",
            "avatar",
            "followers_count",
            "following_count",
            "videos_count",
            "created_at",
        )

    def get_avatar(self, obj):
        request = self.context.get("request")
        return user_avatar_absolute_url(obj, request)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in ("followers_count", "following_count", "videos_count"):
            if getattr(instance, key, None) is None:
                data[key] = 0
        return data


class UserMeUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, max_length=150)
    bio = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username cannot be empty.")
        user = self.context["request"].user
        if (
            get_user_model()
            .objects.exclude(pk=user.pk)
            .filter(username__iexact=value)
            .exists()
        ):
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_avatar(self, value):
        if value in (None, ""):
            return value
        value = value.strip()
        if value in ("",):
            return ""
        if value.startswith(("http://", "https://")):
            return value
        raise serializers.ValidationError("Avatar must be an absolute URL (https://...) or empty to clear.")

    def update(self, user, validated_data):
        if "username" in validated_data:
            user.username = validated_data["username"]
        if "bio" in validated_data:
            user.bio = validated_data["bio"]
        if "avatar" in validated_data:
            av = validated_data["avatar"]
            if av in (None, ""):
                if user.avatar:
                    user.avatar.delete(save=False)
                    user.avatar = None
                user.avatar_url = None
            else:
                user.avatar_url = av
                if user.avatar:
                    user.avatar.delete(save=False)
                    user.avatar = None
        user.save()
        return user


class UserPublicSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    is_followed_by_me = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(read_only=True, default=0)
    following_count = serializers.IntegerField(read_only=True, default=0)
    videos_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "bio",
            "avatar",
            "followers_count",
            "following_count",
            "videos_count",
            "is_followed_by_me",
        )
        read_only_fields = fields

    def get_avatar(self, obj):
        return user_avatar_absolute_url(obj, self.context.get("request"))

    def get_is_followed_by_me(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if request.user.id == obj.id:
            return False
        return _follow_exists(request.user, obj)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for key in ("followers_count", "following_count", "videos_count"):
            if getattr(instance, key, None) is None:
                data[key] = 0
        return data


def _follow_exists(follower, following_user):
    from interactions.models import Follow

    return Follow.objects.filter(follower=follower, following=following_user).exists()


class UserBriefSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "avatar")
        read_only_fields = fields

    def get_avatar(self, obj):
        return user_avatar_absolute_url(obj, self.context.get("request"))


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "avatar",
            "bio",
            "latitude",
            "longitude",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CampusTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token
