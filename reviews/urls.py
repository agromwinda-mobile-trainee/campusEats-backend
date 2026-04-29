from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReviewViewSet

router = DefaultRouter(trailing_slash=False)
router.register("reviews", ReviewViewSet, basename="reviews")

urlpatterns = [
    path("", include(router.urls)),
]
