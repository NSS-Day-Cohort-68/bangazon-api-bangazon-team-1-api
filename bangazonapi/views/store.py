from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import action
from bangazonapi.models import Store, Customer, Favorite


class SellerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")

    class Meta:
        model = Customer
        fields = ["id", "url", "first_name", "last_name"]


class StoreSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for stores"""

    seller = SellerSerializer()

    class Meta:
        model = Store
        url = serializers.HyperlinkedIdentityField(view_name="store", lookup_field="id")
        fields = ("id", "seller", "name", "description")
        depth = 1


class FavoriteStoreSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for stores"""

    class Meta:
        model = Store
        url = serializers.HyperlinkedIdentityField(view_name="store", lookup_field="id")
        fields = ("id", "name", "description")


class FavoriteSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for favorites

    Arguments:
        serializers
    """

    seller = SellerSerializer(many=False)
    customer = SellerSerializer(many=False)
    store = FavoriteStoreSerializer(source="seller.stores.first", many=False)

    class Meta:
        model = Favorite
        fields = ("id", "seller", "customer", "store")

    def get_store(self, obj):
        stores = obj.seller.stores.all()
        serializer = FavoriteStoreSerializer(
            stores, many=True, context={"request": self.context["request"]}
        )
        return serializer.data


class Stores(ViewSet):

    def create(self, request):
        """
        @api {POST} /stores POST new store
        @apiName CreateStore
        @apiGroup Store

        @apiHeader {String} Authorization Auth toke
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiParam {String} name Name of the store.
        @apiParam {String} description Description of the store.

        @apiSuccess {Number} id ID of the newly created store.
        @apiSuccess {String} seller Customer ID associated with the store.
        @apiSuccess {String} name Name of the store.
        @apiSuccess {String} description Description of the store.

        @apiSuccessExample Success
            {
                "id": 1,
                "seller": 5,
                "name": "Tech Emporium",
                "description": "Your one-stop shop for all things tech! Find the latest gadgets, accessories, and more."
            }
        """
        try:
            new_store = Store()
            new_store.name = request.data["name"]
            new_store.description = request.data["description"]

            seller = Customer.objects.get(user=request.auth.user)
            new_store.seller = seller

            new_store.save()

            serializer = StoreSerializer(new_store, context={"request": request})

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except KeyError:
            # Handle missing name or description in request data
            return Response(
                {"error": "Missing name or description in request data"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def retrieve(self, request, pk=None):
        """
        @api {GET} /stores/:id GET stores
        @apiName GetStore
        @apiGroup Store

        @apiParam {id} id Store Id

        @apiSuccess (200) {Object} store Created store
        @apiSuccess (200) {id} store.id Store id
        @apiSuccess (200) {int} store.seller
        @apiSuccess (200) {String} store.name
        @apiSuccess (200) {String} store.description

        @apiSuccessExample Success
            {
                "id": 1,
                "seller": 5,
                "name": "Tech Emporium",
                "description": "Your one-stop shop for all things tech! Find the latest gadgets, accessories, and more."
            }
        """
        try:
            store = Store.objects.get(pk=pk)
            serializer = StoreSerializer(store, context={"request": request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def list(self, request):
        """
        @api {GET} /stores GET all stores
        @apiName GetStores
        @apiGroup Store

        @apiSuccess {Array} stores List of stores.

        @apiSuccessExample Success
            [
                {
                "id": 2,
                "seller": {
                    "id": 6,
                    "first_name": "Jisie",
                    "last_name": "David"
                },
                "name": "Fashion Haven",
                "description": "Discover the trendiest clothing, shoes, and accessories here. Stay stylish all year round!"
            },
            {
                "id": 3,
                "seller": {
                    "id": 7,
                    "first_name": "Brenda",
                    "last_name": "Long"
                },
                "name": "Home Essentials",
                "description": "Transform your living space with our selection of home decor, furniture, and household essentials."
            }
            ]
        """

        stores = Store.objects.all()
        serializer = StoreSerializer(stores, many=True, context={"request": request})

        return Response(serializer.data)

    @action(methods=["post"], detail=True)
    def favorite(self, request, pk=None):
        """
        @api {POST} /stores/n/favorite POST a new favorite store
        @apiName AddFavoriteStore
        @apiGroup Stores

        @apiHeader {String} Authorization Auth token
        @apiHeaderExample {String} Authorization
            Token 9ba45f09651c5b0c404f37a2d2572c026c146611

        @apiBody {Number} pk The ID of the store to favorite

        @apiSuccessExample {json} Success
            HTTP/1.1 201 Created

        @apiError (400) {String} message Invalid input data
        @apiError (404) {String} message Store not found
        """
        try:
            current_user = Customer.objects.get(user=request.auth.user)
            store = Store.objects.get(pk=pk)

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
