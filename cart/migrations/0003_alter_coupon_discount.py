# Generated by Django 5.0.6 on 2024-07-06 11:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cart", "0002_coupon_remove_cart_old_cart_cart_coupon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coupon",
            name="discount",
            field=models.IntegerField(
                help_text="Percentage value (1 to 100)",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
    ]
