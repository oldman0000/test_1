from django.contrib.auth.models import User
from django.db import models


class Comment(models.Model):
    name = models.CharField(max_length=50)
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}: {self.text[:30]}"