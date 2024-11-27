from django.db.models import Min, Max
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from shop.filters import ProductFilter, CategoryFilter
from shop.models import Category, Product, ProductImage
from shop.serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductDetailSerializer,
    CategoryImageSerializer,
    ProductCreateUpdateSerializer,
    ProductImageUploadSerializer, ChangeImageOrderingSerializer,
)
from utils.pagination import Pagination
from utils.permissions import IsAdminUserOrReadOnly


@extend_schema(
    tags=["categories"],
    summary="Retrieve a list of categories",
    description="This endpoint returns a "
    "list of all categories. "
    "Doesn't support pagination.",
)
class ListCategories(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


@extend_schema(tags=["categories"])
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["id"]
    filterset_class = CategoryFilter
    permission_classes = (IsAdminUserOrReadOnly,)

    def get_serializer_class(self):
        if self.action == "upload_image":
            return CategoryImageSerializer
        return CategorySerializer

    @extend_schema(
        summary="Retrieve a list of categories",
        description="This endpoint returns a list of all categories. Supports pagination if configured.",
        parameters=[
            OpenApiParameter(
                name="name",
                description="Search by category name.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Ordering by ID (id - for ascending order, -id for descending)",
                required=False,
                type=str,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new category",
        description="This endpoint allows you to create a new category. You need to provide the required fields.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a specific category",
        description="This endpoint returns the details of a specific category identified by its ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update an existing category",
        description="This endpoint allows you to update an existing category identified by its ID. You only need to provide the fields you want to update.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a category",
        description="This endpoint allows you to delete a category identified by its ID.",
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Category deleted successfully."}, status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Upload image for category",
        description="Endpoint for uploading image for category",
    )
    @action(
        methods=["POST", "PATCH"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        categories = self.get_object()
        serializer = self.get_serializer(categories, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["products"])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    permission_classes = (IsAdminUserOrReadOnly,)
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProductFilter
    ordering_fields = ["views", "price", "id"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        elif self.action == "create":
            return ProductCreateUpdateSerializer
        elif self.action == "partial_update":
            return ProductCreateUpdateSerializer
        elif self.action == "upload_images":
            return ProductImageUploadSerializer
        elif self.action == "change_ordering":
            return ChangeImageOrderingSerializer
        return ProductSerializer

    @extend_schema(
        summary="Retrieve a list of products",
        description="This endpoint returns a list of products. You can filter by category slug and product name, "
                    "and sort by fields such as 'views', 'price', 'id'.",
        parameters=[
            OpenApiParameter(
                name="category",
                description="Specify the category id to filter the products.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="name",
                description="Search by product name.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="price_min",
                description="Filter products within a price range. Select the start of the range.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="price_max",
                description="Filter products within a price range. Select the end of the range.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Sort by fields: 'views' (popular product), 'price', 'id'. Use '-' for descending order.",
                required=False,
                type=str,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        price_range = self.get_queryset().aggregate(min_price=Min('price'), max_price=Max('price'))

        response.data['min_price'] = price_range['min_price']
        response.data['max_price'] = price_range['max_price']

        return response

    @extend_schema(
        summary="Create a new product",
        description="This endpoint allows you to create a new product. You need to provide the required fields.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a specific product",
        description="This endpoint returns the details of a specific product identified by its ID. It also increments the view count of the product.",
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Update an existing product",
        description="This endpoint allows you to update an existing product identified by its ID. You only need to provide the fields you want to update.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a product",
        description="This endpoint allows you to delete a product identified by its ID.",
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Product deleted successfully."}, status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Retrieve popular products",
        description="This endpoint returns the top 30 most viewed products.",
    )
    @action(detail=False, methods=["get"])
    def popular(self, request):
        popular_products = self.queryset.order_by("-views")[:30]
        serializer = self.get_serializer(popular_products, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Retrieve latest arrival products",
        description="This endpoint returns the latest 30 products based on their creation date.",
    )
    @action(detail=False, methods=["get"])
    def latest_arrival(self, request):
        latest_arrival_products = self.queryset.order_by("-pk")[:30]
        serializer = self.get_serializer(latest_arrival_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["POST", "PATCH"],
        detail=True,
        url_path="upload-images",
        permission_classes=[IsAdminUser],
    )
    def upload_images(self, request, pk=None):
        product = self.get_object()

        serializer = ProductImageUploadSerializer(
            instance=product, data=request.data, context={"product": product}
        )

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "images uploaded"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete a product image",
        description="This endpoint allows you to delete a specific image of a product identified by its image ID.",
    )
    @action(
        detail=True, methods=["delete"], url_path="delete-image/(?P<image_id>[^/.]+)"
    )
    def delete_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        try:
            image = product.product_images.get(id=image_id)
            image.delete()
            return Response(
                {"detail": "Image deleted successfully."}, status=status.HTTP_200_OK
            )
        except ProductImage.DoesNotExist:
            return Response(
                {"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="Change the order of product images",
        description="This endpoint allows changing the order of a product's images by passing an ordered list of image IDs."
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="change-ordering",
        permission_classes=[IsAdminUser],
    )
    def change_ordering(self, request, pk=None):
        product = self.get_object()
        serializer = ChangeImageOrderingSerializer(data=request.data, context=product)

        serializer.is_valid(raise_exception=True)

        image_ids = serializer.validated_data.get("image_ids")

        for order, image_id in enumerate(image_ids):
            ProductImage.objects.filter(id=image_id, product=product).update(order=order)

        return Response({"detail": "Image ordering updated successfully"}, status=status.HTTP_200_OK)



    @extend_schema(
        summary="Update a product image",
        description="This endpoint allows you to update a specific image of a product identified by its image ID.",
    )
    @action(
        detail=True, methods=["patch"], url_path="update-image/(?P<image_id>[^/.]+)"
    )
    def update_image(self, request, pk=None, image_id=None):
        product = self.get_object()
        try:
            image = product.product_images.get(id=image_id)
        except ProductImage.DoesNotExist:
            return Response(
                {"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductImageUploadSerializer(
            image, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Image updated successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
