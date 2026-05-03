from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.FileField(upload_to="avatars/", blank=True, null=True)
    avatar_url = models.URLField(max_length=512, blank=True, null=True)
    bio = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return self.username
