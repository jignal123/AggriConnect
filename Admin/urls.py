from django.urls import path
from . import views

urlpatterns = [
    path("password-reset-request/",views.PasswordResetRequest.as_view(),name="password-reset-request"),
    path("password-reset-confirm/",views.PasswordResetConfirm.as_view(),name="password-reset-confirm"),
]