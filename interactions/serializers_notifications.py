from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "actor",
            "actor_username",
            "video",
            "read_at",
            "created_at",
        )
        read_only_fields = fields
