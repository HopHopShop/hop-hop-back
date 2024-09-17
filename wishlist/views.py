from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from wishlist.services import WishlistService
from shop.models import Product
from utils.custom_exceptions import (
    ProductAlreadyExistException,
    ProductNotExistException,
)


@extend_schema(summary="Retrieve wishlist details")
class WishlistView(APIView):
    def get(self, request):
        products = WishlistService(request)

        session_id = request.session.get("session_key", None)

        return Response({"products": products, "sessionid": session_id}, status=status.HTTP_200_OK)


@extend_schema(summary="Add item to wishlist")
class AddToWishlistView(APIView):
    def post(self, request, product_id):
        wishlist_service = WishlistService(request)
        try:
            product = Product.objects.get(id=product_id)
            wishlist_service.add(product=product)
        except Product.DoesNotExist:
            raise ProductNotExistException
        except ProductAlreadyExistException:
            raise ProductAlreadyExistException

        session_id = request.session.get("session_key", None)

        return Response({"products": wishlist_service, "sessionid": session_id}, status=status.HTTP_200_OK)


@extend_schema(summary="Remove item from wishlist")
class RemoveFromWishlistView(APIView):
    def delete(self, request, product_id):
        wishlist_service = WishlistService(request)
        try:
            product = Product.objects.get(id=product_id)
            wishlist_service.remove(product=product)
        except Product.DoesNotExist:
            raise Product.DoesNotExist
        except ProductNotExistException:
            raise

        session_id = request.session.get("session_key", None)

        return Response({"products": wishlist_service, "sessionid": session_id}, status=status.HTTP_204_NO_CONTENT)
