from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.management import call_command


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"

    def ready(self):
        post_migrate.connect(load_fixtures, sender=self)


def load_fixtures(sender, **kwargs):
    call_command("loaddata", "initial_data.json")
