"""View module for handling requests about products"""

from rest_framework.decorators import action
from bangazonapi.models.productlike import Productlike
import base64
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.http import HttpResponseServerError
from django.db import IntegrityError
from django.shortcuts import render
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from bangazonapi.models import (
    Product,
    Customer,
    ProductCategory,
    ProductRating,
    Recommendation,
    OrderProduct,
    Order
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRating
        fields = ("id", "customer", "product", "rating", "review")


class ProductSerializer(serializers.ModelSerializer):
    """JSON serializer for products"""

    ratings = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "number_sold",
            "description",
            "quantity",
            "created_date",
            "location",
            "image_path",
            "average_rating",
            "customer_id",
            "ratings",
        )
        depth = 1


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = ("id", "customer", "product", "recommender")


class ProfileProductSerializer(serializers.ModelSerializer):
    """JSON serializer for products"""

    class Meta:
        model = Product
        fields = ("id", "name", "price", "description", "image_path")


class Products(ViewSet):
    """Request handlers for Products in the Bangazon Platform"""

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def create(self, request):
        """
        @api {POST} /products POST new product
        @apiName CreateProduct
        @apiGroup Product

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {String} name Short form name of product
        @apiParam {Number} price Cost of product
        @apiParam {String} description Long form description of product
        @apiParam {Number} quantity Number of items to sell
        @apiParam {String} location City where product is located
        @apiParam {Number} category_id Category of product
        @apiParamExample {json} Input
            {
                "name": "Kite",
                "price": 14.99,
                "description": "It flies high",
                "quantity": 60,
                "location": "Pittsburgh",
                "category_id": 4
            }

        @apiSuccess (200) {Object} product Created product
        @apiSuccess (200) {id} product.id Product Id
        @apiSuccess (200) {String} product.name Short form name of product
        @apiSuccess (200) {String} product.description Long form description of product
        @apiSuccess (200) {Number} product.price Cost of product
        @apiSuccess (200) {Number} product.quantity Number of items to sell
        @apiSuccess (200) {Date} product.created_date City where product is located
        @apiSuccess (200) {String} product.location City where product is located
        @apiSuccess (200) {String} product.image_path Path to product image
        @apiSuccess (200) {Number} product.average_rating Average customer rating of product
        @apiSuccess (200) {Number} product.number_sold How many items have been purchased
        @apiSuccess (200) {Object} product.category Category of product
        @apiSuccessExample {json} Success
            {
                "id": 101,
                "url": "http://localhost:8000/products/101",
                "name": "Kite",
                "price": 14.99,
                "number_sold": 0,
                "description": "It flies high",
                "quantity": 60,
                "created_date": "2019-10-23",
                "location": "Pittsburgh",
                "image_path": null,
                "average_rating": 0,
                "category": {
                    "url": "http://localhost:8000/productcategories/6",
                    "name": "Games/Toys"
                }
            }
        """
        new_product = Product()
        new_product.name = request.data["name"]
        new_product.price = request.data["price"]
        new_product.description = request.data["description"]
        new_product.quantity = request.data["quantity"]
        new_product.location = request.data["location"]

        customer = Customer.objects.get(user=request.auth.user)
        new_product.customer = customer

        product_category = ProductCategory.objects.get(pk=request.data["category_id"])
        new_product.category = product_category

        if "image_path" in request.data:
            format, imgstr = request.data["image_path"].split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{new_product.id}-{request.data["name"]}.{ext}',
            )

            new_product.image_path = data
        try:
            new_product.full_clean()
        except ValidationError as e:
            return Response({"error": e.messages}, status=status.HTTP_400_BAD_REQUEST)

        new_product.save()

        serializer = ProductSerializer(new_product, context={"request": request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """
        @api {GET} /products/:id GET product
        @apiName GetProduct
        @apiGroup Product

        @apiParam {id} id Product Id

        @apiSuccess (200) {Object} product Created product
        @apiSuccess (200) {id} product.id Product Id
        @apiSuccess (200) {String} product.name Short form name of product
        @apiSuccess (200) {String} product.description Long form description of product
        @apiSuccess (200) {Number} product.price Cost of product
        @apiSuccess (200) {Number} product.quantity Number of items to sell
        @apiSuccess (200) {Date} product.created_date City where product is located
        @apiSuccess (200) {String} product.location City where product is located
        @apiSuccess (200) {String} product.image_path Path to product image
        @apiSuccess (200) {Number} product.average_rating Average customer rating of product
        @apiSuccess (200) {Number} product.number_sold How many items have been purchased
        @apiSuccess (200) {Object} product.category Category of product
        @apiSuccessExample {json} Success
            {
                "id": 101,
                "url": "http://localhost:8000/products/101",
                "name": "Kite",
                "price": 14.99,
                "number_sold": 0,
                "description": "It flies high",
                "quantity": 60,
                "created_date": "2019-10-23",
                "location": "Pittsburgh",
                "image_path": null,
                "average_rating": 0,
                "category": {
                    "url": "http://localhost:8000/productcategories/6",
                    "name": "Games/Toys"
                }
            }
        """
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, context={"request": request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def update(self, request, pk=None):
        """
        @api {PUT} /products/:id PUT changes to product
        @apiName UpdateProduct
        @apiGroup Product

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} id Product Id to update
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        product = Product.objects.get(pk=pk)
        product.name = request.data["name"]
        product.price = request.data["price"]
        product.description = request.data["description"]
        product.quantity = request.data["quantity"]
        product.created_date = request.data["created_date"]
        product.location = request.data["location"]

        customer = Customer.objects.get(user=request.auth.user)
        product.customer = customer

        product_category = ProductCategory.objects.get(pk=request.data["category_id"])
        product.category = product_category
        product.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        """
        @api {DELETE} /products/:id DELETE product
        @apiName DeleteProduct
        @apiGroup Product

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} id Product Id to delete
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        try:
            product = Product.objects.get(pk=pk)
            product.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Product.DoesNotExist as ex:
            return Response({"message": ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response(
                {"message": ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        """
        @api {GET} /products GET all products
        @apiName ListProducts
        @apiGroup Product

        @apiSuccess (200) {Object[]} products Array of products
        @apiSuccessExample {json} Success
            [
                {
                    "id": 101,
                    "url": "http://localhost:8000/products/101",
                    "name": "Kite",
                    "price": 14.99,
                    "number_sold": 0,
                    "description": "It flies high",
                    "quantity": 60,
                    "created_date": "2019-10-23",
                    "location": "Pittsburgh",
                    "image_path": null,
                    "average_rating": 0,
                    "customer_id": 5,
                    "category": {
                        "url": "http://localhost:8000/productcategories/6",
                        "name": "Games/Toys"
                    }
                }
            ]
        """
        products = Product.objects.all()

        # Support filtering by category and/or quantity
        category = self.request.query_params.get("category", None)
        quantity = self.request.query_params.get("quantity", None)
        order = self.request.query_params.get("order_by", None)
        direction = self.request.query_params.get("direction", None)
        number_sold = self.request.query_params.get("number_sold", None)
        min_price = self.request.query_params.get("min_price", None)
        location = self.request.query_params.get("location", None)

        if location is not None:
            products = products.filter(location__contains=location)

        if order is not None:
            order_filter = order

            if direction is not None:
                if direction == "desc":
                    order_filter = f"-{order}"

            products = products.order_by(order_filter)

        if category is not None:
            products = products.filter(category__id=category)

        if quantity is not None:
            products = products.order_by("-created_date")[: int(quantity)]

        if number_sold is not None:

            def sold_filter(product):
                if product.number_sold >= int(number_sold):
                    return True
                return False

            products = filter(sold_filter, products)

        if min_price is not None:
            products = products.filter(price__gte=min_price)

        serializer = ProductSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(methods=["post"], detail=True)
    def recommend(self, request, pk=None):
        """Recommend products to other users"""

        if request.method == "POST":
            recipient = request.data.get("recipient")
            username = request.data.get("username")

            try:
                # get customer by id
                if recipient:
                    customer = Customer.objects.get(user__id=recipient)
                # get customer by username
                elif username:
                    customer = Customer.objects.get(user__username=username)
                else:
                    return Response(
                        {
                            "message": 'Either "recipient" or "username" must be provided'
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Customer.DoesNotExist:
                return Response(
                    {"message": "This user doesn't exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            recommender = Customer.objects.get(user=request.auth.user)

            if recommender == customer:
                return Response(
                    {"message": "You cannot recommend a product to yourself"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product = Product.objects.get(pk=pk)

            rec, created = Recommendation.objects.get_or_create(
                recommender=recommender, customer=customer, product=product
            )

            if not created:
                return Response(
                    {
                        "message": "You have already recommended this product to that user"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            rec.save()

            return Response(
                RecommendationSerializer(rec).data, status=status.HTTP_201_CREATED
            )

        return Response(None, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=["post"], detail=True)
    def rate_product(self, request, pk=None):
        """Rate a product"""
        product = Product.objects.get(pk=pk)
        customer = Customer.objects.get(user=request.auth.user)
        rating = request.data.get("rating")
        if not rating:
            rating = request.data.get("score")
        review = request.data.get("review", "")

        # check if customer has already rated this product
        existing_rating = ProductRating.objects.filter(
            product=product, customer=customer
        ).first()

        try:
            if (rating is not None) and ((rating < 1) or (rating > 5)):
                raise IntegrityError("Rating must be within range 1-5")

            if existing_rating:
                # update existing rating
                existing_rating.rating = rating
                existing_rating.review = review
                existing_rating.save()
                serializer = RatingSerializer(existing_rating)
            else:
                # create new rating
                new_rating = ProductRating.objects.create(
                    product=product, customer=customer, rating=rating, review=review
                )
                serializer = RatingSerializer(new_rating)
        except IntegrityError as ex:
            return Response({"message": ex.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def liked(self, request):
        """
        GET operation to retrieve all products liked by the current user.
        """
        try:
            # Retrieve all products liked by the current user
            liked_products = Productlike.objects.filter(user=request.user)
            # Serialize the liked products
            serializer = ProductSerializer(
                [product_like.product for product_like in liked_products], many=True
            )
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(methods=["delete"], detail=True)
    def remove_from_order(self, request, pk=None):
        """
        @api {DELETE} /products/:id/remove-from-order DELETE product from order
        @apiName RemoveProductFromOrder
        @apiGroup Product

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {id} id Product Id to remove from order
        @apiSuccessExample {json} Success
            HTTP/1.1 204 No Content
        """
        try:

            # Get the order product associated with the product
            order_product = OrderProduct.objects.get(pk=pk)

            # Remove the order product
            order_product.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except OrderProduct.DoesNotExist:
            return Response({"message": "Product not found in order"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({"message": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
def expensive_products(request):
    products = Product.objects.filter(price__gte=1000)
    product_data = [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        for product in products
    ]

    context = {"products": product_data}
    return render(request, "expensiveproducts.html", context)


def inexpensive_products(request):
    products = Product.objects.filter(price__lte=999)
    product_data = [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        for product in products
    ]

    context = {"products": product_data}
    return render(request, "inexpensiveproducts.html", context)
