from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, AllowAny

from contact_us.models import Contact
from contact_us.serializers import ContactUsSerializer
from utils.pagination import Pagination


@extend_schema(tags=["contact-us"])
class ContactUsViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    pagination_class = Pagination
    serializer_class = ContactUsSerializer
    http_method_names = ['get', 'post']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAdminUser()]
        return [AllowAny()]

    @extend_schema(
        summary="Retrieve a list of contact us messages",
        description="This endpoint returns a list of all contact us messages.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve contact us message by ID",
        description="This endpoint returns details of a specific contact us message identified by its ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new contact us message",
        description="This endpoint creates a new contact us message.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)