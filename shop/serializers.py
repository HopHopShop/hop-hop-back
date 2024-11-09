from rest_framework import serializers
from shop.models import Category, Product, ProductAttributes, ProductImage
from utils.repeatable_functions import convert_price


class CategoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("image",)

    def update(self, instance, validated_data):
        image = validated_data.get("image", None)
        if image is not None:
            instance.image = image
            instance.save()
        return instance


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = (
            "id",
            "frontend_id",
            "image",
            "order"
        )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "image",
        ]


class ProductAttributesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttributes
        fields = ["brand", "material", "style", "size"]


class ProductImageUploadSerializer(serializers.Serializer):
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(
            max_length=1000000, allow_empty_file=False, use_url=False
        ),
        write_only=True,
    )
    frontend_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        help_text="An ordered list of image frontend IDs to reorder"
    )

    def validate(self, attrs):
        frontend_ids = attrs.get("frontend_ids")[0].split(',')
        if len(frontend_ids) != len(attrs["uploaded_images"]):
            raise serializers.ValidationError("Ordering IDs list do not match uploaded images list.")

        return attrs

    def create(self, validated_data):
        images_list = validated_data["uploaded_images"]
        frontend_ids = validated_data["frontend_ids"][0].split(',')

        product = self.context["product"]
        product_images = ProductImage.objects.filter(product=product)

        if not product_images:
            product_images = []
            for i, image, fr_id in zip(range(len(images_list)), images_list, frontend_ids):
                product_image = ProductImage(product=product, image=image, order=i, frontend_id=fr_id)
                product_images.append(product_image)
        else:
            last_order_value = list(product_images)[-1].order
            product_images = []
            for i, image, fr_id in zip(range(len(images_list)), images_list, frontend_ids):
                product_image = ProductImage(product=product, image=image, order=i+last_order_value+1, frontend_id=fr_id)
                product_images.append(product_image)

        ProductImage.objects.bulk_create(product_images)
        return product_images


class ChangeImageOrderingSerializer(serializers.Serializer):
    frontend_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        help_text="An ordered list of image frontend IDs to reorder"
    )

    def validate_frontend_ids(self, value):
        product = self.context
        product_ordering_ids = product.product_images.values_list("frontend_id", flat=True)

        if set(value) != set(product_ordering_ids):
            raise serializers.ValidationError("Invalid image ordering IDs provided.")

        return value


class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "slug",
            "price",
            "SKU",
            "images",
        ]
        read_only_fields = ["slug"]

    def get_price(self, obj):
        return convert_price(obj.price)

    def get_images(self, obj):
        first_image = obj.product_images.first()
        return ProductImageSerializer(first_image).data if first_image else None


class ProductDetailSerializer(serializers.ModelSerializer):
    attributes = ProductAttributesSerializer(
        source="product_attributes", required=False
    )
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True, source="product_images")
    slug = serializers.CharField(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "SKU",
            "description",
            "category",
            "attributes",
            "images",
        ]

    def get_price(self, obj):
        return convert_price(obj.price)


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    attributes = ProductAttributesSerializer(
        source="product_attributes", required=False
    )
    slug = serializers.CharField(read_only=True)
    SKU = serializers.CharField(required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "SKU",
            "description",
            "category",
            "attributes",
        ]

    def create(self, validated_data):
        product_attributes_data = validated_data.pop("product_attributes", None)
        product = Product.objects.create(**validated_data)
        if product_attributes_data:
            product_attributes_data["product"] = product
            ProductAttributes.objects.create(**product_attributes_data)

        return product

    def update(self, instance, validated_data):
        product_attributes_data = validated_data.pop("product_attributes", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if product_attributes_data:
            ProductAttributes.objects.update_or_create(
                product=instance, defaults=product_attributes_data
            )

        return instance

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
