# from django.contrib import admin
from django.urls import path,include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    # path('admin/', admin.site.urls),
    path("admin-api/",include("Admin.urls")),
    path("farmer-api/",include("farmer.urls")),
    path("wholesaler-api/", include("wholesaler.urls")),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/doc-with-testing/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/view-only-doc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('silk/', include('silk.urls', namespace='silk')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)