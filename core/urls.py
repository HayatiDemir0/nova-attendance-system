from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin'i gizli URL'ye taşı
    path('gizli-yonetim-2024/', admin.site.urls),  # /admin/ yerine
    
    # Ana URL'ler
    path('', include('core.urls')),
]

# Media dosyaları için
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)