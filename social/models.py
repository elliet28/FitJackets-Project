from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Challenge(models.Model):
    CHALLENGE_TYPES = [
        ("weight_lifted", "Weight Lifted"),
        ("active_days", "Active Days"),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES)
    members = models.JSONField(default=dict, blank=True, null=True) # Dictionary to store member IDs and their associated values

    def __str__(self):
        return self.name
