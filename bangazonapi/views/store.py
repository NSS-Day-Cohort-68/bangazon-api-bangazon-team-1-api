from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from bangazonapi.models import Store, Customer


class StoreSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for stores"""

    class Meta:
        model = Store
        url = serializers.HyperlinkedIdentityField(view_name="store", lookup_field="id")
        fields = ("id", "customer_id", "name", "description")
        depth = 1


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
        @apiSuccess {String} customer_id Customer ID associated with the store.
        @apiSuccess {String} name Name of the store.
        @apiSuccess {String} description Description of the store.

        @apiSuccessExample Success
            {
                "id": 1,
                "customer_id": 5,
                "name": "Tech Emporium",
                "description": "Your one-stop shop for all things tech! Find the latest gadgets, accessories, and more."
            }
        """
        try:
            new_store = Store()
            new_store.name = request.data["name"]
            new_store.description = request.data["description"]

            customer = Customer.objects.get(user=request.auth.user)
            new_store.customer = customer

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
        @apiSuccess (200) {int} store.owner_id
        @apiSuccess (200) {String} store.name
        @apiSuccess (200) {String} store.description

        @apiSuccessExample Success
            {
                "id": 1,
                "customer_id": 5,
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
