from django.core.cache import cache


def count_cache_key(video_id: int, metric: str) -> str:
    return f"video:{video_id}:{metric}:count"


def get_or_set_count(video, metric: str, queryset_name: str) -> int:
    key = count_cache_key(video.id, metric)
    cached_value = cache.get(key)
    if cached_value is not None:
        return cached_value

    count = getattr(video, queryset_name).count()
    cache.set(key, count, timeout=300)
    return count


def invalidate_video_counts(video_id: int) -> None:
    cache.delete_many(
        [
            count_cache_key(video_id, "likes"),
            count_cache_key(video_id, "comments"),
        ]
    )
