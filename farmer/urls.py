from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register("farmer",views.FarmerViewSet,basename="farmer")
router.register("stock-detail",views.StockDetailTableViewSet,basename="stock-detail")
router.register("stock-master",views.StockMasterViewSet,basename="stock-master")
router.register("listing",viewset=views.ListingViewSet,basename="listing")
urlpatterns = []
urlpatterns += router.urls