from rest_framework import serializers
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from .models import Admin

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ("email")

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True,min_length=8)
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        try:
            uid = urlsafe_base64_decode(data["uidb64"]).decode()
            admin = Admin.objects.get(pk=uid)
        except (ValueError,OverflowError,TypeError,Admin.DoesNotExist):
            raise serializers.ValidationError({"uidb64":"Invalid UID"})
        
        if not PasswordResetTokenGenerator().check_token(admin,data["token"]):
            raise serializers.ValidationError({"token":"Token is Invalid or Expired"})
        return data