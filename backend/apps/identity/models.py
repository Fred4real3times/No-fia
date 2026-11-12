from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Application identity; email is unique even while username remains Django-compatible."""
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=160, blank=True)

    def __str__(self) -> str:
        return self.email
