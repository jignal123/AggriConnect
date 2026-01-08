from django.urls import path
from . import views
from rest_framework_simplejwt.views import(
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("password-reset-request/",views.PasswordResetRequest.as_view(),name="password-reset-request"),
    path("password-reset-confirm/",views.PasswordResetConfirm.as_view(),name="password-reset-confirm"),
    path("api/token/",TokenObtainPairView.as_view(),name="token_obtain_pair"),
    path("api/token/refresh/",TokenRefreshView.as_view(),name="token_refresh"),
]