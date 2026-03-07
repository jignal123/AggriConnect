from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register("wholesaler",views.WholesalerViewSet,basename="wholesaler")
router.register("stock-detail",views.StockDetailTableViewSet,basename="stock-detail")
router.register("stock-master",views.StockMasterViewSet,basename="stock-master")
router.register("order",views.OrderViewSet,basename="order")
urlpatterns = []
urlpatterns += router.urls