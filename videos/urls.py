from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import VideoViewSet

router = DefaultRouter(trailing_slash=False)
router.register("videos", VideoViewSet, basename="videos")

urlpatterns = [
    path("", include(router.urls)),
]
