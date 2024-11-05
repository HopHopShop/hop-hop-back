import os
import uuid

from django.db import models
from pytils.translit import slugify


def product_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.product.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/products/", filename)


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to="uploads/category/",
        max_length=255,
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    class Meta:
        app_label = "shop"
        ordering = ["-id"]


class Product(models.Model):
    name = models.CharField(max_length=100, db_index=True, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    slug = models.SlugField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    SKU = models.CharField(max_length=100)
    description = models.TextField()
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.SKU:
            self.SKU = slugify(self.name)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        app_label = "shop"
        ordering = ["-id"]


class ProductImage(models.Model):
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=product_image_file_path,
        max_length=255,
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="product_images"
    )
    order = models.PositiveIntegerField()
    frontend_id = models.CharField(max_length=255)

    def __str__(self):
        return f"Image for {self.product.name}"

    class Meta:
        ordering = ["order", "id"]
        app_label = "shop"


class ProductAttributes(models.Model):
    brand = models.CharField(max_length=100)
    material = models.CharField(max_length=100)
    style = models.CharField(max_length=100)
    size = models.IntegerField()
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="product_attributes"
    )

    def __str__(self):
        return f"Attributes for {self.product.name}"

    class Meta:
        app_label = "shop"
