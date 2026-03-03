from django.shortcuts import render
from rest_framework import viewsets, mixins
from wholesaler.models import Wholesaler, StockDetail, StockMaster
from wholesaler.serializer import *
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import F , Subquery , Sum , OuterRef
from .filters import *


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


class WholesalerViewSet(CommonViewSet):
    myfields = CommonViewSet.myfields + [
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
        "pan_no",
    ]
    queryset = Wholesaler.objects.only(*myfields)
    serializer_class = WholesalerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    pagination_class = LimitOffsetPagination
    filterset_class = WholesalerFilter
    search_fields = [
        "w_id",
        "email",
        "first_name",
        "last_name",
        "gender",
        "city",
        "state",
        "address",
        "w_phone",
        "aadhar_no",
        "gst_no",
        "business_name",
        "status",
        "pan_no",
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
        "stock_id__w_id__first_name",
        "quantity",
        "price_per_unit",
        "intake_date",
        "expiry_date",
        "warehouse_loc",
    ]
    extra_fields = {
        "crop_name": F("stock_id__crop_id__crop_name"),
        "first_name": F("stock_id__w_id__first_name"),
    }
    queryset = (
        StockDetail.objects.select_related("stock_id__crop_id", "stock_id__w_id")
        .filter(
            stock_id__crop_id__deleted=False,
            stock_id__w_id__deleted=False,
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
        "stock_id__w_id__first_name",
        "quantity",
        "price_per_unit",
        "intake_date",
        "expiry_date",
        "warehouse_loc"
    ]
    ordering_fields = "__all__"


class StockMasterViewSet(CommonViewSet):
    myfields = CommonViewSet.myfields + [
        "stock_id",
        "items",
        "crop_id",
        "w_id",
        "crop_id__crop_name",
        "w_id__first_name",
    ]
    extra_fields = {
        "crop_name": F("crop_id__crop_name"),
        "first_name": F("w_id__first_name"),
        "total_quantity": Subquery(
            StockDetail.objects.filter(stock_id=OuterRef("pk")).
            values("stock_id")
            .annotate(
                total_quantity = Sum("quantity")
            ).values("total_quantity")
        ),
    }
    queryset = (
        StockMaster.objects.select_related("crop_id", "w_id")
        .filter(crop_id__deleted = False, w_id__deleted = False)
        .prefetch_related("items")
        .annotate(**extra_fields)
        .only(*myfields)
    )
    serializer_class = StockMasterSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    permission_classes = [IsAuthenticated]
    filterset_class = StockMasterFilter
    search_fields = [
        "crop_id__crop_name",
        "w_id__first_name",
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
                StockMaster.objects.select_related("crop_id", "w_id")
                .filter(crop_id__deleted = False, w_id__deleted = False)
                .annotate(**self.extra_fields)
                .only(*self.myfields)
            )
        return super().get_queryset()
