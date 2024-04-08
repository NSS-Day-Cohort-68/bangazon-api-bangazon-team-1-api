from rest_framework import serializers
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from bangazonapi.models import Productlike
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from .product import ProductSerializer
from bangazonapi.models import Product
from django.db import IntegrityError

class ProductLikeSerializer(serializers.ModelSerializer):
    """Serializer for ProductLike model"""

    class Meta:
        model = Productlike 
        fields = ('id', 'user', 'product')

class ProductLikes(ViewSet):
    """Request handlers for Product Likes"""

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def create(self, request, product_id=None):
        """
        POST operation to like a product.
        """
        try:
            product = Product.objects.get(pk=product_id)
            product_like, created = Productlike.objects.get_or_create(product=product, user=request.user)
            if created:
                product_like.save()
                serializer = ProductLikeSerializer(product_like)
                return Response(serializer.data)
            else:
                return Response({'message': 'Product is already liked.'}, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({'message': 'Product does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'message': 'Integrity error. Unable to create like.'}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, product_id=None):
        """
        DELETE operation to unlike a product.
        """
        try:
            product_like = Productlike.objects.get(product_id=product_id, user=request.user)
            product_like.delete()
            return Response({'message': 'Productlike deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except Productlike.DoesNotExist:
            return Response({'message': 'Productlike does not exist.'}, status=status.HTTP_404_NOT_FOUND)
