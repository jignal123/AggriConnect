import django_filters
from farmer.models import CropMaster


class CropFilter(django_filters.FilterSet):
    class Meta:
        model = CropMaster
        fields = {
            "crop_name":["iexact", "icontains", "istartswith", "iendswith"],
            "crop_variety":["iexact", "icontains", "istartswith", "iendswith"],
            "description":["iexact", "icontains", "istartswith", "iendswith"],
        }
