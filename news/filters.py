import django_filters
from news.models import News, NewsType


class NewsFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.ChoiceFilter(choices=NewsType.choices)

    class Meta:
        model = News
        fields = ['title', 'type']
