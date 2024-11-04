import django_filters

from checkout.models import Order


class OrderFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(field_name="id", lookup_expr="icontains")

    class Meta:
        model = Order
        fields = ["id"]
