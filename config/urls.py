from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/", include("users.router_urls")),
    path("api/", include("videos.urls")),
    path("api/", include("interactions.urls")),
    path("api/", include("reviews.urls")),
]
