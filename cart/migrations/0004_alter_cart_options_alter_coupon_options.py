# Generated by Django 5.0.6 on 2024-09-14 11:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cart", "0003_alter_coupon_discount"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="cart",
            options={"ordering": ["-id"]},
        ),
        migrations.AlterModelOptions(
            name="coupon",
            options={"ordering": ["-id"]},
        ),
    ]