from django.db import models
from django.conf import settings

class Productlike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
