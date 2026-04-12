from rest_framework import viewsets, mixins
from wholesaler.models import Wholesaler, StockDetail, StockMaster
from wholesaler.serializer import *
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import F, Subquery, Sum, OuterRef
from .filters import *
from rest_framework.response import Response
from farmer.models import StockDetail as FarmerStock
from rest_framework.views import status , APIView
from Admin.extra_func import fetch_aadhaar
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from rest_framework_simplejwt.views  import TokenRefreshView
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError
import tempfile
import os

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
        "aadhar_photo",
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
        else :
            self.permission_classes = [IsAuthenticated]
        
        return super().get_permissions()
    
    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            
            if instance.aadhar_photo:
                # 1. Grab the raw bytes directly from the S3 object
                image_bytes = instance.aadhar_photo.read()
                
                # 2. Pass those bytes into your OCR function
                aadhar_no = fetch_aadhaar(image_bytes)
                
                if not aadhar_no:
                    raise serializers.ValidationError(
                        {"message": "Invalid Aadhaar image"}
                    )

                instance.aadhar_no = aadhar_no
                instance.save()
    
    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            
            # Only run OCR if a NEW photo was uploaded in this request
            if "aadhar_photo" in self.request.data and instance.aadhar_photo:
                
                # Grab the raw bytes directly from the S3 object in memory
                image_bytes = instance.aadhar_photo.read()
                
                # Pass those bytes into your updated OCR function
                aadhar_no = fetch_aadhaar(image_bytes)
                
                if not aadhar_no:
                    raise serializers.ValidationError(
                        {"message": "Invalid Aadhaar image"}
                    )

                instance.aadhar_no = aadhar_no
                instance.save()

    def handle_exception(self, exc):
        """
        This method is called automatically by DRF when an error occurs.
        """
        if isinstance(exc, IntegrityError):
            return Response(
                {"error": "Error: Likely a duplicate entry or missing reference.Check your Aadhar"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For all other errors, use the default DRF behavior
        return super().handle_exception(exc)


class StockDetailTableViewSet(CommonViewSet):
    myfields = CommonViewSet.myfields + [
        "id",
        "stock_id",
        "stock_id__crop_id__crop_name",
        "stock_id__w_id__first_name",
        "quantity",
        "price_per_unit",
        "unit",
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
        "unit",
        "expiry_date",
        "warehouse_loc",
    ]
    ordering_fields = "__all__"

    def get_queryset(self):
        if not self.request.user.is_staff:
            self.queryset = self.queryset.filter(stock_id__w_id = self.request.user)
        return super().get_queryset()


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
            StockDetail.objects.filter(stock_id=OuterRef("pk"))
            .values("stock_id")
            .annotate(total_quantity=Sum("quantity"))
            .values("total_quantity")
        ),
    }
    queryset = (
        StockMaster.objects.select_related("crop_id", "w_id")
        .filter(crop_id__deleted=False, w_id__deleted=False)
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
                .filter(crop_id__deleted=False, w_id__deleted=False)
                .annotate(**self.extra_fields)
                .only(*self.myfields)
            )
        if not self.request.user.is_staff:
            self.queryset = self.queryset.filter(w_id = self.request.user)
        return super().get_queryset()


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    myfields = CommonViewSet.myfields + [
        "o_id",
        "b_id",
        "order_date",
        "status",
        "price_per_unit",
        "delivery_date",
        "b_id__b_id",
    ]
    extra_fields = {
        "crop_name": F("b_id__l_id__stock_detail__stock_id__crop_id__crop_name"),
        "bidder_name": F("b_id__bidder_id__business_name"),
        "farmer_name": F("b_id__l_id__stock_detail__stock_id__farmer_id__first_name"),
        "quantity": F("b_id__l_id__qty_available"),
        "unit": F("b_id__l_id__stock_detail__unit"),
        "stored_location": F("b_id__l_id__stock_detail__stored_location"),
    }
    serializer_class = OrderSerializer
    queryset = (
        Orders.objects.select_related(
            "b_id"
        ).annotate(**extra_fields)
        .only(*myfields)
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    filterset_class = OrderFilter
    search_fields = [
        "order_date",
        "status",
        "price_per_unit",
        "delivery_date",
        "b_id__l_id__stock_detail__stock_id__crop_id__crop_name",
        "b_id__bidder_id__business_name",
        "b_id__l_id__stock_detail__stock_id__farmer_id__first_name",
        "b_id__l_id__qty_available",
        "b_id__l_id__stock_detail__unit",
        "b_id__l_id__stock_detail__stored_location",
    ]
    pagination_class = LimitOffsetPagination
    ordering_fields = "__all__"
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            self.queryset =   self.queryset.filter(b_id__bidder_id = self.request.user)
        return super().get_queryset()

    def get_permissions(self):
        if self.action in ["update","partial_update"]:
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        return self._handle_update(request, partial=False, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self._handle_update(request, partial=True, **kwargs)

    def _handle_update(self, request, partial, **kwargs):

        with transaction.atomic():

            instance = (
                Orders.objects.select_for_update()
                .select_related(
                    "b_id",
                    "b_id__l_id",
                    "b_id__l_id__stock_detail",
                    "b_id__l_id__stock_detail__stock_id",
                    "b_id__bidder_id",
                )
                .get(pk=kwargs["pk"])
            )

            old_status = instance.status
            if old_status != "Paid":
                serializer = self.get_serializer(
                    instance, data=request.data, partial=partial
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

                self.__update_stock_details_if_paid(old_status, instance)
            else:
                return Response({
                    "message" : "You Can't Edit The Order Which is Paid!"
                },
                status= status.HTTP_412_PRECONDITION_FAILED)

            return Response(serializer.data)

    def __update_stock_details_if_paid(self, old_status, instance: Orders):
        if old_status != "Paid" and instance.status == "Paid":

            bidding = instance.b_id
            listing = bidding.l_id
            wholesaler = bidding.bidder_id

            qty = listing.qty_available
            farmer_stock_detail = listing.stock_detail
            unit = farmer_stock_detail.unit
            crop = farmer_stock_detail.stock_id.crop_id
            price = instance.price_per_unit

            FarmerStock.objects.filter(pk=farmer_stock_detail.pk).update(
                quantity=F("quantity") - qty
            )

            w_stock_master, _ = StockMaster.objects.get_or_create(
                crop_id=crop, w_id=wholesaler
            )
            StockDetail.objects.create(
                stock_id=w_stock_master,
                quantity=qty,
                unit=unit,
                price_per_unit=price,
                intake_date=instance.order_date,
                expiry_date=farmer_stock_detail.expiry_date,
            )

class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            try:
                wholesaler = Wholesaler.objects.get(email=validated_data["email"])
                if check_password(validated_data["password"], wholesaler.password):
                    wholesaler.id = wholesaler.w_id
                    token = RefreshToken.for_user(wholesaler)
                    token["first_name"] = wholesaler.first_name
                    token["last_name"] = wholesaler.last_name
                    token["status"] = wholesaler.status
                    token["pan_no"] = wholesaler.pan_no
                    token["address"] = wholesaler.address
                    token["role"] = "wholesaler"
                    token["w_photo"] = str(wholesaler.w_photo)
                    token["business_proof"] = str(wholesaler.business_proof)
                    token["aadhar_photo"] = str(wholesaler.aadhar_photo)
                    token["aadhar_no"] = wholesaler.aadhar_no
                    token["w_phone"] = wholesaler.w_phone
                    token["gender"] = wholesaler.gender
                    token["city"] = wholesaler.city
                    token["business_name"] = wholesaler.business_name
                    token["gst_no"] = wholesaler.gst_no
                    token["state"] = wholesaler.state

                    return Response(
                        {"refresh": str(token), "access": str(token.access_token)},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"message": "wholesaler does not exists!"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except Wholesaler.DoesNotExist:
                return Response(
                    {"message": " wholesaler does not exists!"},
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


class RedisTokenwholesalerRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = RefreshToken(request.data["refresh"])
        jti = refresh["jti"]

        if cache.get(f"blacklist({jti})", None):
            raise InvalidToken({"detail": "Refresh Token is Invalid or expired!"})
        return super().post(request, *args, **kwargs)