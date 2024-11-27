from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from cart.models import Coupon, CartItem, Cart
from shop.models import Product
from shop.serializers import ProductSerializer


class CartService:
    """
    General service to handle cart operations depending on user authentication status.
    """

    def __init__(self, request):
        self.request = request
        if self.request.user.is_authenticated:
            self.service = CartDBService(self.request.user)
        else:
            self.service = CartSessionService(self.request)

    def add(
            self, product: Product, quantity: int = 1, update_quantity: bool = False
    ) -> None:
        self.service.add(product, quantity, update_quantity)

    def subtract_quantity(self, product: Product) -> None:
        self.service.subtract_quantity(product)

    def remove(self, product: Product) -> None:
        self.service.remove(product)

    def clear(self) -> None:
        self.service.clear()

    def add_coupon(self, coupon: Coupon) -> None:
        self.service.add_coupon(coupon)

    def get_coupon(self) -> Optional[Coupon]:
        self.handle_empty_cart()
        return self.service.get_coupon()

    def remove_coupon(self) -> None:
        self.service.remove_coupon()

    def coupon_is_used(self) -> bool:
        return self.service.coupon_is_used()

    def get_total_price(self) -> Decimal:
        return self.service.get_total_price()

    def get_total_item(self) -> int:
        return self.service.get_total_item()

    def get_session_id(self) -> int:
        return self.request.session.session_key

    def handle_empty_cart(self) -> None:
        if self.service.get_total_item() == 0:
            self.service.remove_coupon()

    def __iter__(self):
        return iter(self.service)


class CartSessionService:
    """
    Service for managing cart operations within a session.

    Attributes:
        session: The session from the request.
        cart: A dictionary representing the cart in the session.
        coupon_id: The ID of the applied coupon, if any.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.coupon_id = self.session.get("coupon_id")

    def add(
            self, product: Product, quantity: int = 1, update_quantity: bool = False
    ) -> None:
        """
        Add a product to the cart or update its quantity
        """
        product_id = str(product.id)
        # If the product is not already in the cart, add it with initial quantity and price
        if product_id not in self.cart:
            self.cart[product_id] = {"quantity": 0, "price": str(product.price)}
        # Update the quantity of the product
        if update_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity
        self.save()

    def subtract_quantity(self, product: Product) -> None:
        """
        Subtract a product from the cart or update its quantity
        """
        product_id = str(product.id)
        if product_id in self.cart:
            if self.cart[product_id]["quantity"] == 1:
                del self.cart[product_id]
            else:
                self.cart[product_id]["quantity"] -= 1
        self.save()

    def save(self) -> None:
        """
        Save the cart to the session.
        """
        self.session.modified = True

    # Remove a product from the cart
    def remove(self, product: Product) -> None:
        """
        Remove a product from the cart
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Loop through cart items and fetch the products from the database
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        for product in products:
            cart[str(product.id)]["product"] = ProductSerializer(product).data
        for item in cart.values():
            item["price"] = float(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            cart_item = {
                "product": item["product"],
                "quantity": item["quantity"],
                "total_price": item["total_price"],
                "price": item["price"],
            }
            yield cart_item

    def __len__(self) -> int:
        return sum(item["quantity"] for item in self.cart.values())

    # Get the total number of items in the cart
    def get_total_item(self) -> int:
        return sum(item["quantity"] for item in self.cart.values())

    # Clear the cart by deleting it from the session
    def clear(self) -> None:
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def add_coupon(self, coupon: Coupon) -> None:
        """
        Add a coupon to the cart
        """
        if not self.cart.values():
            raise ValidationError("You cannot use coupon on empty cart")

        self.coupon_id = coupon.id
        self.session["coupon_id"] = coupon.id
        self.save()

    def get_coupon(self) -> Optional[Coupon]:
        """
        Get a coupon by ID
        """
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                pass

    def remove_coupon(self) -> None:
        """
        Remove a coupon from the cart
        """
        self.coupon_id = None
        self.session["coupon_id"] = {}
        self.save()

    def coupon_is_used(self) -> bool:
        """
        Check if a coupon has been used
        """
        return bool(self.session.get("coupon_id"))

    # Get the total price of all items in the cart
    def get_total_price(self) -> Decimal | int:
        total = sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )
        coupon = self.get_coupon()
        if coupon:
            total -= (coupon.discount / Decimal(100)) * total
        return total


class CartDBService:
    """
    Service for managing cart operations using database storage.

    Attributes:
        user: The user associated with the cart.
        cart: The Cart object associated with the user.
        coupon_id: The ID of the applied coupon, if any.
    """

    def __init__(self, user: get_user_model()):
        self.user = user
        self.cart, created = Cart.objects.get_or_create(user=user)
        self.coupon_id = self.cart.coupon_id

    def __iter__(self):
        """
        Iterate through cart items associated with the user's cart in the database.
        """
        cart_items = CartItem.objects.filter(cart=self.cart).select_related("product")
        for item in cart_items:
            yield {
                "product": ProductSerializer(item.product).data,
                "quantity": item.quantity,
                "total_price": item.quantity * item.product.price,
                "price": item.product.price,
            }

    def add(
            self, product: Product, quantity: int = 1, update_quantity: bool = False
    ) -> None:
        """
        Add a product to the user's cart in the database or update its quantity.
        """
        cart_item, created = CartItem.objects.get_or_create(
            cart=self.cart, product=product
        )
        cart_item.quantity = (
            quantity if update_quantity else cart_item.quantity + quantity
        )
        cart_item.save()

    def subtract_quantity(self, product: Product) -> None:
        """
        Subtract a product from the user's cart in the database or update its quantity.
        """
        try:
            cart_item = CartItem.objects.get(cart=self.cart, product=product)
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
            else:
                cart_item.save()
        except CartItem.DoesNotExist:
            pass

    def remove(self, product):
        """
        Remove a product from the user's cart in the database.
        """
        CartItem.objects.filter(cart=self.cart, product=product).delete()

    def clear(self):
        """
        Clear the user's cart in the database.
        """
        CartItem.objects.filter(cart=self.cart).delete()

    def get_total_price(self):
        return self.cart.get_total_price()

    def get_total_item(self):
        return self.cart.get_total_item()

    def get_coupon(self):
        if self.coupon_id:
            try:
                return Coupon.objects.get(id=self.coupon_id)
            except Coupon.DoesNotExist:
                return None
        return None

    def add_coupon(self, coupon: Coupon):
        """
        Apply a coupon to the user's cart in the database.
        """

        if not self.cart.get_total_item():
            raise ValidationError("You cannot use coupon on empty cart")

        self.coupon_id = coupon.id
        self.cart.coupon = coupon
        self.cart.save()

    def remove_coupon(self):
        """
        Remove the applied coupon from the user's cart in the database.
        """

        self.coupon_id = None
        self.cart.coupon = None
        self.cart.save()

    def coupon_is_used(self):
        """
        Check if a coupon is applied to the user's cart in the database.
        """
        return self.cart.coupon_is_used()
