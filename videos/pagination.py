from rest_framework.pagination import CursorPagination, LimitOffsetPagination


class FeedCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 30
    ordering = "-created_at"


class CommentCursorPagination(CursorPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = "-created_at"


class FollowRelationPagination(LimitOffsetPagination):
    default_limit = 30
    max_limit = 100
