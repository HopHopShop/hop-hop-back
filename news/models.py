import os
import uuid

from django.db import models
from pytils.translit import slugify


def news_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"news-{instance.id}-{uuid.uuid4()}{extension}"
    return os.path.join("uploads/news_images/", filename)


class NewsType(models.TextChoices):
    HOTTEST = "hottest", "The Hottest"
    HIPHOP = "choice", "HopHop choice"
    LOVE = "love", "One Love"
    SECRET = "secret", "Customer Secret"
    DEFAULT = "default", "Default"


class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to=news_image_file_path, blank=True, null=True)
    type = models.CharField(
        max_length=20, choices=NewsType.choices, default=NewsType.DEFAULT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.type != NewsType.DEFAULT:
            existing_news = News.objects.filter(type=self.type).exclude(id=self.id).exists()
            if existing_news:
                raise ValidationError(f"A news item with type '{self.type}' already exists.")

    def save(self, *args, **kwargs):
        if self.type != NewsType.DEFAULT:
            previous_news = News.objects.filter(type=self.type).exclude(pk=self.pk)
            if previous_news.exists():
                previous_news.update(type=NewsType.DEFAULT)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
