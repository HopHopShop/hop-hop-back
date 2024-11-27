import jwt

from django.contrib.auth import authenticate, get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import generics, viewsets, response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.models import Customer
from authentication.serializers import (
    CustomerSerializer,
    LoginSerializer, CustomerAdminSerializer,
    ResetPasswordSerializer, ResetPasswordRequestSerializer, RegistrationSerializer, EmailVerificationSerializer,
)
from authentication.utils import send_email_verification_url
from checkout.models import Order
from checkout.serializers import OrderListSerializer
from checkout.serializers import OrderSerializer
from utils.custom_exceptions import InvalidCredentialsError, AccountIsNotVerifyError
from utils.pagination import Pagination
from django.conf import settings


@extend_schema(tags=["authentication"], summary="Registering a new user")
class CreateCustomerView(generics.CreateAPIView):
    """
    API view to register a new user.

    This view handles the creation of a new user account. Upon successful registration,
    it issues JWT tokens (access and refresh) and sets the refresh token in an HTTP-only cookie.

    """

    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs) -> Response:
        """
        Handle the creation of a new user and issue JWT tokens.

         Args:
            request: The HTTP request object containing user registration data.

        Returns:
            Response: The HTTP response object containing user data and JWT tokens.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user is not None:
            refresh = RefreshToken.for_user(user)
            response = Response(status=status.HTTP_201_CREATED)

            token = RefreshToken.for_user(user).access_token

            send_email_verification_url(user, token)

            response.data = {
                "user": CustomerSerializer(user).data,
                "access_token": {
                    "value": str(refresh.access_token),
                    "expires": settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(),
                },
                "refresh_token": {
                    "value": str(refresh),
                    "expires": settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
                },
            }

            return response


@extend_schema(tags=["authentication"])
class VerifyEmail(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='token',
                type=str,
                location=OpenApiParameter.QUERY,
                description='JWT token for email verification'
            )
        ],
        responses={
            200: OpenApiResponse(description="Email successfully verified."),
            400: OpenApiResponse(description="Invalid or expired token."),
        },
    )
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user = get_user_model().objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return response.Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return response.Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.DecodeError:
            return response.Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["authentication"], summary="Log in to an existing account")
class LoginView(APIView):
    """
    API view to log in an existing user.

    This view handles user authentication and issues JWT tokens upon successful login.
    The refresh token is set in an HTTP-only cookie.

    Methods:
        post: Handles POST requests to log in a user.
    """

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs) -> Response:
        """
        Handle user login and issue JWT tokens.

        Args:
            request: The HTTP request object containing login credentials.

        Returns:
            Response: The HTTP response object containing user data and access token.

        Raises:
            InvalidCredentialsError: If the login credentials are invalid.
        """
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            response = Response()

            response.data = {
                "user": CustomerSerializer(user).data,
                "access_token": {
                    "value": str(refresh.access_token),
                    "expires": settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(),
                },
                "refresh_token": {
                    "value": str(refresh),
                    "expires": settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
                },
            }
            return response
        raise InvalidCredentialsError


@extend_schema(tags=["authentication"])
class CustomTokenRefreshView(TokenRefreshView):
    """
    API view to refresh JWT tokens using refresh token from body
    """

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=["customer data"], summary="Get all customers")
class CustomersListView(viewsets.ModelViewSet):
    """
    API viewset to list all customers, retrieve one customer and update their personal information/roles/set them as inactive.
    """

    serializer_class = CustomerAdminSerializer
    queryset = Customer.objects.all()
    pagination_class = Pagination
    permission_classes = (IsAdminUser,)
    filter_backends = [SearchFilter, OrderingFilter]
    ordering_fields = ['id']
    search_fields = ['first_name', 'email']
    http_method_names = ["get", "patch"]

    @extend_schema(
        summary="Retrieve a list of customers",
        description="This endpoint returns a list of all customers.",
        parameters=[
            OpenApiParameter(
                name="search",
                description="Search by name and/or surname",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Ordering by ID (id - for ascending order, -id for descending)",
                required=False,
                type=str,
            )
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a specific customer",
        description="This endpoint returns the details of a specific customer identified by its ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update an existing customer",
        description="This endpoint allows you to update an existing customer identified by its ID. You only need to "
                    "provide the fields you want to update.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


@extend_schema(tags=["customer data"], summary="Get information about your profile")
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve and update the authenticated user's profile.
    """

    serializer_class = CustomerSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(tags=["authentication"])
class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        reset_password_serializer = self.serializer_class(data=request.data)
        if reset_password_serializer.is_valid(raise_exception=True):
            reset_password_serializer.save()

            return Response("Password was successfully changed", status=status.HTTP_200_OK)


@extend_schema(tags=["authentication"])
class PasswordResetRequestView(APIView):
    serializer_class = ResetPasswordRequestSerializer

    def post(self, request, *args, **kwargs):
        password_reset_request_serializer = self.serializer_class(data=request.data)

        if password_reset_request_serializer.is_valid(raise_exception=True):
            password_reset_request_serializer.save()

            return Response("Recovery email was successfully sent", status=status.HTTP_200_OK)


@extend_schema(tags=["customer data"])
class ProfileOrder(viewsets.ReadOnlyModelViewSet):
    """
    API view for retrieving orders that belong to the authenticated user
    """
    permission_classes = (IsAuthenticated,)
    pagination_class = Pagination
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).select_related("customer")
