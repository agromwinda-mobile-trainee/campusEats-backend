from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import generics, mixins, permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView

from interactions.models import Follow
from interactions.notifications import notify_follow

from videos.models import VideoPost
from videos.pagination import FeedCursorPagination, FollowRelationPagination
from videos.serializers import VideoPostSerializer

from .serializers import (
    CampusTokenObtainPairSerializer,
    RegisterSerializer,
    UserBriefSerializer,
    UserPublicSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = CampusTokenObtainPairSerializer


class UserViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    lookup_field = "pk"

    def get_queryset(self):
        return User.objects.annotate(
            followers_count=Count("follower_edges", distinct=True),
            following_count=Count("following_edges", distinct=True),
            videos_count=Count("videos", distinct=True),
        )

    def get_serializer_class(self):
        if self.action == "me":
            return UserSerializer
        if self.action in ("followers", "following"):
            return UserBriefSerializer
        return UserPublicSerializer

    @action(detail=False, methods=["get", "patch"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == "GET":
            serializer = UserSerializer(request.user, context={"request": request})
            return response.Response(serializer.data)
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def videos(self, request, pk=None):
        profile_user = self.get_object()
        queryset = VideoPost.objects.filter(user=profile_user).select_related("user", "sound").order_by(
            "-created_at"
        )
        paginator = FeedCursorPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = VideoPostSerializer(page, many=True, context={"request": request})
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def followers(self, request, pk=None):
        profile_user = self.get_object()
        follows = (
            Follow.objects.filter(following=profile_user)
            .select_related("follower")
            .order_by("-created_at")
        )
        paginator = FollowRelationPagination()
        page = paginator.paginate_queryset(follows, request, view=self)
        users = [f.follower for f in page] if page is not None else [f.follower for f in follows]
        serializer = UserBriefSerializer(users, many=True, context={"request": request})
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def following(self, request, pk=None):
        profile_user = self.get_object()
        follows = (
            Follow.objects.filter(follower=profile_user)
            .select_related("following")
            .order_by("-created_at")
        )
        paginator = FollowRelationPagination()
        page = paginator.paginate_queryset(follows, request, view=self)
        users = [f.following for f in page] if page is not None else [f.following for f in follows]
        serializer = UserBriefSerializer(users, many=True, context={"request": request})
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    @action(detail=True, methods=["post", "delete"], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        target = self.get_object()
        if target.id == request.user.id:
            return response.Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == "POST":
            _follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
            if created:
                notify_follow(actor=request.user, following_user_id=target.id)
            return response.Response(
                {"following": True},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        deleted, _ = Follow.objects.filter(follower=request.user, following=target).delete()
        return response.Response({"following": False, "removed": bool(deleted)})
