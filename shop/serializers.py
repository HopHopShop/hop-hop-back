from rest_framework import serializers
from shop.models import Category, Product, ProductAttributes, ProductImage


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
            "image",
            "order"
        )


class ChangeImageOrderingSerializer(serializers.Serializer):
    image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="An ordered list of image IDs to reorder"
    )

    def validate_image_ids(self, value):
        # Ensure that all IDs are valid and belong to the product
        product = self.context
        product_image_ids = product.product_images.values_list("id", flat=True)

        print(product_image_ids)

        if set(value) != set(product_image_ids):
            raise serializers.ValidationError("Invalid image IDs provided.")

        return value


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

    def create(self, validated_data):
        images = validated_data["uploaded_images"]
        product = self.context["product"]
        product_images = [
            ProductImage(product=product, image=image) for image in images
        ]
        ProductImage.objects.bulk_create(product_images)
        return product_images

    def update(self, instance, validated_data):
        instance.product_images.all().delete()
        images = validated_data["uploaded_images"]
        product_images = [
            ProductImage(product=instance, image=image) for image in images
        ]
        ProductImage.objects.bulk_create(product_images)
        return product_images

    class Meta:
        model = ProductImage
        fields = [
            "image",
        ]


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
        if obj.price % 1 == 0:
            return str(int(obj.price))
        return str(obj.price)

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
        if obj.price % 1 == 0:
            return str(int(obj.price))
        return str(obj.price)


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
