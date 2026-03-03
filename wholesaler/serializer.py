from rest_framework import serializers
from .models import Wholesaler, StockDetail, StockMaster
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q

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

class WholesalerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta(MetaAbstract):
        model = Wholesaler
        fields = MetaAbstract.fields + (
        "w_id",
        "email",
        "password",
        "first_name",
        "last_name",
        "gender",
        "city",
        "state",
        "address",
        "w_phone",
        "w_photo",
        "aadhar_no",
        "gst_no",
        "business_proof",
        "business_name",
        "status",
        "pan_no"
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

class StockDetailTableSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(read_only=True)
    wholesaler_name = serializers.CharField(read_only=True, source="first_name")
    total_price = serializers.DecimalField(
        read_only=True, max_digits=20, decimal_places=2
    )

    class Meta(MetaAbstract):
        model = StockDetail
        fields = MetaAbstract.fields + (
            "id",
            "stock_id",
            "quantity",
            "crop_name",
            "price_per_unit",
            "intake_date",
            "expiry_date",
            "warehouse_loc",
            "wholesaler_name",
            "total_price",
        )
    
class StockDetailSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(
        read_only=True, max_digits=20, decimal_places=2
    )

    class Meta:
        model = StockDetail
        fields = (
            "quantity",
            "price_per_unit",
            "intake_date",
            "expiry_date",
            "warehouse_loc",
            "total_price",
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
            "w_id",
            "items",
        )

    def create(self, validated_data):
        with transaction.atomic():
            stockDetail = validated_data.pop("items")
            stock_id = StockMaster.objects.create(**validated_data)

            for item in stockDetail:
                StockDetail.objects.create(stock_id=stock_id, **item)

            return stock_id

class StockMasterSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(read_only=True)
    wholesaler_name = serializers.CharField(read_only=True, source="first_name")
    total_quantity = serializers.DecimalField(read_only=True, max_digits=10,decimal_places=2)

    class Meta(MetaAbstract):
        model = StockMaster
        fields = MetaAbstract.fields + (
            "stock_id",
            "crop_name",
            "wholesaler_name",
            "crop_id",
            "w_id",
            "total_quantity"
        )

class StockMasterRetrieveSerializer(serializers.ModelSerializer):
    items = StockDetailSerializer(many=True, read_only=True)
    crop_name = serializers.CharField(read_only=True)
    wholesaler_name = serializers.CharField(read_only=True, source="first_name")
    total_quantity = serializers.DecimalField(read_only=True, max_digits=10,decimal_places=2)

    class Meta(MetaAbstract):
        model = StockMaster
        fields = MetaAbstract.fields + (
            "stock_id",
            "items",
            "crop_name",
            "wholesaler_name",
            "total_quantity"
        )