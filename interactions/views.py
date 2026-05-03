from django.utils import timezone
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.pagination import CursorPagination

from .models import Notification
from .serializers_notifications import NotificationSerializer


class NotificationCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = "-created_at"


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationCursorPagination

    def get_queryset(self):
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("actor", "video")
            .order_by("-created_at")
        )

    @decorators.action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        if notif.recipient_id != request.user.id:
            return response.Response(status=status.HTTP_403_FORBIDDEN)
        if notif.read_at is None:
            notif.read_at = timezone.now()
            notif.save(update_fields=["read_at"])
        return response.Response(NotificationSerializer(notif).data)

    @decorators.action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        updated = Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return response.Response({"marked_read": updated})
