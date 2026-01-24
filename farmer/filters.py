import django_filters
from .models import StockDetail, Listing, Farmer


class CommonFilter(django_filters.FilterSet):
    crop_name = django_filters.CharFilter(field_name="crop_name", lookup_expr="iexact")
    farmer_name = django_filters.CharFilter(
        field_name="first_name", lookup_expr="iexact"
    )

    class Meta:
        fields = []


class StockDetailFilter(CommonFilter):
    class Meta:
        model = StockDetail
        fields = {
            "harvested_date": [
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
            "hectares": ["iexact", "range", "lt", "gt", "lte", "gte"],
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
            "stored_location": ["iexact", "icontains", "istartswith", "iendswith"],
        }


class ListingFilter(CommonFilter):
    class Meta:
        model = Listing
        fields = {
            "qty_available": ["iexact", "range", "lt", "gt", "lte", "gte"],
            "price_per_unit": ["iexact", "range", "lt", "gt", "lte", "gte"],
            "status": ["iexact", "icontains", "istartswith", "iendswith"],
        }


class FarmerFilter(django_filters.FilterSet):
    class Meta:
        model = Farmer
        fields = {
            "user_name":["iexact", "icontains", "istartswith", "iendswith"],
            "first_name":["iexact", "icontains", "istartswith", "iendswith"],
            "last_name":["iexact", "icontains", "istartswith", "iendswith"],
            "gender":["iexact", "icontains", "istartswith", "iendswith"],
            "sub_district":["iexact", "icontains", "istartswith", "iendswith"],
            "state":["iexact", "icontains", "istartswith", "iendswith"],
            "address":["iexact", "icontains", "istartswith", "iendswith"],
            "ekyf_id":["iexact", "icontains", "istartswith", "iendswith"],
            "f_phone":["iexact", "icontains", "istartswith", "iendswith"],
            "aadhar_no":["iexact", "icontains", "istartswith", "iendswith"],
        }
