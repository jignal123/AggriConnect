# from django.contrib import admin
from django.urls import path,include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
urlpatterns = [
    # path('admin/', admin.site.urls),
    path("admin-api/",include("Admin.urls")),
    path("farmer-api/",include("farmer.urls")),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/doc-with-testing/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/view-only-doc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
