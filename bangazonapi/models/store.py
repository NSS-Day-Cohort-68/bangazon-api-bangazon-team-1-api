from django.db import models
from django.contrib.auth.models import User
from .customer import Customer


class Store(models.Model):

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="stores"
    )
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100)
