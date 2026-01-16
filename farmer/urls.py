from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register("farmer",views.FarmerViewSet,basename="farmer")
urlpatterns = []
urlpatterns += router.urls