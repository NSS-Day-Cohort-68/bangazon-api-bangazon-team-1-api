"""View module for handling requests about customer payment types"""

from django.http import HttpResponseServerError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from bangazonapi.models import Payment, Customer
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime


class PaymentSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for Payment

    Arguments:
        serializers
    """

    obscured_num = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        url = serializers.HyperlinkedIdentityField(
            view_name="payment", lookup_field="id"
        )
        fields = (
            "id",
            "url",
            "merchant_name",
            "account_number",
            "expiration_date",
            "create_date",
            "obscured_num",
        )

    def get_obscured_num(self, obj):
        account_num = obj.account_number
        return f"{'*' * (len(account_num) - 4)}{account_num[-4:]}"


class Payments(ViewSet):

    def create(self, request):
        """Handle POST operations

        Returns:
            Response -- JSON serialized payment instance
        """

        try:
            new_payment = Payment()

            merchant_name = request.data.get("merchant_name")
            if not merchant_name:
                merchant_name = request.data.get("merchant")

            account_number = request.data.get("account_number")
            if not account_number:
                account_number = request.data.get("acctNumber")

            customer = Customer.objects.get(user=request.auth.user)

            new_payment.merchant_name = merchant_name
            new_payment.account_number = account_number
            new_payment.expiration_date = request.data.get(
                "expiration_date", "0000-00-00"
            )
            new_payment.create_date = request.data.get(
                "create_date", datetime.now().date()
            )
            new_payment.customer = customer
            new_payment.save()

            serializer = PaymentSerializer(new_payment, context={"request": request})

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError as ex:
            return Response({"message": ex.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response(
                {"message": "Payment must include a valid expiration date"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def retrieve(self, request, pk=None):
        """Handle GET requests for single payment type

        Returns:
            Response -- JSON serialized payment_type instance
        """
        try:
            payment_type = Payment.objects.get(pk=pk)
            serializer = PaymentSerializer(payment_type, context={"request": request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single payment type

        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            payment = Payment.objects.get(pk=pk)
            payment.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Payment.DoesNotExist as ex:
            return Response({"message": ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response(
                {"message": ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        """Handle GET requests to payment type resource"""
        customer = Customer.objects.get(user=request.auth.user)
        payment_types = Payment.objects.filter(customer=customer)
        serializer = PaymentSerializer(
            payment_types, many=True, context={"request": request}
        )
        return Response(serializer.data)
