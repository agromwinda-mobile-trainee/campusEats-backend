from math import radians, cos, sin, asin, sqrt

from django.core.cache import cache
from django.db.models import Count, F, IntegerField, Value
from django.db.models.functions import Coalesce

from .models import VideoPost


def haversine_distance(lat1, lon1, lat2, lon2):
    """Distance in km between two coordinates."""
    r = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return r * c


def get_trending_queryset():
    # Trending score favors engagement while preserving recency ordering fallback.
    return (
        VideoPost.objects.select_related("user")
        .annotate(
            likes_total=Count("likes", distinct=True),
            comments_total=Count("comments", distinct=True),
        )
        .annotate(
            trending_score=Coalesce(F("views_count"), Value(0), output_field=IntegerField())
            + (Coalesce(F("likes_total"), Value(0), output_field=IntegerField()) * Value(3))
            + (Coalesce(F("comments_total"), Value(0), output_field=IntegerField()) * Value(2))
        )
        .order_by("-trending_score", "-created_at")
    )


def get_cached_feed_key(kind: str, suffix: str = "") -> str:
    return f"feed:{kind}:{suffix}"


def get_cached_videos(key: str):
    return cache.get(key)


def set_cached_videos(key: str, data, ttl: int = 120):
    cache.set(key, data, timeout=ttl)
