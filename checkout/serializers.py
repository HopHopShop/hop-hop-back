import datetime
from decimal import Decimal

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from checkout.models import Order, OrderItem
from checkout.services import DashboardStatistic
from shop.serializers import ProductSerializer


class CardInformationSerializer(serializers.Serializer):
    @staticmethod
    def validate_card_number(value):
        value = value.replace(" ", "")
        if not value.isdigit():
            raise serializers.ValidationError("Card number is invalid")
        if not 13 <= len(value) <= 19:
            raise serializers.ValidationError("Card number is invalid")
        return value

    @staticmethod
    def check_expiry_month(value):
        if not 1 <= int(value) <= 12:
            raise serializers.ValidationError("Invalid expiry month.")

    @staticmethod
    def check_expiry_year(value):
        today = datetime.datetime.now()
        if not int(value) >= today.year:
            raise serializers.ValidationError("Invalid expiry year.")

    @staticmethod
    def check_cvc(value):
        if not 3 <= len(value) <= 4:
            raise serializers.ValidationError("Invalid cvc number.")

    @staticmethod
    def check_payment_method(value):
        payment_method = value.lower()
        if payment_method not in ["card"]:
            raise serializers.ValidationError("Invalid payment_method.")

    card_number = serializers.CharField(
        max_length=150, required=True, validators=[validate_card_number]
    )
    expiry_month = serializers.CharField(
        max_length=150,
        required=True,
        validators=[check_expiry_month],
    )
    expiry_year = serializers.CharField(
        max_length=150,
        required=True,
        validators=[check_expiry_year],
    )
    cvc = serializers.CharField(
        max_length=150,
        required=True,
        validators=[check_cvc],
    )


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = [
            "order",
            "product",
            "quantity",
            "price",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    total_quantity = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        return sum(item.quantity * item.price for item in obj.items.all())

    class Meta:
        model = Order
        fields = [
            "id",
            "payment_status",
            "order_status",
            "created_at",
            "total_quantity",
            "total_price",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    card_information = CardInformationSerializer(write_only=True, required=False)
    subtotal_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    tax_percent = serializers.SerializerMethodField()
    shipping_rate = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "first_name",
            "last_name",
            "email",
            "phone",
            "shipping_address",
            "shipping_postcode",
            "payment_id",
            "payment_type",
            "payment_status",
            "order_status",
            "items",
            "subtotal_price",
            "total_price",
            "coupon",
            "tax_percent",
            "shipping_rate",
            "discount",
            "card_information",
        ]
        read_only_fields = [
            "customer",
            "coupon",
            "payment_id",
            "payment_status",
            "order_status",
            "total_price",
            "created_at",
            "updated_at",
            "created_at"
        ]

    def validate(self, attrs):
        if attrs.get("payment_type", None) == "card" and not attrs.get("card_information", None):
            raise ValidationError("Card information is required for card payment type.")
        return attrs

    def get_subtotal_price(self, obj):
        return sum(item.quantity * item.price for item in obj.items.all())

    def get_tax_percent(self, obj):
        return Decimal(20)

    def get_shipping_rate(self, obj):
        return 20

    def get_discount(self, obj):
        if obj.coupon:
            return obj.coupon.discount

    def get_total_price(self, obj):
        discount = self.get_discount(obj) if obj.coupon else 0
        subtotal_price = self.get_subtotal_price(obj)
        tax = self.get_tax_percent(obj)
        shipping_rate = self.get_shipping_rate(obj)

        subtotal_price -= (subtotal_price * Decimal(discount / 100))
        subtotal_price -= (subtotal_price * Decimal(tax / 100))
        subtotal_price -= shipping_rate

        return subtotal_price

    def create(self, validated_data):
        validated_data.pop("card_information", None)
        order = Order.objects.create(**validated_data)
        return order

    def update(self, instance, validated_data):
        validated_data.pop("card_information", None)
        instance = super().update(instance, validated_data)
        return instance


class DashboardStatisticSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    active_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    returned_orders = serializers.IntegerField()
    total_orders_growth = serializers.FloatField()
    active_orders_growth = serializers.FloatField()
    completed_orders_growth = serializers.FloatField()
    returned_orders_growth = serializers.FloatField()

    def create(self, validated_data):
        return DashboardStatistic(**validated_data)
