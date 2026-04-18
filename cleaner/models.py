from django.db import models

# Create your models here.

from django.contrib.auth.models import User

class CleanedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField()

    def __str__(self):
        return self.filename