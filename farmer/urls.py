from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register("farmer",views.FarmerViewSet,basename="farmer")
router.register("stock-detail",views.StockDetailTableViewSet,basename="stock-detail")
router.register("stock-master",views.StockMasterViewSet,basename="stock-master")
router.register("listing",viewset=views.ListingViewSet,basename="listing")
router.register("price-prediction", viewset=views.PricePredictionViewSet,basename="price-prediction")
urlpatterns = [
    path("login/",views.LoginView.as_view(),name="login"),
    path("logout/",views.LogoutView.as_view(),name= "logout"),
    path("refresh/",views.RedisTokenFarmerRefreshView.as_view(),name="refresh"),
    path("state/",views.StateListView.as_view(),name="state"),
    path("district/",views.DistrictListView.as_view(),name="district"),
    path("commodity/",views.CommodityListView.as_view(),name="commodity"),
    path("grade/",views.GradeListView.as_view(),name="grade"),
    path("variety/",views.VarietyListView.as_view(),name="variety"),
    path("market/",views.MarketListView.as_view(),name="market"),
]
urlpatterns += router.urls