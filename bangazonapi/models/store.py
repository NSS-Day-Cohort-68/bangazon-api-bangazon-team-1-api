from django.db import models
from django.contrib.auth.models import User


class Store(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    store_name = models.CharField(max_length=20)
    store_desc = models.CharField(max_length=100)

