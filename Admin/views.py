from rest_framework import generics, status, mixins, viewsets
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import Admin
from farmer.models import CropMaster, Farmer
from wholesaler.models import Wholesaler, Bidding, Orders
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from .serializer import *
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework_simplejwt.views import TokenObtainPairView
from .filters import *
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
import calendar
# Create your views here.
class MyCustomViewSet(
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
    myfields = (
        "deleted",
        "created_at",
        "updated_at"
    )

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class PasswordResetRequest(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            if Admin.objects.filter(email=email).exists():
                admin = Admin.objects.get(email=email)
                uidb64 = urlsafe_base64_encode(force_bytes(admin.pk))
                token = PasswordResetTokenGenerator().make_token(admin)

                reset_link = f"http://localhost:3000/password-reset-confirm/{uidb64}/{token}"
                # print(reset_link)
                send_mail(
                    "Password Change Request",
                    f"Click the link to reset your password: {reset_link}",
                    "202500819010083@glsu.edu.in",
                    [email],
                    fail_silently=False,
                )

            return Response(
                {"Message": "If this email Exists, the reset link has been sent"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirm(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_id = urlsafe_base64_decode(
                serializer.validated_data["uidb64"]
            ).decode()
            admin = Admin.objects.get(pk=user_id)
            admin.set_password(serializer.validated_data["password"])
            admin.save()

            return Response(
                {"message": "Password Changed Successfully!"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = LogoutSerializer
    def post(self, request):
        access = request.auth
        refresh = RefreshToken(request.data["refresh"])
        self.blacklist_token(access)
        self.blacklist_token(refresh)
        return JsonResponse({"details": "Logged out Successfully!"})

    def blacklist_token(self, token):
        jti = token.get("jti")
        exp = token.get("exp")
        now = token.current_time.timestamp()
        storetill = int(exp - now)
        cache.set(f"blacklist({jti})", "true", timeout=storetill)


class RedisTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = RefreshToken(request.data["refresh"])
        jti = refresh["jti"]

        if cache.get(f"blacklist({jti})", None):
            raise InvalidToken({"detail": "Refresh Token is Invalid or expired!"})
        return super().post(request, *args, **kwargs)


class CropViewSet(MyCustomViewSet):
    myfields = MyCustomViewSet.myfields + (
        "crop_id",
        "crop_name",
        "crop_variety",
        "photo",
        "description",
    )
    queryset = CropMaster.objects.only(*myfields)
    serializer_class = CropMasterSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend,OrderingFilter,SearchFilter]
    pagination_class = LimitOffsetPagination
    search_fields = [
        "crop_name",
        "crop_variety",
        "description",
    ]
    filterset_class = CropFilter

    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class DashboardView(APIView):
    permission_classes = [IsAdminUser]
    serializer_class = DashboardSerializer

    def get(self, request):
        """
        Returns comprehensive dashboard metrics including:
        - Farmer and wholesaler counts
        - Stock analytics
        - Bidding statistics
        - Order statistics
        - Registration breakdown by day for current month
        """

        # Get current month date range
        today = timezone.now()
        first_day = today.replace(day=1)
        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        # Farmer Statistics
        farmers_total = Farmer.objects.filter(deleted=False).count()

        # Wholesaler Statistics
        wholesalers_total = Wholesaler.objects.filter(deleted=False).count()
        wholesalers_verified = Wholesaler.objects.filter(deleted=False, status="V").count()
        wholesalers_unverified = Wholesaler.objects.filter(deleted=False, status="U").count()

        # Stock Statistics - Farmer
        from wholesaler.models import StockDetail as WholesalerStockDetail
        from farmer.models import StockDetail as FarmerStockDetail

        farmer_stock_items = FarmerStockDetail.objects.filter(stock_id__deleted=False).count()
        farmer_stock_value = FarmerStockDetail.objects.filter(stock_id__deleted=False).aggregate(
            total=Sum(F("quantity") * F("price_per_unit"))
        )["total"] or 0

        # Stock Statistics - Wholesaler
        wholesaler_stock_items = WholesalerStockDetail.objects.filter(stock_id__deleted=False).count()
        wholesaler_stock_value = WholesalerStockDetail.objects.filter(stock_id__deleted=False).aggregate(
            total=Sum(F("quantity") * F("price_per_unit"))
        )["total"] or 0

        # Bidding Statistics
        biddings_total = Bidding.objects.count()
        biddings_pending = Bidding.objects.filter(status="P").count()
        biddings_accepted = Bidding.objects.filter(status="A").count()
        biddings_rejected = Bidding.objects.filter(status="R").count()

        # Order Statistics
        orders_total = Orders.objects.count()
        orders_pending = Orders.objects.filter( status="Pending").count()
        orders_paid = Orders.objects.filter( status="Paid").count()
        orders_rejected = Orders.objects.filter( status="Rejected").count()

        # Daily registration breakdown for farmers
        farmers_daily = self._get_daily_registration_breakdown(
            Farmer.objects.filter(created_at__date__gte=first_day.date(), created_at__date__lte=last_day.date()),
            first_day,
            last_day
        )

        # Daily registration breakdown for wholesalers
        wholesalers_daily = self._get_daily_registration_breakdown(
            Wholesaler.objects.filter(created_at__date__gte=first_day.date(), created_at__date__lte=last_day.date()),
            first_day,
            last_day
        )

        dashboard_data = {
            "farmers": {
                "total": farmers_total
            },
            "wholesalers": {
                "total": wholesalers_total,
                "verified": wholesalers_verified,
                "unverified": wholesalers_unverified
            },
            "stock": {
                "farmer": {
                    "total_items": farmer_stock_items,
                    "total_value": float(farmer_stock_value)
                },
                "wholesaler": {
                    "total_items": wholesaler_stock_items,
                    "total_value": float(wholesaler_stock_value)
                }
            },
            "biddings": {
                "total": biddings_total,
                "pending": biddings_pending,
                "accepted": biddings_accepted,
                "rejected": biddings_rejected
            },
            "orders": {
                "total": orders_total,
                "pending_payment": orders_pending,
                "paid": orders_paid,
                "rejected": orders_rejected
            },
            "registrations": {
                "farmers_current_month": {
                    "total": Farmer.objects.filter(
                        created_at__date__gte=first_day.date(),
                        created_at__date__lte=last_day.date()
                    ).count(),
                    "daily_breakdown": farmers_daily
                },
                "wholesalers_current_month": {
                    "total": Wholesaler.objects.filter(
                        created_at__date__gte=first_day.date(),
                        created_at__date__lte=last_day.date()
                    ).count(),
                    "daily_breakdown": wholesalers_daily
                }
            }
        }

        serializer = self.serializer_class(dashboard_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _get_daily_registration_breakdown(self, queryset, first_day, last_day):
        """
        Returns daily registration counts for the given date range.
        """
        daily_counts = queryset.extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(count=Count('pk')).order_by('date')

        # Create a complete list with all days in month (including days with 0 registrations)
        current_date = first_day.date()
        daily_breakdown = []

        while current_date <= last_day.date():
            day_count = next((item['count'] for item in daily_counts if item['date'] == current_date), 0)
            daily_breakdown.append({
                "date": current_date,
                "count": day_count
            })
            current_date += timedelta(days=1)

        return daily_breakdown