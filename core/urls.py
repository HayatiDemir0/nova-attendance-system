from django.urls import path
from . import views

urlpatterns = [
    # Genel
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ==================== ADMİN PANELİ ====================
    path('admin-panel/', views.yonetim_panel, name='yonetim_panel'),
    path('admin-panel/ogretmenler/', views.yonetim_ogretmenler, name='yonetim_ogretmenler'),
    path('admin-panel/siniflar/', views.yonetim_siniflar, name='yonetim_siniflar'),
    path('admin-panel/ogrenciler/', views.yonetim_ogrenciler, name='yonetim_ogrenciler'),
    path('admin-panel/ders-programi/', views.yonetim_ders_programi, name='yonetim_ders_programi'),
    path('admin-panel/yoklamalar/', views.yonetim_yoklamalar, name='yonetim_yoklamalar'),
    path('admin-panel/ayarlar/', views.yonetim_ayarlar, name='yonetim_ayarlar'),
    
    # Öğretmenler
    path('ogretmenler/', views.ogretmen_listesi, name='ogretmen_listesi'),
    path('ogretmenler/ekle/', views.ogretmen_ekle, name='ogretmen_ekle'),
    path('ogretmenler/<int:pk>/duzenle/', views.ogretmen_duzenle, name='ogretmen_duzenle'),
    path('ogretmenler/<int:pk>/sil/', views.ogretmen_sil, name='ogretmen_sil'),
    
    # Sınıflar
    path('siniflar/', views.sinif_listesi, name='sinif_listesi'),
    path('siniflar/ekle/', views.sinif_ekle, name='sinif_ekle'),
    path('siniflar/<int:pk>/duzenle/', views.sinif_duzenle, name='sinif_duzenle'),
    path('siniflar/<int:pk>/sil/', views.sinif_sil, name='sinif_sil'),
    
    # Öğrenciler
    path('ogrenciler/', views.ogrenci_listesi, name='ogrenci_listesi'),
    path('ogrenciler/ekle/', views.ogrenci_ekle, name='ogrenci_ekle'),
    path('ogrenciler/<int:pk>/duzenle/', views.ogrenci_duzenle, name='ogrenci_duzenle'),
    path('ogrenciler/<int:pk>/sil/', views.ogrenci_sil, name='ogrenci_sil'),
    path('ogrenciler/<int:pk>/detay/', views.ogrenci_detay, name='ogrenci_detay'),
    path('ogrenciler/<int:pk>/not-ekle/', views.ogrenci_not_ekle, name='ogrenci_not_ekle'),
    path('ogrenci-notu/<int:pk>/duzenle/', views.ogrenci_not_duzenle, name='ogrenci_not_duzenle'),
    path('ogrenci-notu/<int:pk>/sil/', views.ogrenci_not_sil, name='ogrenci_not_sil'),
    
    # Ders Programı
    path('ders-programi/', views.ders_programi_listesi, name='ders_programi_listesi'),
    path('ders-programi/ekle/', views.ders_programi_ekle, name='ders_programi_ekle'),
    path('ders-programi/<int:pk>/duzenle/', views.ders_programi_duzenle, name='ders_programi_duzenle'),
    path('ders-programi/<int:pk>/sil/', views.ders_programi_sil, name='ders_programi_sil'),
    
    # Yoklama
    path('yoklama/al/<int:ders_id>/', views.yoklama_al, name='yoklama_al'),
    path('yoklama/duzenle/<int:pk>/', views.yoklama_duzenle, name='yoklama_duzenle'),
    path('yoklama/gecmis/', views.yoklama_gecmis, name='yoklama_gecmis'),
    path('yoklama/detay/<int:pk>/', views.yoklama_detay, name='yoklama_detay'),
    
    # Takvim
    path('takvim/', views.takvim, name='takvim'),
]