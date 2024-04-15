"""View module for handling requests about customer profiles"""

import datetime
from django.http import HttpResponseServerError, JsonResponse
from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from bangazonapi.models import (
    Order,
    Customer,
    Product,
    Recommendation,
    OrderProduct,
    Favorite,
    Store,
)
from .product import ProfileProductSerializer
from .order import OrderSerializer
from .store import FavoriteSerializer

User = get_user_model()


def get_unique_recs(data, key="customer"):
    unique_products = {}

    for item in data:
        product = item["product"]
        given_key = item[key]

        if product["id"] not in unique_products:
            unique_products[product["id"]] = {"product": product, (key + "s"): []}

        unique_products[product["id"]][(key + "s")].append(given_key)

    out = list(unique_products.values())
    return out


class Profile(ViewSet):
    """Request handlers for user profile info in the Bangazon Platform"""

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def list(self, request):
        """
        @api {GET} /profile GET user profile info
        @apiName GetProfile
        @apiGroup UserProfile

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiSuccess (200) {Number} id Profile id
        @apiSuccess (200) {String} url URI of customer profile
        @apiSuccess (200) {Object} user Related user object
        @apiSuccess (200) {String} user.first_name Customer first name
        @apiSuccess (200) {String} user.last_name Customer last name
        @apiSuccess (200) {String} user.email Customer email
        @apiSuccess (200) {String} phone_number Customer phone number
        @apiSuccess (200) {String} address Customer address
        @apiSuccess (200) {Object[]} payment_types Array of user's payment types
        @apiSuccess (200) {Object[]} recommends Array of recommendations made by the user

        @apiSuccessExample {json} Success
            HTTP/1.1 200 OK
            {
                "id": 7,
                "url": "http://localhost:8000/customers/7",
                "user": {
                    "first_name": "Brenda",
                    "last_name": "Long",
                    "email": "brenda@brendalong.com"
                },
                "phone_number": "555-1212",
                "address": "100 Indefatiguable Way",
                "payment_types": [
                    {
                        "url": "http://localhost:8000/paymenttypes/3",
                        "deleted": null,
                        "merchant_name": "Visa",
                        "account_number": "fj0398fjw0g89434",
                        "expiration_date": "2020-03-01",
                        "create_date": "2019-03-11",
                        "customer": "http://localhost:8000/customers/7"
                    }
                ],
                "recommends": [
                    {
                        "product": {
                            "id": 32,
                            "name": "DB9"
                        },
                        "customer": {
                            "id": 5,
                            "user": {
                                "first_name": "Joe",
                                "last_name": "Shepherd",
                                "email": "joe@joeshepherd.com"
                            }
                        }
                    }
                ]
            }
        """
        try:
            current_user = Customer.objects.get(user=request.auth.user)
            current_user.recommends = Recommendation.objects.filter(
                recommender=current_user
            )

            serializer = ProfileSerializer(
                current_user, many=False, context={"request": request}
            )
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    @action(methods=["get", "post", "delete"], detail=False)
    def cart(self, request):
        """Shopping cart manipulation"""

        current_user = Customer.objects.get(user=request.auth.user)

        if request.method == "DELETE":
            """
            @api {DELETE} /profile/cart DELETE all line items in cart
            @apiName DeleteCart
            @apiGroup UserProfile

            @apiHeader {String} Authorization Auth token
            @apiHeaderExample {String} Authorization
                Token 9ba45f09651c5b0c404f37a2d2572c026c146611

            @apiSuccessExample {json} Success
                HTTP/1.1 204 No Content
            @apiError (404) {String} message  Not found message.
            """
            try:

                open_order = Order.objects.get(customer=current_user, payment_type=None)
                line_items = OrderProduct.objects.filter(order=open_order)
                line_items.delete()
                open_order.delete()
            except Order.DoesNotExist as ex:
                return Response(
                    {"message": ex.args[0]}, status=status.HTTP_404_NOT_FOUND
                )

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        if request.method == "GET":
            """
            @api {GET} /profile/cart GET line items in cart
            @apiName GetCart
            @apiGroup UserProfile

            @apiHeader {String} Authorization Auth token
            @apiHeaderExample {String} Authorization
                Token 9ba45f09651c5b0c404f37a2d2572c026c146611

            @apiSuccess (200) {Number} id Order cart
            @apiSuccess (200) {String} url URL of order
            @apiSuccess (200) {String} created_date Date created
            @apiSuccess (200) {Object} payment_type Payment Id used to complete order
            @apiSuccess (200) {String} customer URI for customer
            @apiSuccess (200) {Number} size Number of items in cart
            @apiSuccess (200) {Object[]} line_items Line items in cart
            @apiSuccess (200) {Number} line_items.id Line item id
            @apiSuccess (200) {Object} line_items.product Product in cart
            @apiSuccessExample {json} Success
                {
                    "id": 2,
                    "url": "http://localhost:8000/orders/2",
                    "created_date": "2019-04-12",
                    "payment_type": null,
                    "customer": "http://localhost:8000/customers/7",
                    "line_items": [
                        {
                            "id": 4,
                            "product": {
                                "id": 52,
                                "url": "http://localhost:8000/products/52",
                                "name": "900",
                                "price": 1296.98,
                                "number_sold": 0,
                                "description": "1987 Saab",
                                "quantity": 2,
                                "created_date": "2019-03-19",
                                "location": "Vratsa",
                                "image_path": null,
                                "average_rating": 0,
                                "category": {
                                    "url": "http://localhost:8000/productcategories/2",
                                    "name": "Auto"
                                }
                            }
                        }
                    ],
                    "size": 1
                }
            @apiError (404) {String} message  Not found message
            """
            try:
                open_order = Order.objects.get(customer=current_user, payment_type=None)
                line_items = OrderProduct.objects.filter(order=open_order)
                line_items = LineItemSerializer(
                    line_items, many=True, context={"request": request}
                )

                cart = {}
                cart["order"] = OrderSerializer(
                    open_order, many=False, context={"request": request}
                ).data
                cart["order"]["size"] = len(line_items.data)

            except Order.DoesNotExist as ex:
                return Response(
                    {"message": ex.args[0]}, status=status.HTTP_404_NOT_FOUND
                )
            return Response(cart["order"])

        if request.method == "POST":
            """
            @api {POST} /profile/cart POST new product to cart
            @apiName AddToCart
            @apiGroup UserProfile

            @apiHeader {String} Authorization Auth token
            @apiHeaderExample {String} Authorization
                Token 9ba45f09651c5b0c404f37a2d2572c026c146611

            @apiSuccess (200) {Object} line_item Line items in cart
            @apiSuccess (200) {Number} line_item.id Line item id
            @apiSuccess (200) {Object} line_item.product Product in cart
            @apiSuccess (200) {Object} line_item.order Open order for cart
            @apiSuccessExample {json} Success
                {
                    "id": 14,
                    "product": {
                        "url": "http://localhost:8000/products/52",
                        "deleted": null,
                        "name": "900",
                        "price": 1296.98,
                        "description": "1987 Saab",
                        "quantity": 2,
                        "created_date": "2019-03-19",
                        "location": "Vratsa",
                        "image_path": null,
                        "customer": "http://localhost:8000/customers/7",
                        "category": "http://localhost:8000/productcategories/2"
                    },
                    "order": {
                        "url": "http://localhost:8000/orders/2",
                        "created_date": "2019-04-12",
                        "customer": "http://localhost:8000/customers/7",
                        "payment_type": null
                    }
                }

            @apiError (404) {String} message  Not found message
            """

            try:
                open_order = Order.objects.get(customer=current_user)
            except Order.DoesNotExist:
                open_order = Order.objects.create(
                    customer=current_user, created_date=datetime.datetime.now()
                )

            try:
                product_id = request.data.get("product_id")
                if product_id is None:
                    raise KeyError("Product ID is required in the request body")
                product = Product.objects.get(pk=product_id)
            except KeyError as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Product.DoesNotExist:
                return Response(
                    {"message": "Product not found with the provided ID"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            line_item = OrderProduct(product=product, order=open_order)
            line_item.save()

            line_item_json = LineItemSerializer(
                line_item, many=False, context={"request": request}
            )

            return Response(line_item_json.data)

        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(methods=["get", "post"], detail=False)
    def favoritesellers(self, request):

        current_user = Customer.objects.get(user=request.auth.user)

        if request.method == "GET":
            """
            @api {GET} /profile/favoritesellers GET favorite sellers
            @apiName GetFavoriteSellers
            @apiGroup UserProfile

            @apiHeader {String} Authorization Auth token
            @apiHeaderExample {String} Authorization
                Token 9ba45f09651c5b0c404f37a2d2572c026c146611

            @apiSuccess (200) {id} id Favorite id
            @apiSuccess (200) {Object} seller Favorited seller
            @apiSuccess (200) {String} seller.url Seller URI
            @apiSuccess (200) {String} seller.phone_number Seller phone number
            @apiSuccess (200) {String} seller.address Seller address
            @apiSuccess (200) {String} seller.user Seller user profile URI
            @apiSuccessExample {json} Success
                [
                    {
                        "id": 1,
                        "seller": {
                            "url": "http://localhost:8000/customers/5",
                            "phone_number": "555-1212",
                            "address": "100 Endless Way",
                            "user": "http://localhost:8000/users/6"
                        }
                    },
                    {
                        "id": 2,
                        "seller": {
                            "url": "http://localhost:8000/customers/6",
                            "phone_number": "555-1212",
                            "address": "100 Dauntless Way",
                            "user": "http://localhost:8000/users/7"
                        }
                    },
                    {
                        "id": 3,
                        "seller": {
                            "url": "http://localhost:8000/customers/7",
                            "phone_number": "555-1212",
                            "address": "100 Indefatiguable Way",
                            "user": "http://localhost:8000/users/8"
                        }
                    }
                ]
            """

            favorites = Favorite.objects.filter(customer=current_user)
            serializer = FavoriteSerializer(
                favorites, many=True, context={"request": request}
            )
            return Response(serializer.data)

        if request.method == "POST":
            """
            @api {POST} /profile/favoritesellers POST a new favorite seller
            @apiName AddFavoriteSeller
            @apiGroup UserProfile

            @apiHeader {String} Authorization Auth token
            @apiHeaderExample {String} Authorization
                Token 9ba45f09651c5b0c404f37a2d2572c026c146611

            @apiBody {Number} store_id The ID of the store to favorite

            @apiSuccessExample {json} Success
                HTTP/1.1 201 Created

            @apiError (400) {String} message Invalid input data
            @apiError (404) {String} message Store not found
            """

            store_id = request.data.get("store_id")

            if not store_id:
                return Response(
                    {"message": "Store ID is required in the request body"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                store = Store.objects.get(id=store_id)

                if store.seller == current_user:
                    return Response(
                        {"message": "You cannot favorite your own store."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if Favorite.objects.filter(
                    customer=current_user, seller=store.seller
                ).exists():
                    return Response(
                        {"message": "You have already favorited this store."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                favorite = Favorite(customer=current_user, seller=store.seller)
                favorite.save()

                return Response(
                    FavoriteSerializer(
                        favorite, many=False, context={"request": request}
                    ).data,
                    status=status.HTTP_201_CREATED,
                )
            except Store.DoesNotExist:
                return Response(
                    {"message": "Store not found with provided ID"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def favoritesellers_report(request):

    customer_id = request.GET.get("customer")

    if customer_id is not None:
        try:
            customer = Customer.objects.get(id=customer_id)

            favorite_sellers = Favorite.objects.filter(customer_id=customer_id)

            seller_ids = [favorite.seller_id for favorite in favorite_sellers]
            sellers = User.objects.filter(id__in=seller_ids)
            serialized_sellers = FavoriteUserSerializer(sellers, many=True)

            context = {
                "customer": customer,
                "favorite_sellers": serialized_sellers.data,
            }
            return render(request, "favoritesellers.html", context)
        except Customer.DoesNotExist:
            return JsonResponse(
                {"error": "Customer does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class LineItemSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for products

    Arguments:
        serializers
    """

    product = ProfileProductSerializer(many=False)

    class Meta:
        model = OrderProduct
        fields = ("id", "product")
        depth = 1


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for customer profile

    Arguments:
        serializers
    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        depth = 1


class CustomerSerializer(serializers.ModelSerializer):
    """JSON serializer for recommendation customers"""

    user = UserSerializer()

    class Meta:
        model = Customer
        fields = (
            "id",
            "user",
        )


class RecommenderSerializer(serializers.ModelSerializer):
    """JSON serializer for recommendations"""

    customer = CustomerSerializer()
    product = ProfileProductSerializer()

    class Meta:
        model = Recommendation
        fields = (
            "product",
            "customer",
        )


class RecommendationSerializer(serializers.ModelSerializer):
    """JSON serializer for recommendations"""

    product = ProfileProductSerializer()
    recommender = CustomerSerializer()

    class Meta:
        model = Recommendation
        fields = (
            "product",
            "recommender",
        )


class FavoriteUserSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for favorite sellers user

    Arguments:
        serializers
    """

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username")
        depth = 1


class FavoriteSellerSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for favorite sellers

    Arguments:
        serializers
    """

    user = FavoriteUserSerializer(many=False)

    class Meta:
        model = Customer
        fields = (
            "id",
            "url",
            "user",
        )
        depth = 1


class ProfileSerializer(serializers.ModelSerializer):
    """JSON serializer for customer profile

    Arguments:
        serializers
    """

    user = UserSerializer(many=False)
    favorites = FavoriteSerializer(many=True)
    recommended_by = serializers.SerializerMethodField()
    recommendations = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = (
            "id",
            "url",
            "user",
            "phone_number",
            "address",
            "payment_types",
            "recommended_by",
            "favorites",
            "recommendations",
        )

        depth = 1

    def get_recommended_by(self, obj):
        recs = Recommendation.objects.filter(recommender=obj)
        serializer = RecommenderSerializer(recs, many=True)

        return get_unique_recs(serializer.data)

    def get_recommendations(self, obj):
        recs = Recommendation.objects.filter(customer=obj)
        serializer = RecommendationSerializer(recs, many=True)

        return get_unique_recs(serializer.data, "recommender")
