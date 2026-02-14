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

# --- ÖZEL FORMLAR (Kelime Kontrolleri) ---

class YoklamaForm(forms.ModelForm):
    class Meta:
        model = Yoklama
        fields = '__all__'

    def clean_ders_basligi(self):
        baslik = self.cleaned_data.get('ders_basligi', '')
        kelime_sayisi = len(baslik.split())
        if kelime_sayisi < 3:
            raise ValidationError(f"Ders konusu çok kısa! En az 3 kelime yazmalısınız. (Şu an: {kelime_sayisi})")
        return baslik

class OgrenciNotuForm(forms.ModelForm):
    class Meta:
        model = OgrenciNotu
        fields = '__all__'

    def clean_aciklama(self):
        aciklama = self.cleaned_data.get('aciklama', '')
        kelime_sayisi = len(aciklama.split())
        if kelime_sayisi < 5:
            raise ValidationError(f"Açıklama çok kısa! En az 5 kelime yazmalısınız. (Şu an: {kelime_sayisi})")
        return aciklama

# --- ADMIN SINIFLARI ---

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name_display', 'role_badge', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Ek Bilgiler', {'fields': ('role', 'telefon', 'adres', 'profil_resmi')}),
    )
    def full_name_display(self, obj): return obj.get_full_name() or '-'
    def role_badge(self, obj):
        colors = {'admin': 'red', 'ogretmen': 'green'}
        return format_html('<span style="background-color:{};color:white;padding:3px 10px;border-radius:3px;">{}</span>',
                           colors.get(obj.role, 'gray'), obj.get_role_display())

@admin.register(Sinif)
class SinifAdmin(admin.ModelAdmin):
    list_display = ['ad', 'ogrenci_sayisi_display', 'aktif_ogrenci_sayisi']
    def ogrenci_sayisi_display(self, obj): return obj.ogrenciler.count()
    def aktif_ogrenci_sayisi(self, obj):
        aktif = obj.ogrenciler.filter(aktif=True).count()
        return format_html('<span style="color:green;font-weight:bold;">{}</span>', aktif)

class OgrenciNotuInline(admin.TabularInline):
    model = OgrenciNotu
    form = OgrenciNotuForm
    extra = 1
    fields = ['kategori', 'baslik', 'aciklama', 'tarih']

@admin.register(Ogrenci)
class OgrenciAdmin(admin.ModelAdmin):
    list_display = ['tam_ad_display', 'tc_kimlik', 'sinif_badge', 'aktif']
    inlines = [OgrenciNotuInline]
    fieldsets = (
        ('Öğrenci Bilgileri', {'fields': ('ad', 'soyad', 'tc_kimlik', 'dogum_tarihi', 'cinsiyet', 'sinif', 'profil_resmi')}),
        ('Veli Bilgileri', {'fields': ('veli_adi', 'veli_telefon', 'adres')}),
        ('Durum', {'fields': ('aktif',)}),
    )
    def tam_ad_display(self, obj): return obj.tam_ad
    def sinif_badge(self, obj):
        return format_html('<span style="background-color:#0d6efd;color:white;padding:3px 8px;border-radius:3px;">{}</span>', obj.sinif.ad)

@admin.register(DersProgrami)
class DersProgramiAdmin(admin.ModelAdmin):
    list_display = ['ders_adi', 'ogretmen', 'sinif', 'gun', 'aktif']
    list_editable = ['aktif']
    # DÜZELTME: fieldsets içindeki isimlerin modeldeki isimlerle tam eşleştiğinden emin olduk
    fieldsets = (
        ('Ders Bilgileri', {
            'fields': ('ders_adi', 'ogretmen', 'sinif')
        }),
        ('Zaman Bilgisi', {
            'fields': ('gun', 'baslangic_saati', 'bitis_saati')
        }),
        ('Durum', {
            'fields': ('aktif',)
        }),
    )

class YoklamaDetayInline(admin.TabularInline):
    model = YoklamaDetay
    extra = 0
    fields = ['ogrenci', 'durum', 'not_durumu']

@admin.register(Yoklama)
class YoklamaAdmin(admin.ModelAdmin):
    form = YoklamaForm # 3 kelime engeli burada devreye girer
    list_display = ['ders_basligi', 'tarih', 'ogretmen', 'sinif']
    inlines = [YoklamaDetayInline]
    
    def save_model(self, request, obj, form, change):
        if not change and obj.ders_programi:
            obj.ogretmen = obj.ders_programi.ogretmen
            obj.sinif = obj.ders_programi.sinif
        super().save_model(request, obj, form, change)

@admin.register(OgrenciNotu)
class OgrenciNotuAdmin(admin.ModelAdmin):
    form = OgrenciNotuForm
    list_display = ['ogrenci', 'kategori', 'baslik', 'tarih']
    def save_model(self, request, obj, form, change):
        if not change: obj.olusturan = request.user
        super().save_model(request, obj, form, change)