from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from contact_us.models import Contact
from contact_us.serializers import ContactUsSerializer, SendMessageSerializer
from utils.mail_sender import EmailUtil
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


@extend_schema(tags=["contact-us"])
class SendQuickAnswer(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = SendMessageSerializer

    @extend_schema(
        request=SendMessageSerializer,
        responses={200: SendMessageSerializer},
        description="Send a quick answer to the user's email address."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid(raise_exception=True):
            user_email = serializer.validated_data['email']
            email_body = serializer.validated_data['message']

            data = {
                'email_body': email_body,
                'to_email': user_email,
                'email_subject': 'Message from Hop Hop Shop administration'
            }

            EmailUtil.send_email(data=data)

            return Response({"details": "Message was successfully sent to the provided email!"},
                            status=status.HTTP_200_OK)
