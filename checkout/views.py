import json

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from checkout.filters import OrderFilter
from checkout.models import Order
from checkout.serializers import (
    OrderSerializer,
    OrderListSerializer,
    DashboardStatisticSerializer,
)
from checkout.services import (
    OrderService,
    PaymentService,
    DashboardStatisticService,
)
from checkout.tasks.order_notification import send_notification_mail
from checkout.utils import send_webhook_email
from utils.pagination import Pagination


@extend_schema(tags=["checkout"], summary="Checkout for specific payment method")
class CheckoutView(generics.CreateAPIView):
    serializer_class = OrderSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid(raise_exception=True):
            order_service = OrderService(request)
            order_data = order_service.create_order(serializer.validated_data)
            serializer.validated_data["order_id"] = order_data.order.id

            payment_id = None
            if serializer.validated_data.get('payment_type', None) == 'card':
                payment_service = PaymentService()

                response = payment_service.stripe_card_payment(
                    order_data.card_information, order_data.total_price
                )

                if response.status_code != status.HTTP_200_OK:
                    order_data.order.payment_status = "Failed"
                    return response
                else:
                    payment_id = response.data.get("payment_id")

            order_data.order.payment_status = "pending"
            order_data.order.payment_id = payment_id
            order_data.order.save()

            # send_notification_mail.delay(user_email=order_data.order.email)

            order_service.clear_cart()

            return Response(
                {
                    "order": serializer.validated_data,
                    "payment_id": payment_id,
                    "message": "Order created and payment successful",
                    "sessionid": request.session.session_key,
                },
                status=status.HTTP_201_CREATED,
            )


@extend_schema(tags=["orders"], summary="Get all orders")
class OrderListView(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    pagination_class = Pagination
    filterset_class = OrderFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['id']

    queryset = Order.objects.all().select_related("customer")
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    @extend_schema(
        summary="Retrieve a list of orders",
        description="This endpoint returns a list of all orders.",
        parameters=[
            OpenApiParameter(
                name="ordering",
                description="Ordering by ID (id - for ascending order, -id for descending)",
                required=False,
                type=str,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve an order by ID",
        description="This endpoint returns details of a specific order identified by its ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update an order",
        description="This endpoint allows you to partially update an existing order.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete an order",
        description="This endpoint allows you to delete an existing order.",
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Order deleted successfully."}, status=status.HTTP_200_OK
        )


class ProfileOrder(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    queryset = Order.objects.all().select_related("customer")
    serializer_class = OrderSerializer

    def get_object(self):
        return self.request.user


class OrderStatisticsView(APIView):
    @extend_schema(
        summary="Retrieve order statistics",
        description="Returns the order statistics for a specified period (in days), including total orders, active orders, completed orders, and returned orders.",
        parameters=[
            OpenApiParameter(
                name="period",
                description="The number of days to calculate statistics for",
                required=True,
                type=int,
            )
        ],
    )
    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", 30)
        try:
            period = int(period)
        except ValueError:
            return Response(
                {"error": "Invalid 'days' parameter. It should be an integer."},
                status=400,
            )
        service = DashboardStatisticService(period=period)
        statistics = service.get_order_statistics()
        serializer = DashboardStatisticSerializer(statistics)
        return Response(serializer.data)


@extend_schema(tags=["coinbase"])
class CoinBaseWebhookView(APIView):
    @extend_schema(
        summary="Coin base webhook",
        description="Sends data to reserved email"
    )
    def post(self, request, *args, **kwargs):
        json_data = json.dumps(request.data)
        send_webhook_email(json_data)
        return Response({"detail": "Message was sent successfully!"}, status=status.HTTP_200_OK)
