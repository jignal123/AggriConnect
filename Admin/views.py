from rest_framework import generics,status
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import Admin
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from .serializer import PasswordResetRequestSerializer,PasswordResetConfirmSerializer
# Create your views here.

class PasswordResetRequest(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self,request):
        serializer = self.serializer_class(data = request.data)
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
                    fail_silently=False
                )

            return Response({"Message":"If this email Exists, the reset link has been sent"},status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirm(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_id = urlsafe_base64_decode(serializer.validated_data["uidb64"]).decode()
            admin = Admin.objects.get(pk=user_id)
            admin.set_password(serializer.validated_data["password"])
            admin.save()

            return Response({"message":"Password Changed Successfully!"},status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)