from rest_framework import permissions, viewsets

from videos.permissions import IsOwnerOrReadOnly

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Review.objects.select_related("user").order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
