from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile",)
    accepted_terms = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class State(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class District(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="districts",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("code", "state")
        ordering = ["id"]

    def __str__(self):
        return self.name

