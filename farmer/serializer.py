from rest_framework import serializers
from .models import Farmer, StockDetail, StockMaster, Listing
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
    farmer_name = serializers.CharField(read_only=True, source="first_name")
    total_price = serializers.DecimalField(
        read_only=True, max_digits=20, decimal_places=2
    )

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
            "total_price",
        )


class StockDetailSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(
        read_only=True, max_digits=20, decimal_places=2
    )

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
            "farmer_id",
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
    farmer_name = serializers.CharField(read_only=True, source="first_name")

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
    items = StockDetailSerializer(many=True, read_only=True)
    crop_name = serializers.CharField(read_only=True)
    farmer_name = serializers.CharField(read_only=True, source="first_name")

    class Meta(MetaAbstract):
        model = StockMaster
        fields = MetaAbstract.fields + (
            "stock_id",
            "items",
            "crop_name",
            "farmer_name",
        )


class ListingRetrieveSerializer(serializers.ModelSerializer):
    stock_detail = StockDetailTableSerializer(read_only=True)
    crop_name = serializers.CharField(read_only=True)
    farmer_name = serializers.CharField(read_only=True, source="first_name")
    class Meta(MetaAbstract):
        model = Listing
        fields = MetaAbstract.fields + (
            "l_id",
            "stock_detail",
            "qty_available",
            "price_per_unit",
            "status",
            "crop_name",
            "farmer_name",
        )


class ListingSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(read_only=True)
    farmer_name = serializers.CharField(read_only=True, source="first_name")

    class Meta(MetaAbstract):
        model = Listing
        fields = MetaAbstract.fields + (
            "l_id",
            "qty_available",
            "price_per_unit",
            "status",
            "crop_name",
            "farmer_name",
            "stock_detail",
        )

    def validate_qty_available(self, data):

        req = self.get_initial()
        original = self.instance
        stockdetail_id = req.get(
            "stock_detail",
            getattr(
                (
                    original.stock_detail
                    if hasattr(original, "stock_detail")
                    else object
                ),
                "id",
                None,
            ),
        )

        # print(stockdetail_id)
        primary = getattr(original, "l_id", False)
        original_stock = StockDetail.objects.filter(pk=stockdetail_id).values(
            "quantity"
        )[0]["quantity"]
        if original_stock < data:
            raise serializers.ValidationError(
                "Available Quantity Should not exceed Original Quantity"
            )
        else:
            if primary:
                existing_listing = Listing.objects.filter(
                    ~Q(l_id=primary), stock_detail=stockdetail_id
                ).values("qty_available")
            else:
                existing_listing = Listing.objects.filter(
                    stock_detail=stockdetail_id
                ).values("qty_available")
            avl_qty = original_stock - data
            for listing in existing_listing:
                avl_qty -= listing["qty_available"]
                if avl_qty < 0:
                    raise serializers.ValidationError(
                        "Unable to save listing: the total quantity from existing listings plus the entered quantity exceeds the original quantity."
                    )

        return data
