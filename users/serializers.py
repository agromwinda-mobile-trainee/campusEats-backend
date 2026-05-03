from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "avatar",
            "bio",
            "latitude",
            "longitude",
        )
        read_only_fields = ("id",)


class UserPublicSerializer(serializers.ModelSerializer):
    """Profil public (+ champs enrichis via annotate sur le queryset)."""

    followers_count = serializers.IntegerField(read_only=True, default=0)
    following_count = serializers.IntegerField(read_only=True, default=0)
    videos_count = serializers.IntegerField(read_only=True, default=0)
    is_followed_by_me = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "avatar",
            "bio",
            "latitude",
            "longitude",
            "followers_count",
            "following_count",
            "videos_count",
            "is_followed_by_me",
        )
        read_only_fields = fields

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
    class Meta:
        model = User
        fields = ("id", "username", "avatar")
        read_only_fields = fields


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
