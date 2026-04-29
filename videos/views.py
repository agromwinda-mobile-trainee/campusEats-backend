from decimal import Decimal, InvalidOperation

from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, response, status, viewsets

from interactions.models import Comment, Like
from interactions.serializers import CommentCreateSerializer, CommentSerializer
from interactions.services import invalidate_video_counts

from .models import VideoPost
from .permissions import IsOwnerOrReadOnly
from .serializers import VideoCreateSerializer, VideoPostSerializer
from .services import haversine_distance, get_trending_queryset


class VideoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = VideoPost.objects.select_related("user")
        feed_type = self.request.query_params.get("feed")

        if feed_type == "trending":
            return get_trending_queryset()
        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return VideoCreateSerializer
        return VideoPostSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        VideoPost.objects.filter(id=instance.id).update(views_count=F("views_count") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @decorators.action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def nearby(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius_km = request.query_params.get("radius_km", "3")
        if not lat or not lng:
            return response.Response(
                {"detail": "lat and lng are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = Decimal(lat)
            lng = Decimal(lng)
            radius_km = Decimal(radius_km)
        except (InvalidOperation, TypeError):
            return response.Response(
                {"detail": "Invalid coordinates."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        videos = self.get_queryset().exclude(latitude__isnull=True, longitude__isnull=True)
        nearby_ids = []
        for video in videos:
            distance = haversine_distance(float(lat), float(lng), float(video.latitude), float(video.longitude))
            if distance <= float(radius_km):
                nearby_ids.append(video.id)

        queryset = self.get_queryset().filter(id__in=nearby_ids)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        video = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, video=video)
        if not created:
            like.delete()
            invalidate_video_counts(video.id)
            return response.Response({"liked": False})

        invalidate_video_counts(video.id)
        return response.Response({"liked": True}, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def comment(self, request, pk=None):
        video = get_object_or_404(VideoPost, pk=pk)
        serializer = CommentCreateSerializer(data={**request.data, "video": video.id})
        serializer.is_valid(raise_exception=True)
        comment = Comment.objects.create(
            user=request.user,
            video=video,
            text=serializer.validated_data["text"],
        )
        invalidate_video_counts(video.id)
        return response.Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )
