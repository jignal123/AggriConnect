from django.shortcuts import render
from rest_framework import viewsets, mixins
from .models import Farmer
from .serializer import FarmerSerializer
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.filters import SearchFilter,OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination

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

    pass


class FarmerViewSet(CommonViewSet):
    my_fields = (
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
    queryset = Farmer.objects.only(*my_fields)
    serializer_class = FarmerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [AllowAny]
        elif self.action in ("list"):
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()
