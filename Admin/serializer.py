from rest_framework import serializers
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from .models import Admin
from farmer.models import CropMaster
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import json

class MetaAbstract:
    fields = (
        "deleted",
        "created_at",
        "updated_at",
    )
    read_only_fields = (
        "created_at",
        "updated_at",
    )

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls,user):
        token = super().get_token(user)
        token["email"] = user.email
        token["address"] = user.address
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["a_photo"] = str(user.a_photo)

        return token


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = "email"


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        try:
            uid = urlsafe_base64_decode(data["uidb64"]).decode()
            admin = Admin.objects.get(pk=uid)
        except (ValueError, OverflowError, TypeError, Admin.DoesNotExist):
            raise serializers.ValidationError({"uidb64": "Invalid UID"})

        if not PasswordResetTokenGenerator().check_token(admin, data["token"]):
            raise serializers.ValidationError({"token": "Token is Invalid or Expired"})
        return data


class CropMasterSerializer(serializers.ModelSerializer):
    class Meta(MetaAbstract):
        model = CropMaster
        fields = MetaAbstract.fields + (
            "crop_id",
            "crop_name",
            "crop_variety",
            "photo",
            "description",
        )

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)
    class Meta:
        fields = (
            "refresh"
        )


class DailyBreakdownSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()


class RegistrationBreakdownSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    daily_breakdown = DailyBreakdownSerializer(many=True)


class DashboardSerializer(serializers.Serializer):
    farmers = serializers.DictField(child=serializers.IntegerField())
    wholesalers = serializers.DictField(child=serializers.IntegerField())
    stock = serializers.DictField()
    biddings = serializers.DictField(child=serializers.IntegerField())
    orders = serializers.DictField(child=serializers.IntegerField())
    registrations = serializers.DictField()