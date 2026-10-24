from datetime import timedelta
from django.db import models
from django.utils import timezone


class LoginCode(models.Model):
    email = models.EmailField()
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.IntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)


class CodeRequest(models.Model):
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)