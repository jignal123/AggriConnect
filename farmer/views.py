from rest_framework import viewsets, mixins, status
from .models import Farmer, StockDetail, StockMaster, Listing
from .serializer import *
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import F, Subquery, Sum, OuterRef
from .filters import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from wholesaler.models import Bidding, Orders
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from Admin.extra_func import fetch_aadhaar


class CommonViewSet(
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

    myfields = ["deleted", "created_at", "updated_at"]


class FarmerViewSet(CommonViewSet):
    myfields = CommonViewSet.myfields + [
        "f_id",
        "user_name",
        "first_name",
        "last_name",
        "gender",
        "sub_district",
        "state",
        "address",
        "aadhar_photo",
        "farmer_id_photo",
        "ekyf_id",
        "f_phone",
        "f_photo",
        "aadhar_no",
    ]
    queryset = Farmer.objects.only(*myfields)
    serializer_class = FarmerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = LimitOffsetPagination
    filterset_class = FarmerFilter
    search_fields = [
        "f_id",
        "user_name",
        "first_name",
        "last_name",
        "gender",
        "sub_district",
        "state",
        "address",
        "ekyf_id",
        "f_phone",
        "aadhar_no",
    ]

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer : FarmerSerializer):
        with transaction.atomic():
            instance = serializer.save()
            if instance.aadhar_photo:
                aadhar_no = fetch_aadhaar(instance.aadhar_photo.path)
                if not aadhar_no:
                    raise serializers.ValidationError({"message":"Invalid Aadhaar image"})

                instance.aadhar_no = aadhar_no
                instance.save()
    
    def perform_update(self, serializer:FarmerSerializer):
        with transaction.atomic():
            instance = serializer.save()
            if "aadhar_photo" in self.request.data:
                aadhar_no = fetch_aadhaar(instance.aadhar_photo.path)
                if not aadhar_no:
                    raise serializers.ValidationError({"message":"Invalid Aadhaar image"})

                instance.aadhar_no = aadhar_no
                instance.save()

class StockDetailTableViewSet(CommonViewSet):
    myfields = CommonViewSet.myfields + [
        "id",
        "stock_id",
        "stock_id__crop_id__crop_name",
        "stock_id__farmer_id__first_name",
        "harvested_date",
        "hectares",
        "quantity",
        "unit",
        "price_per_unit",
        "expiry_date",
        "stored_location",
    ]
    extra_fields = {
        "crop_name": F("stock_id__crop_id__crop_name"),
        "first_name": F("stock_id__farmer_id__first_name"),
    }
    queryset = (
        StockDetail.objects.select_related("stock_id__crop_id", "stock_id__farmer_id")
        .filter(
            stock_id__crop_id__deleted=False,
            stock_id__farmer_id__deleted=False,
            stock_id__deleted=False,
        )
        .annotate(**extra_fields)
        .only(*myfields)
    )
    serializer_class = StockDetailTableSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    pagination_class = LimitOffsetPagination
    filterset_class = StockDetailFilter
    search_fields = [
        "stock_id__crop_id__crop_name",
        "stock_id__farmer_id__first_name",
        "harvested_date",
        "hectares",
        "quantity",
        "unit",
        "price_per_unit",
        "expiry_date",
        "stored_location",
    ]
    ordering_fields = "__all__"


class StockMasterViewSet(CommonViewSet):
    myfields = CommonViewSet.myfields + [
        "stock_id",
        "items",
        "crop_id",
        "farmer_id",
        "crop_id__crop_name",
        "farmer_id__first_name",
    ]
    extra_fields = {
        "crop_name": F("crop_id__crop_name"),
        "first_name": F("farmer_id__first_name"),
        "total_quantity": Subquery(
            StockDetail.objects.filter(stock_id=OuterRef("pk")).
            values("stock_id")
            .annotate(
                total_quantity = Sum("quantity")
            ).values("total_quantity")
        ),
    }
    queryset = (
        StockMaster.objects.select_related("crop_id", "farmer_id")
        .filter(crop_id__deleted=False, farmer_id__deleted=False)
        .prefetch_related("items")
        .annotate(**extra_fields)
        .only(*myfields)
    )
    serializer_class = StockMasterSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    permission_classes = [IsAuthenticated]
    filterset_class = CommonFilter
    search_fields = [
        "crop_id__crop_name",
        "farmer_id__first_name",
    ]
    ordering_fields = "__all__"

    def get_serializer_class(self):
        if self.action == "retrieve":
            self.serializer_class = StockMasterRetrieveSerializer
        elif self.action == "create":
            self.serializer_class = StockMasterCreateSerializer

        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == "list":
            if "items" in self.myfields:
                self.myfields.remove("items")
            self.queryset = (
                StockMaster.objects.select_related("crop_id", "farmer_id")
                .filter(crop_id__deleted=False, farmer_id__deleted=False)
                .annotate(**self.extra_fields)
                .only(*self.myfields)
            )
        return super().get_queryset()


class ListingViewSet(CommonViewSet):
    myfields = CommonViewSet.myfields + [
        "l_id",
        "qty_available",
        "price_per_unit",
        "status",
        "stock_detail",
    ]
    extra_fields = {
        "crop_name": F("stock_detail__stock_id__crop_id__crop_name"),
        "first_name": F("stock_detail__stock_id__farmer_id__first_name"),
    }
    queryset = (
        Listing.objects.select_related("stock_detail")
        .filter(
            stock_detail__stock_id__crop_id__deleted=False,
            stock_detail__stock_id__farmer_id__deleted=False,
            stock_detail__stock_id__deleted=False,
            stock_detail__deleted=False,
        )
        .annotate(**extra_fields)
        .only(*myfields)
    )
    serializer_class = ListingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination
    filterset_class = ListingFilter
    search_fields = [
        "l_id",
        "qty_available",
        "price_per_unit",
        "status",
        "stock_detail__stock_id__crop_id__crop_name",
        "stock_detail__stock_id__farmer_id__first_name",
    ]
    ordering_fields = "__all__"

    def get_queryset(self):
        if self.action != "retrieve":
            if "stock_detail__id" not in self.myfields:
                self.myfields.append("stock_detail__id")
                return super().get_queryset().only(*self.myfields)
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == "retrieve":
            self.serializer_class = ListingRetrieveSerializer
        return super().get_serializer_class()

    def __broadcast_if_sold(self, old_status: str, listing: Listing):
        """
        This is for if Listing's status became SOLD we
        have to broadcast to websocket
        """
        if old_status != "S" and listing.status == "S":
            with transaction.atomic():
                winner_bid = (
                    Bidding.objects.filter(l_id=listing.l_id)
                    .order_by("-price_per_unit")
                    .only(
                        "price_per_unit",
                        "bidder_id__business_name",
                        "b_id",
                        "status",
                        "bidder_id",
                    )
                    .first()
                )
                if winner_bid:
                    winner_bid.status = "A"
                    winner_bid.save()

                    Bidding.objects.filter(l_id=listing.l_id).exclude(
                        b_id=winner_bid.b_id
                    ).update(status="R")
                    if not Orders.objects.filter(b_id=winner_bid.b_id).exists():
                        Orders.objects.create(
                            b_id=winner_bid, price_per_unit=winner_bid.price_per_unit
                        )
                    winner_bid_data = {
                        "b_id": winner_bid.b_id,
                        "wholesaler_name": winner_bid.bidder_id.business_name,
                        "price_per_unit_str": str(winner_bid.price_per_unit),
                        "bidder_id": winner_bid.bidder_id.w_id,
                    }
                else:
                    winner_bid_data = {}
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"bids-of-{listing.l_id}",
                {
                    "success": True,
                    "type": "bid_closed",
                    "message": "Bid Closed",
                    "winner_bid": winner_bid_data,
                },
            )

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_queryset().select_for_update().get(pk=kwargs["pk"])
            old_status = instance.status
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            instance.refresh_from_db()
            self.__broadcast_if_sold(old_status, instance)

            return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_queryset().select_for_update().get(pk=kwargs["pk"])
            old_status = instance.status
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            instance.refresh_from_db()
            self.__broadcast_if_sold(old_status, instance)

            return Response(serializer.data)


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            try:
                farmer = Farmer.objects.get(user_name=validated_data["username"])
                if check_password(validated_data["password"], farmer.password):
                    farmer.id = farmer.f_id
                    token = RefreshToken.for_user(farmer)
                    token["first_name"] = farmer.first_name
                    token["last_name"] = farmer.last_name
                    token["address"] = farmer.address
                    token["f_photo"] = str(farmer.f_photo)
                    token["ekyf_id"] = farmer.ekyf_id
                    token["aadhar_no"] = farmer.aadhar_no
                    token["f_phone"] = farmer.f_phone
                    token["gender"] = farmer.gender
                    token["sub_district"] = farmer.sub_district
                    token["state"] = farmer.state

                    return Response(
                        {"refresh": str(token), "access": str(token.access_token)},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"message": "Farmer does not exists!"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except Farmer.DoesNotExist:
                return Response(
                    {"message": " Farmer does not exists!"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        access = request.auth
        refresh = RefreshToken(request.data["refresh"])
        self.__blacklist_token(refresh)
        self.__blacklist_token(access)
        return Response({"details": "Logged out Successfully!"})

    def __blacklist_token(self, token):
        jti = token.get("jti")
        exp = token.get("exp")
        now = token.current_time.timestamp()
        storetill = int(exp - now)
        cache.set(f"blacklist({jti})", "true", timeout=storetill)


class RedisTokenFarmerRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = RefreshToken(request.data["refresh"])
        jti = refresh["jti"]

        if cache.get(f"blacklist({jti})", None):
            raise InvalidToken({"detail": "Refresh Token is Invalid or expired!"})
        return super().post(request, *args, **kwargs)
