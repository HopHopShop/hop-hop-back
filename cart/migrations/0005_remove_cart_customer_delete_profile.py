# Generated by Django 4.2.13 on 2024-06-26 12:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cart", "0004_cart_customer"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cart",
            name="customer",
        ),
        migrations.DeleteModel(
            name="Profile",
        ),
    ]
