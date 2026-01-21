from rest_framework import serializers
from .models import Farmer, StockDetail, StockMaster
from django.contrib.auth.hashers import make_password
from django.db import transaction

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


class FarmerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta(MetaAbstract):
        model = Farmer
        fields = MetaAbstract.fields + (
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
        )

    def create(self, validated_data):
        print(validated_data)
        password = validated_data.pop("password")
        password = make_password(password)
        validated_data["password"] = password

        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            password = make_password(password)
            instance.password = password
            validated_data["password"] = password

        return super().update(instance, validated_data)


class StockDetailTableSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(read_only=True)
    farmer_name = serializers.CharField(read_only=True,source="first_name")
    class Meta(MetaAbstract):
        model = StockDetail
        fields = MetaAbstract.fields + (
            "id",
            "stock_id",
            "harvested_date",
            "hectares",
            "quantity",
            "unit",
            "price_per_unit",
            "expiry_date",
            "stored_location",
            "crop_name",
            "farmer_name",
        )

class StockDetailSerializer(serializers.ModelSerializer):
        class Meta:
            model = StockDetail
            fields = (
                "harvested_date",
                "hectares",
                "quantity",
                "unit",
                "price_per_unit",
                "expiry_date",
                "stored_location",
            )
class StockMasterCreateSerializer(serializers.ModelSerializer):
    """
    StockMasterCreateSerializer is for Only Creating a Stock Because
    Insertion of Stock Should Be with Stock Items
    """
    items = StockDetailSerializer(many=True)
    class Meta:
        model = StockMaster
        fields = (
            "stock_id",
            "crop_id",
            "farmer_id",
            "items",
        )
    def create(self, validated_data):
        with transaction.atomic():
            stockDetail = validated_data.pop("items")
            stock_id = StockMaster.objects.create(**validated_data)

            for item in stockDetail:
                StockDetail.objects.create(stock_id = stock_id, **item)

            return stock_id

class StockMasterSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(read_only=True)
    farmer_name = serializers.CharField(read_only=True,source="first_name")
    class Meta(MetaAbstract):
        model = StockMaster
        fields = MetaAbstract.fields + (
            "stock_id",
            "crop_name",
            "farmer_name",
            "crop_id",
            "farmer_id",
        )

class StockMasterRetrieveSerializer(serializers.ModelSerializer):
    items = StockDetailSerializer(many=True,read_only=True)
    crop_name = serializers.CharField(read_only=True)
    farmer_name = serializers.CharField(read_only=True,source="first_name")
    class Meta(MetaAbstract):
        model = StockMaster
        fields = MetaAbstract.fields + (
            "stock_id",
            "items",
            "crop_name",
            "farmer_name",
        )