from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import decorators, mixins, permissions, response, status, viewsets
from rest_framework.views import APIView

from interactions.models import Comment, Follow, Like, VideoBookmark
from interactions.notifications import notify_comment, notify_like
from interactions.serializers import CommentCreateSerializer, CommentSerializer
from interactions.services import invalidate_video_counts

from .models import Sound, VideoPost
from .pagination import CommentCursorPagination, FeedCursorPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    SoundSerializer,
    VideoBookmarkRowSerializer,
    VideoCreateSerializer,
    VideoPostSerializer,
)
from .services import get_for_you_queryset, get_trending_queryset, haversine_distance

User = get_user_model()


class SearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from users.serializers import UserBriefSerializer

        q = (request.query_params.get("q") or "").strip()
        type_ = (request.query_params.get("type") or "all").lower()
        if len(q) < 1:
            return response.Response(
                {"detail": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        users_payload = []
        videos_payload = []
        if type_ in ("all", "users"):
            users = User.objects.filter(username__icontains=q).order_by("username")[:20]
            users_payload = UserBriefSerializer(users, many=True).data
        if type_ in ("all", "videos"):
            videos = (
                VideoPost.objects.filter(caption__icontains=q)
                .select_related("user", "sound")
                .order_by("-created_at")[:20]
            )
            videos_payload = VideoPostSerializer(videos, many=True, context={"request": request}).data
        return response.Response(
            {
                "query": q,
                "type": type_,
                "users": users_payload,
                "videos": videos_payload,
            }
        )


class SoundViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Sound.objects.all()
    serializer_class = SoundSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return super().get_permissions()


class BookmarkViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Favoris de l’utilisateur connecté (pagination curseur sur la date d’enregistrement)."""

    serializer_class = VideoBookmarkRowSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FeedCursorPagination

    def get_queryset(self):
        return (
            VideoBookmark.objects.filter(user=self.request.user)
            .select_related("video", "video__user", "video__sound")
            .order_by("-created_at")
        )


class VideoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        base = VideoPost.objects.select_related("user", "sound")
        if self.action != "list":
            return base.order_by("-created_at")
        feed_type = (self.request.query_params.get("feed") or "").lower()
        if feed_type == "trending":
            return get_trending_queryset()
        if feed_type == "for_you":
            return get_for_you_queryset(
                user=self.request.user if self.request.user.is_authenticated else None
            )
        if feed_type == "following":
            if not self.request.user.is_authenticated:
                return VideoPost.objects.none()
            following_ids = Follow.objects.filter(follower=self.request.user).values_list(
                "following_id", flat=True
            )
            return base.filter(user_id__in=following_ids).order_by("-created_at")
        return base.order_by("-created_at")

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

        base = VideoPost.objects.select_related("user", "sound")
        videos = base.exclude(latitude__isnull=True, longitude__isnull=True)
        nearby_ids = []
        for video in videos:
            distance = haversine_distance(float(lat), float(lng), float(video.latitude), float(video.longitude))
            if distance <= float(radius_km):
                nearby_ids.append(video.id)

        queryset = base.filter(id__in=nearby_ids).order_by("-created_at")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def comments(self, request, pk=None):
        video = self.get_object()
        qs = Comment.objects.filter(video=video).select_related("user").order_by("-created_at")
        paginator = CommentCursorPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        if page is not None:
            ser = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(ser.data)
        return response.Response(CommentSerializer(qs, many=True).data)

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        video = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, video=video)
        if not created:
            like.delete()
            invalidate_video_counts(video.id)
            return response.Response({"liked": False})

        invalidate_video_counts(video.id)
        notify_like(actor=request.user, video=video)
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
        notify_comment(actor=request.user, video=video)
        return response.Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(detail=True, methods=["post", "delete"], permission_classes=[permissions.IsAuthenticated])
    def bookmark(self, request, pk=None):
        video = self.get_object()
        if request.method == "POST":
            _b, created = VideoBookmark.objects.get_or_create(user=request.user, video=video)
            return response.Response(
                {"saved": True},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        deleted, _ = VideoBookmark.objects.filter(user=request.user, video=video).delete()
        return response.Response({"saved": False, "removed": bool(deleted)})
