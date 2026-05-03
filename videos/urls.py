from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookmarkViewSet, SearchView, SoundViewSet, VideoViewSet

router = DefaultRouter(trailing_slash=False)
router.register("videos", VideoViewSet, basename="videos")
router.register("sounds", SoundViewSet, basename="sounds")
router.register("bookmarks", BookmarkViewSet, basename="bookmarks")

urlpatterns = [
    path("search", SearchView.as_view(), name="api-search"),
    path("", include(router.urls)),
]
