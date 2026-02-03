from rest_framework import viewsets, mixins
from .models import Farmer, StockDetail, StockMaster, Listing
from .serializer import *
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import F
from .filters import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from wholesaler.models import Bidding, Orders
from django.db import transaction
from rest_framework.response import Response

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
    search_filter = [
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
    }
    queryset = (
        StockMaster.objects.select_related("crop_id", "farmer_id")
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
            serializer = self.get_serializer(instance,data=request.data,partial = False)
            serializer.is_valid(raise_exception = True)
            self.perform_update(serializer)
            instance.refresh_from_db()
            self.__broadcast_if_sold(old_status, instance)

            return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_queryset().select_for_update().get(pk=kwargs["pk"])
            old_status = instance.status
            serializer = self.get_serializer(instance,data=request.data,partial = True)
            serializer.is_valid(raise_exception = True)
            self.perform_update(serializer)
            instance.refresh_from_db()
            self.__broadcast_if_sold(old_status, instance)

            return Response(serializer.data)
