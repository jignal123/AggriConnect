from rest_framework import serializers
from .models import Farmer
from django.contrib.auth.hashers import make_password

class FarmerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = Farmer
        fields = (
            "f_id",
            "user_name",
            "password",
            "first_name",
            "last_name",
            "gender",
            "sub_district",
            "state",
            "address",
            "ekyf_id",
            "f_phone",
            "f_photo",
            "aadhar_no",
            "deleted",
        )

    def create(self, validated_data):
        print(validated_data)
        password = validated_data.pop("password")
        password = make_password(password)
        validated_data["password"] = password
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop("password",None)
        if password:
            password = make_password(password)
            instance.password = password
            validated_data["password"] = password
        
        return super().update(instance, validated_data)