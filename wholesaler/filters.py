import django_filters
from .models import StockDetail, Wholesaler,StockMaster

class CommonFilter(django_filters.FilterSet):
    crop_name = django_filters.CharFilter(field_name="crop_name", lookup_expr="iexact")
    wholesaler_name = django_filters.CharFilter(
        field_name="first_name", lookup_expr="iexact"
    )

    class Meta:
        fields = []

class StockDetailFilter(CommonFilter):
    class Meta:
        model = StockDetail
        fields = {
            "intake_date": [
                "iexact",
                "range",
                "lt",
                "gt",
                "lte",
                "gte",
                "year",
                "month",
                "day",
            ],
            "quantity": ["iexact", "range", "lt", "gt", "lte", "gte"],
            "unit": ["iexact", "range", "lt", "gt", "lte", "gte"],
            "price_per_unit": ["iexact", "range", "lt", "gt", "lte", "gte"],
            "expiry_date": [
                "iexact",
                "range",
                "lt",
                "gt",
                "lte",
                "gte",
                "year",
                "month",
                "day",
            ],
            "warehouse_loc": ["iexact", "icontains", "istartswith", "iendswith"],
        }

class StockMasterFilter(CommonFilter):
    class Meta:
        model = StockMaster
        fields = [
            "stock_id"
        ]

class WholesalerFilter(django_filters.FilterSet):
    class Meta:
        model = Wholesaler
        fields = {
            "email":["iexact", "icontains", "istartswith", "iendswith"],
            "first_name":["iexact", "icontains", "istartswith", "iendswith"],
            "last_name":["iexact", "icontains", "istartswith", "iendswith"],
            "gender":["iexact", "icontains", "istartswith", "iendswith"],
            "pan_no":["iexact", "icontains", "istartswith", "iendswith"],
            "state":["iexact", "icontains", "istartswith", "iendswith"],
            "address":["iexact", "icontains", "istartswith", "iendswith"],
            "gst_no":["iexact", "icontains", "istartswith", "iendswith"],
            "business_name":["iexact", "icontains", "istartswith", "iendswith"],
            "aadhar_no":["iexact", "icontains", "istartswith", "iendswith"],
        }