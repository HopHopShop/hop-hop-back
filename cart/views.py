from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Coupon
from cart.serializers import CouponSerializer, UseCouponSerializer, CartSerializer
from shop.models import Product
from cart.services import CartService
from utils.custom_exceptions import (
    ProductNotExistException, CouponNotExistException,
)
from utils.pagination import Pagination


def cart_session_response(cart_service):
    cart_items = cart_service
    total_price = cart_service.get_total_price()
    total_items = cart_service.get_total_item()
    session_id = cart_service.get_session_id()

    coupon_is_used = cart_service.coupon_is_used()
    coupon = cart_service.get_coupon()
    if coupon:
        coupon_data = {
            "name": coupon.code,
            "discount": coupon.discount,
        }
    else:
        coupon_data = None
        coupon_is_used = False

    return {
        "products": cart_items,
        "total_items": total_items,
        "subtotal_price": total_price,
        "total_price": total_price,
        "coupon_is_used": coupon_is_used,
        "coupon": coupon_data,
        "sessionid": session_id
    }


@extend_schema(summary="Retrieve cart details")
class CartDetailView(APIView):
    """
    Retrieve the details of the cart.
    """

    serializer_class = CartSerializer

    def get(self, request):
        cart = CartService(request)
        response_data = cart_session_response(cart)

        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(summary="Add item to cart")
class CartAddItemView(APIView):
    """
    Add an item to the cart.
    """

    serializer_class = CartSerializer

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ProductNotExistException

        cart = CartService(request)
        cart.add(
            product=product,
            quantity=request.data.get("quantity", 1),
            update_quantity=request.data.get("update_quantity", False),
        )
        response_data = cart_session_response(cart)
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(summary="Remove item from cart")
class CartRemoveItemView(APIView):
    """
    Remove an item from the cart.
    """

    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ProductNotExistException

        cart = CartService(request)
        cart.remove(product)
        response_data = cart_session_response(cart)
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(summary="Subtract item quantity in cart")
class CartSubtractItemView(APIView):
    """
    Subtract the quantity of an item in the cart.
    """

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise ProductNotExistException

        cart = CartService(request)
        cart.subtract_quantity(product)
        response_data = cart_session_response(cart)
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(tags=["coupon"], summary="Apply coupon")
class UseCouponView(APIView):
    """
    Apply a coupon to the cart.
    """

    serializer_class = UseCouponSerializer

    def post(self, request):
        code = request.data.get("code")
        try:
            coupon = Coupon.objects.get(code=code, active=True)
        except Coupon.DoesNotExist:
            raise CouponNotExistException

        cart = CartService(request)
        cart.add_coupon(coupon)
        response_data = cart_session_response(cart)
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(tags=["coupon"], summary="Cancel applied coupon")
class RemoveCouponView(APIView):
    """
    Remove an applied coupon from the cart.
    """

    def post(self, request):
        cart = CartService(request)
        cart.remove_coupon()
        response_data = cart_session_response(cart)
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(tags=["coupon"])
class CouponView(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['id']
    pagination_class = Pagination
    http_method_names = ["get", "post", "patch", "delete"]

    @extend_schema(
        summary="Retrieve a list of coupons",
        description="This endpoint returns a list of all coupons.",
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
        summary="Create a new coupon",
        description="This endpoint allows you to create a new coupon. You need to provide the required fields.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a specific coupon",
        description="This endpoint returns the details of a specific coupon identified by its ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update an existing coupon",
        description="This endpoint allows you to update an existing coupon identified by its ID. You only need to provide the fields you want to update.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a coupon",
        description="This endpoint allows you to delete a coupon identified by its ID.",
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Coupon deleted successfully."}, status=status.HTTP_200_OK
        )
