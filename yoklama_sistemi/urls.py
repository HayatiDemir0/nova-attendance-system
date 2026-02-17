from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

# --- OTOMATİK ADMİN OLUŞTURUCU ---
def create_extra_admin():
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Kullanıcı adını 'admin' olarak belirliyoruz
        if not User.objects.filter(username='admin').exists():
            # Buradaki şifreyi (Sifre123!) giriş yaptıktan sonra değiştirmeyi unutma!
            User.objects.create_superuser('admin', 'admin@example.com', 'Sifre123!')
            print("BAŞARILI: Süper kullanıcı 'admin' oluşturuldu.")
    except Exception as e:
        # Veritabanı henüz hazır değilse veya tablolar oluşmadıysa hata verebilir, normaldir.
        print(f"Bilgi: Admin oluşturma atlandı veya hata oluştu: {e}")

# Fonksiyonu çalıştır
create_extra_admin()
# --------------------------------

urlpatterns = [  
    path('admin/', admin.site.urls), # Admin panelini buraya ekledik
    path('', include('core.urls')),
]

# Media ve Static dosyaları için
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Render (Production) ortamında static dosyaları sunmak için
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)