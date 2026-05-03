from .models import Notification


def notify_like(*, actor, video) -> None:
    if video.user_id == actor.id:
        return
    Notification.objects.create(
        recipient_id=video.user_id,
        actor=actor,
        kind=Notification.Kind.LIKE,
        video=video,
    )


def notify_comment(*, actor, video) -> None:
    if video.user_id == actor.id:
        return
    Notification.objects.create(
        recipient_id=video.user_id,
        actor=actor,
        kind=Notification.Kind.COMMENT,
        video=video,
    )


def notify_follow(*, actor, following_user_id: int) -> None:
    if following_user_id == actor.id:
        return
    Notification.objects.create(
        recipient_id=following_user_id,
        actor=actor,
        kind=Notification.Kind.FOLLOW,
        video=None,
    )
