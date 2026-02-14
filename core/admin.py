from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django import forms
from django.core.exceptions import ValidationError
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, YoklamaDetay, OgrenciNotu

# --- Admin Site Özelleştirme ---
admin.site.site_header = "Yoklama Sistemi Yönetim Paneli"
admin.site.site_title = "Yoklama Sistemi"
admin.site.index_title = "Yönetim Paneline Hoş Geldiniz"

# --- Kelime Kontrolü İçin Form ---
class OgrenciNotuForm(forms.ModelForm):
    class Meta:
        model = OgrenciNotu
        fields = '__all__'

    def clean_aciklama(self):
        aciklama = self.cleaned_data.get('aciklama', '')
        kelime_sayisi = len(aciklama.split())
        if kelime_sayisi < 5:
            raise ValidationError(f"Not çok kısa! Lütfen en az 5 kelimeyle durumu açıklayın. (Şu an: {kelime_sayisi})")
        return aciklama

# --- User Admin ---
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name_display', 'email', 'role_badge', 'is_active', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Ek Bilgiler', {'fields': ('role', 'telefon', 'adres', 'profil_resmi')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Ek Bilgiler', {'fields': ('role', 'first_name', 'last_name', 'email', 'telefon', 'adres')}),
    )
    
    def full_name_display(self, obj): return obj.get_full_name() or '-'
    full_name_display.short_description = 'Ad Soyad'
    
    def role_badge(self, obj):
        colors = {'admin': 'red', 'ogretmen': 'green'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.role, 'gray'), obj.get_role_display()
        )
    role_badge.short_description = 'Rol'

# --- Sınıf Admin ---
@admin.register(Sinif)
class SinifAdmin(admin.ModelAdmin):
    list_display = ['ad', 'ogrenci_sayisi_display', 'aktif_ogrenci_sayisi', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    list_filter = ['olusturma_tarihi']
    ordering = ['ad']
    
    def ogrenci_sayisi_display(self, obj): return obj.ogrenciler.count()
    ogrenci_sayisi_display.short_description = 'Toplam Öğrenci'
    
    def aktif_ogrenci_sayisi(self, obj):
        aktif = obj.ogrenciler.filter(aktif=True).count()
        return format_html('<span style="color: green; font-weight: bold;">{}</span>', aktif)
    aktif_ogrenci_sayisi.short_description = 'Aktif Öğrenci'

# --- Öğrenci Notu (Inline) ---
class OgrenciNotuInline(admin.TabularInline):
    model = OgrenciNotu
    form = OgrenciNotuForm # Kelime kontrolü burada
    extra = 1
    fields = ['kategori', 'baslik', 'aciklama', 'tarih']

# --- Öğrenci Admin ---
@admin.register(Ogrenci)
class OgrenciAdmin(admin.ModelAdmin):
    list_display = ['tam_ad_display', 'tc_kimlik', 'sinif_badge', 'cinsiyet', 'veli_telefon', 'aktif', 'kayit_tarihi']
    list_filter = ['sinif', 'aktif', 'cinsiyet', 'kayit_tarihi']
    search_fields = ['ad', 'soyad', 'tc_kimlik', 'veli_adi', 'veli_telefon']
    list_editable = ['aktif']
    ordering = ['sinif__ad', 'ad', 'soyad']
    
    # SENİN KODUNDA EKSİK OLAN KRİTİK SATIR BURASIYDI:
    inlines = [OgrenciNotuInline] 
    
    fieldsets = (
        ('Öğrenci Bilgileri', {'fields': ('ad', 'soyad', 'tc_kimlik', 'dogum_tarihi', 'cinsiyet', 'sinif', 'profil_resmi')}),
        ('Veli Bilgileri', {'fields': ('veli_adi', 'veli_telefon', 'adres')}),
        ('Durum', {'fields': ('aktif',)}),
    )
    
    def tam_ad_display(self, obj): return obj.tam_ad
    tam_ad_display.short_description = 'Ad Soyad'
    
    def sinif_badge(self, obj):
        return format_html('<span style="background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>', obj.sinif.ad)
    sinif_badge.short_description = 'Sınıf'

# --- Ders Programı Admin ---
@admin.register(DersProgrami)
class DersProgramiAdmin(admin.ModelAdmin):
    list_display = ['ders_adi', 'ogretmen_display', 'sinif_badge', 'gun_display', 'saat_display', 'aktif']
    list_filter = ['gun', 'aktif', 'ogretmen', 'sinif']
    search_fields = ['ders_adi', 'ogretmen__first_name', 'ogretmen__last_name', 'sinif__ad']
    list_editable = ['aktif']
    ordering = ['gun', 'baslangic_saati']
    
    def ogretmen_display(self, obj): return obj.ogretmen.get_full_name() or obj.ogretmen.username
    def gun_display(self, obj): return obj.get_gun_display()
    def sinif_badge(self, obj):
        return format_html('<span style="background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>', obj.sinif.ad)
    def saat_display(self, obj):
        return f"{obj.baslangic_saati.strftime('%H:%M')} - {obj.bitis_saati.strftime('%H:%M')}"

# --- Yoklama Admin ---
class YoklamaDetayInline(admin.TabularInline):
    model = YoklamaDetay
    extra = 0
    fields = ['ogrenci', 'durum', 'not_durumu']

@admin.register(Yoklama)
class YoklamaAdmin(admin.ModelAdmin):
    list_display = ['ders_basligi', 'tarih', 'ogretmen_display', 'sinif_badge', 'ders_display', 'olusturma_zamani']
    list_filter = ['tarih', 'ogretmen', 'sinif']
    inlines = [YoklamaDetayInline]
    
    def save_model(self, request, obj, form, change):
        if not change and obj.ders_programi:
            obj.ogretmen = obj.ders_programi.ogretmen
            obj.sinif = obj.ders_programi.sinif
        super().save_model(request, obj, form, change)

    def ogretmen_display(self, obj): return obj.ogretmen.get_full_name() or obj.ogretmen.username
    def sinif_badge(self, obj):
        return format_html('<span style="background-color: #0d6efd; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>', obj.sinif.ad)
    def ders_display(self, obj): return obj.ders_programi.ders_adi

# --- Yoklama Detay Admin ---
@admin.register(YoklamaDetay)
class YoklamaDetayAdmin(admin.ModelAdmin):
    list_display = ['yoklama', 'ogrenci', 'durum_badge', 'not_durumu']
    
    def durum_badge(self, obj):
        colors = {'var': 'green', 'yok': 'red', 'izinli': 'orange', 'gec': 'blue'}
        return format_html('<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>', colors.get(obj.durum, 'gray'), obj.get_durum_display())

# --- Öğrenci Notu (Müstakil Yönetim) ---
@admin.register(OgrenciNotu)
class OgrenciNotuAdmin(admin.ModelAdmin):
    form = OgrenciNotuForm
    list_display = ['ogrenci', 'kategori', 'baslik', 'tarih', 'olusturan']
    list_filter = ['kategori', 'tarih']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.olusturan = request.user
        super().save_model(request, obj, form, change)