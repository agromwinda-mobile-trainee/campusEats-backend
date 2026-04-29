from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "user",
            "username",
            "place_name",
            "rating",
            "comment",
            "media",
            "latitude",
            "longitude",
            "created_at",
        )
        read_only_fields = ("id", "user", "created_at")

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
