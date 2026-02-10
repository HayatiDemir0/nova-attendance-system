from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, YoklamaDetay

# Admin Site Özelleştirme
admin.site.site_header = "Yoklama Sistemi Yönetim Paneli"
admin.site.site_title = "Yoklama Sistemi"
admin.site.index_title = "Yönetim Paneline Hoş Geldiniz"

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name_display', 'email', 'role_badge', 'is_active', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Ek Bilgiler', {
            'fields': ('role', 'telefon', 'adres', 'profil_resmi')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Ek Bilgiler', {
            'fields': ('role', 'first_name', 'last_name', 'email', 'telefon', 'adres')
        }),
    )
    
    def full_name_display(self, obj):
        return obj.get_full_name() or '-'
    full_name_display.short_description = 'Ad Soyad'
    
    def role_badge(self, obj):
        colors = {
            'admin': 'red',
            'ogretmen': 'green'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.role, 'gray'),
            obj.get_role_display()
        )
    role_badge.short_description = 'Rol'

@admin.register(Sinif)
class SinifAdmin(admin.ModelAdmin):
    list_display = ['ad', 'ogrenci_sayisi_display', 'aktif_ogrenci_sayisi', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    list_filter = ['olusturma_tarihi']
    ordering = ['ad']
    
    fieldsets = (
        ('Sınıf Bilgileri', {
            'fields': ('ad', 'aciklama')
        }),
    )
    
    def ogrenci_sayisi_display(self, obj):
        return obj.ogrenciler.count()
    ogrenci_sayisi_display.short_description = 'Toplam Öğrenci'
    
    def aktif_ogrenci_sayisi(self, obj):
        aktif = obj.ogrenciler.filter(aktif=True).count()
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            aktif
        )
    aktif_ogrenci_sayisi.short_description = 'Aktif Öğrenci'

@admin.register(Ogrenci)
class OgrenciAdmin(admin.ModelAdmin):
    list_display = ['tam_ad_display', 'tc_kimlik', 'sinif_badge', 'cinsiyet', 'veli_telefon', 'aktif', 'kayit_tarihi']
    list_filter = ['sinif', 'aktif', 'cinsiyet', 'kayit_tarihi']
    search_fields = ['ad', 'soyad', 'tc_kimlik', 'veli_adi', 'veli_telefon']
    list_editable = ['aktif']
    ordering = ['sinif__ad', 'ad', 'soyad']
    # date_hierarchy kaldırıldı - timezone hatası yüzünden
    
    fieldsets = (
        ('Öğrenci Bilgileri', {
            'fields': ('ad', 'soyad', 'tc_kimlik', 'dogum_tarihi', 'cinsiyet', 'sinif', 'profil_resmi')
        }),
        ('Veli Bilgileri', {
            'fields': ('veli_adi', 'veli_telefon', 'adres')
        }),
        ('Durum', {
            'fields': ('aktif',)
        }),
    )
    
    def tam_ad_display(self, obj):
        return obj.tam_ad
    tam_ad_display.short_description = 'Ad Soyad'
    
    def sinif_badge(self, obj):
        return format_html(
            '<span style="background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.sinif.ad
        )
    sinif_badge.short_description = 'Sınıf'

@admin.register(DersProgrami)
class DersProgramiAdmin(admin.ModelAdmin):
    list_display = ['ders_adi', 'ogretmen_display', 'sinif_badge', 'gun_display', 'saat_display', 'aktif']
    list_filter = ['gun', 'aktif', 'ogretmen', 'sinif']
    search_fields = ['ders_adi', 'ogretmen__first_name', 'ogretmen__last_name', 'sinif__ad']
    list_editable = ['aktif']
    ordering = ['gun', 'baslangic_saati']
    
    fieldsets = (
        ('Ders Bilgileri', {
            'fields': ('ders_adi', 'ogretmen', 'sinif')
        }),
        ('Zaman', {
            'fields': ('gun', 'baslangic_saati', 'bitis_saati')
        }),
        ('Durum', {
            'fields': ('aktif',)
        }),
    )
    
    def ogretmen_display(self, obj):
        return obj.ogretmen.get_full_name() or obj.ogretmen.username
    ogretmen_display.short_description = 'Öğretmen'
    
    def sinif_badge(self, obj):
        return format_html(
            '<span style="background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.sinif.ad
        )
    sinif_badge.short_description = 'Sınıf'
    
    def gun_display(self, obj):
        return obj.get_gun_display()
    gun_display.short_description = 'Gün'
    
    def saat_display(self, obj):
        return f"{obj.baslangic_saati.strftime('%H:%M')} - {obj.bitis_saati.strftime('%H:%M')}"
    saat_display.short_description = 'Saat'

class YoklamaDetayInline(admin.TabularInline):
    model = YoklamaDetay
    extra = 0
    fields = ['ogrenci', 'durum', 'not_durumu']
    
    def has_add_permission(self, request, obj=None):
        return True  # Öğrenci ekleyebilme

@admin.register(Yoklama)
class YoklamaAdmin(admin.ModelAdmin):
    list_display = ['ders_basligi', 'tarih', 'ogretmen_display', 'sinif_badge', 'ders_display', 'olusturma_zamani']
    list_filter = ['tarih', 'ogretmen', 'sinif', 'olusturma_zamani']
    search_fields = ['ders_basligi', 'ogretmen__first_name', 'ogretmen__last_name', 'sinif__ad']
    # date_hierarchy kaldırıldı - timezone hatası olabilir
    ordering = ['-tarih', '-olusturma_zamani']
    inlines = [YoklamaDetayInline]
    
    fieldsets = (
        ('Yoklama Bilgileri', {
            'fields': ('ders_programi', 'tarih', 'ders_basligi', 'ogretmen', 'sinif')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Yoklama kaydedilirken öğretmen ve sınıf otomatik doldurulsun"""
        if not change:  # Yeni kayıt ise
            # Ders programından öğretmen ve sınıfı al
            if obj.ders_programi:
                obj.ogretmen = obj.ders_programi.ogretmen
                obj.sinif = obj.ders_programi.sinif
        super().save_model(request, obj, form, change)
    
    def ogretmen_display(self, obj):
        return obj.ogretmen.get_full_name() or obj.ogretmen.username
    ogretmen_display.short_description = 'Öğretmen'
    
    def sinif_badge(self, obj):
        return format_html(
            '<span style="background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.sinif.ad
        )
    sinif_badge.short_description = 'Sınıf'
    
    def ders_display(self, obj):
        return obj.ders_programi.ders_adi
    ders_display.short_description = 'Ders'

@admin.register(YoklamaDetay)
class YoklamaDetayAdmin(admin.ModelAdmin):
    list_display = ['yoklama_display', 'ogrenci', 'durum_badge', 'not_durumu']
    list_filter = ['durum', 'yoklama__tarih', 'yoklama__sinif']
    search_fields = ['ogrenci__ad', 'ogrenci__soyad', 'yoklama__ders_basligi']
    ordering = ['-yoklama__tarih']
    
    def yoklama_display(self, obj):
        return f"{obj.yoklama.ders_basligi} ({obj.yoklama.tarih})"
    yoklama_display.short_description = 'Yoklama'
    
    def durum_badge(self, obj):
        colors = {
            'var': 'green',
            'yok': 'red',
            'izinli': 'orange',
            'gec': 'blue'
        }
        icons = {
            'var': '✓',
            'yok': '✗',
            'izinli': '🏥',
            'gec': '⏰'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.durum, 'gray'),
            icons.get(obj.durum, ''),
            obj.get_durum_display()
        )
    durum_badge.short_description = 'Durum'