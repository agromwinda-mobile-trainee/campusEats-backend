from __future__ import annotations


def absolute_media_url(request, url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith(("http://", "https://")):
        return url
    if request is not None:
        return request.build_absolute_uri(url)
    return url


def user_avatar_absolute_url(user, request) -> str | None:
    if getattr(user, "avatar", None) and user.avatar:
        try:
            path = user.avatar.url
        except ValueError:
            path = None
        if path:
            return absolute_media_url(request, path)
    if getattr(user, "avatar_url", None):
        return absolute_media_url(request, user.avatar_url)
    return None


def file_field_absolute_url(request, file_field) -> str | None:
    if not file_field:
        return None
    try:
        path = file_field.url
    except ValueError:
        return None
    return absolute_media_url(request, path)
