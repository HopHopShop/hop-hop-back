# Generated by Django 5.0.6 on 2024-09-11 13:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cart", "0003_alter_coupon_discount"),
        ("checkout", "0002_alter_order_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="coupon",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cart.coupon",
            ),
        ),
    ]
