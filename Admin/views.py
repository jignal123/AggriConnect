from rest_framework import generics, status, mixins, viewsets
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import Admin
from farmer.models import CropMaster
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from .serializer import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.pagination import LimitOffsetPagination

# Create your views here.
class MyCustomViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    This is The common Viewset which will allow specific requests
    in the viewsets. This is only for Model Viewsets
    """
    myfields = (
        "deleted",
        "created_at",
        "updated_at"
    )

class PasswordResetRequest(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            if Admin.objects.filter(email=email).exists():
                admin = Admin.objects.get(email=email)
                uidb64 = urlsafe_base64_encode(force_bytes(admin.pk))
                token = PasswordResetTokenGenerator().make_token(admin)

                reset_link = f"http://localhost/{uidb64}/{token}"
                # print(reset_link)
                send_mail(
                    "Password Change Request",
                    f"Click the link to reset your password: {reset_link}",
                    "202500819010083@glsu.edu.in",
                    [email],
                    fail_silently=False,
                )

            return Response(
                {"Message": "If this email Exists, the reset link has been sent"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirm(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_id = urlsafe_base64_decode(
                serializer.validated_data["uidb64"]
            ).decode()
            admin = Admin.objects.get(pk=user_id)
            admin.set_password(serializer.validated_data["password"])
            admin.save()

            return Response(
                {"message": "Password Changed Successfully!"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        access = request.auth
        refresh = RefreshToken(request.data["refresh"])
        self.blacklist_token(access)
        self.blacklist_token(refresh)
        return JsonResponse({"details": "Logged out Successfully!"})

    def blacklist_token(self, token):
        jti = token.get("jti")
        exp = token.get("exp")
        now = token.current_time.timestamp()
        storetill = int(exp - now)
        cache.set(f"blacklist({jti})", "true", timeout=storetill)


class RedisTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = RefreshToken(request.data["refresh"])
        jti = refresh["jti"]

        if cache.get(f"blacklist({jti})", None):
            raise InvalidToken({"detail": "Refresh Token is Invalid or expired!"})
        return super().post(request, *args, **kwargs)


class CropViewSet(MyCustomViewSet):
    myfields = MyCustomViewSet.myfields + (
        "crop_id",
        "crop_name",
        "crop_variety",
        "photo",
        "description",
    )
    queryset = CropMaster.objects.only(*myfields)
    serializer_class = CropMasterSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend,OrderingFilter,SearchFilter]
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()