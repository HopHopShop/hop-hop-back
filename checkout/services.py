from dataclasses import dataclass
from datetime import timedelta

import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from cart.services import CartSessionService
from checkout.models import Order, OrderItem, OrderStatus
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response

from cart.services import CartSessionService, CartDBService
from shop.models import Product
from utils.custom_exceptions import (
    CartEmptyException,
    StripeCardError,
    StripeRateLimitError,
    StripeInvalidRequestError,
    StripeAuthenticationError,
    StripeAPIConnectionError,
    StripeGeneralError,
)
from utils.repeatable_functions import convert_price

stripe.api_key = settings.STRIPE_SECRET_KEY


@dataclass
class OrderData:
    def __init__(
            self, order=None, order_items=None, card_information=None, total_price=0
    ):
        self.order = order
        self.order_items = order_items
        self.card_information = card_information
        self.total_price = total_price


class OrderService:
    def __init__(self, request):
        self.request = request
        if self.request.user.is_authenticated:
            self.cart_service = CartDBService(self.request.user)
        else:
            self.cart_service = CartSessionService(self.request)

    def create_order(self, validated_data: dict):
        if not self._is_cart_not_empty():
            raise CartEmptyException

        card_information = validated_data.pop("card_information", None)
        coupon_id = self.cart_service.coupon_id if self.cart_service.coupon_id else None
        validated_data["coupon_id"] = coupon_id

        customer = self.request.user if isinstance(self.cart_service, CartDBService) else None

        order = self._create_order_instance(validated_data, customer)
        validated_data.pop("coupon_id", None)

        order_items = self._create_order_items(order)

        total_price = self.cart_service.get_total_price()
        return OrderData(order, order_items, card_information, total_price)

    def _is_cart_not_empty(self) -> bool:
        return self.cart_service.get_total_price() > 0

    def _create_order_instance(self, validated_data: dict, customer: get_user_model() = None) -> Order:
        return Order.objects.create(**validated_data, customer=customer)

    def _create_order_items(self, order: Order) -> list:
        items_data = self._get_cart_items()
        order_items = []
        for item_data in items_data:
            order_item = OrderItem.objects.create(order=order, **item_data)
            order_items.append(order_item)
        return order_items

    def _get_cart_items(self):
        return [
            {
                "product": Product.objects.get(id=item["product"]["id"]),
                "quantity": item["quantity"],
                "price": item["total_price"]
            }
            for item in self.cart_service
        ]

    def clear_cart(self):
        self.cart_service.clear()


class PaymentService:
    @staticmethod
    def stripe_card_payment(
            card_information: dict, total_price: float
    ) -> Response | Exception:
        payment_method_data = {
            "type": "card",
            "card": {
                "number": card_information["card_number"],
                "exp_month": card_information["expiry_month"],
                "exp_year": card_information["expiry_year"],
                "cvc": card_information["cvc"],
            },
        }
        try:
            payment = stripe.PaymentIntent.create(
                amount=int(total_price * 100),
                currency="usd",
                payment_method_data=payment_method_data,
                confirm=True,
                return_url="http://127.0.0.1:8000/api/doc/",
            )
            data = {"payment_id": payment["payment_method"]}
            return Response(data=data, status=status.HTTP_200_OK)
        except stripe.error.CardError as e:
            raise StripeCardError(detail=str(e.user_message))

        except stripe.error.RateLimitError as e:
            raise StripeRateLimitError(detail=str(e))

        except stripe.error.InvalidRequestError as e:
            raise StripeInvalidRequestError(detail=str(e))

        except stripe.error.AuthenticationError as e:
            raise StripeAuthenticationError(detail=str(e))

        except stripe.error.APIConnectionError as e:
            raise StripeAPIConnectionError(detail=str(e))

        except stripe.error.StripeError as e:
            raise StripeGeneralError(detail=str(e))


@dataclass
class DashboardStatistic:
    total_orders: int
    active_orders: int
    completed_orders: int
    returned_orders: int
    total_orders_growth: float
    active_orders_growth: float
    completed_orders_growth: float
    returned_orders_growth: float


class DashboardStatisticService:
    def __init__(self, period: int):
        self.period = period

    def get_order_statistics(self) -> DashboardStatistic:
        start_date = timezone.now() - timedelta(days=self.period)
        orders = Order.objects.filter(created_at__gte=start_date)

        total_orders = orders.count()
        active_orders = orders.filter(
            order_status__in=(
                OrderStatus.STATUS_PENDING,
                OrderStatus.STATUS_IN_PROGRESS,
                OrderStatus.STATUS_IN_TRANSIT,
            )
        ).count()

        completed_orders = orders.filter(
            order_status=OrderStatus.STATUS_DELIVERED
        ).count()

        returned_orders = orders.filter(
            order_status=OrderStatus.STATUS_RETURNED
        ).count()

        previous_start_date = start_date - timedelta(days=self.period)
        previous_orders = Order.objects.filter(
            created_at__gte=previous_start_date,
            created_at__lt=start_date,
        )

        previous_total_orders = previous_orders.count()
        previous_active_orders = previous_orders.filter(
            order_status__in=(
                OrderStatus.STATUS_PENDING,
                OrderStatus.STATUS_IN_PROGRESS,
                OrderStatus.STATUS_IN_TRANSIT,
            )
        ).count()

        previous_completed_orders = previous_orders.filter(
            order_status=OrderStatus.STATUS_DELIVERED
        ).count()

        previous_returned_orders = previous_orders.filter(
            order_status=OrderStatus.STATUS_RETURNED
        ).count()

        total_orders_growth = self.calculate_growth(total_orders, previous_total_orders)
        active_orders_growth = self.calculate_growth(active_orders, previous_active_orders)
        completed_orders_growth = self.calculate_growth(completed_orders, previous_completed_orders)
        returned_orders_growth = self.calculate_growth(returned_orders, previous_returned_orders)

        return DashboardStatistic(
            total_orders=total_orders,
            active_orders=active_orders,
            completed_orders=completed_orders,
            returned_orders=returned_orders,
            total_orders_growth=total_orders_growth,
            active_orders_growth=active_orders_growth,
            completed_orders_growth=completed_orders_growth,
            returned_orders_growth=returned_orders_growth,
        )

    def calculate_growth(self, current: int, previous: int) -> float:
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100
