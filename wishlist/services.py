from django.conf import settings
from shop.models import Product
from shop.serializers import ProductSerializer
from utils.custom_exceptions import (
    ProductAlreadyExistException,
    ProductNotExistException,
)


class WishlistService:

    def __init__(self, request):
        self.session = request.session
        wishlist = self.session.get(settings.WISHLIST_SESSION_ID)
        if not wishlist:
            wishlist = self.session[settings.WISHLIST_SESSION_ID] = {}
        self.wishlist = wishlist
        self.session.save()

    def __iter__(self):
        product_ids = self.wishlist.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            wishlist_item = {
                "product": ProductSerializer(product).data,
            }
            yield wishlist_item

    def save(self) -> None:
        """
        Saves the wishlist to the session
        """
        self.session.modified = True

    def add(self, product: Product) -> None:
        """
        Adds a product to the wishlist
        """
        product_id = str(product.id)
        if product_id in self.wishlist:
            raise ProductAlreadyExistException
        self.wishlist[product_id] = {"product": ProductSerializer(product).data}
        self.save()

    def remove(self, product: Product) -> None:
        """
        Removes the product from the wishlist
        """
        product_id = str(product.id)
        if product_id not in self.wishlist:
            raise ProductNotExistException
        del self.wishlist[product_id]
        self.save()

    def clear(self) -> None:
        """
        Clears the wishlist
        """
        self.wishlist = {}
        self.save()

    def get_session_id(self):
        return self.session.session_key
