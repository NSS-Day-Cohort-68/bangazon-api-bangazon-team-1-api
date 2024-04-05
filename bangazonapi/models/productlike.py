from django.db import models
from django.conf import settings
from .product import Product  # Import your Product model

class Productlike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Use ForeignKey relationship with the Product model
    created_at = models.DateTimeField(auto_now_add=True)
