from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("crop",views.CropViewSet,basename="cropMaster")

urlpatterns = [
    path("password-reset-request/",views.PasswordResetRequest.as_view(),name="password-reset-request"),
    path("password-reset-confirm/",views.PasswordResetConfirm.as_view(),name="password-reset-confirm"),
    path("api/token/",views.MyTokenObtainPairView.as_view(),name="token_obtain_pair"),
    path("api/token/refresh/",views.RedisTokenRefreshView.as_view(),name="token_refresh"),
    path("logout/",views.LogoutView.as_view(),name="logout"),
]

urlpatterns += router.urls