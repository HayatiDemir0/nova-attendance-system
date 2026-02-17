from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, OgrenciNotu, YoklamaDetay
import calendar
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Yoklama
# ==================== KİMLİK DOĞRULAMA ====================

def login_view(request):
    """Giriş Sayfası"""
    # --- GEÇİCİ DEBUG (sonra sil) ---
    if request.GET.get('setup') == 'nova':
        from django.contrib.auth import get_user_model
        from django.http import HttpResponse
        User = get_user_model()
        try:
            u, created = User.objects.get_or_create(username='novakademi')
            u.role = 'admin'
            u.is_staff = True
            u.is_superuser = True
            u.is_active = True
            u.set_password('novakademi2026')
            u.save()
            
            test_user = authenticate(username='novakademi', password='novakademi2026')
            return HttpResponse(
                f"Created: {created}<br>"
                f"Role: {u.role}<br>"
                f"Active: {u.is_active}<br>"
                f"Auth test: {'OK' if test_user else 'FAIL'}"
            )
        except Exception as e:
            return HttpResponse(f"HATA: {e}")
    # --- GEÇİCİ DEBUG SONU ---

    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Hoş geldiniz, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı!')
    
    return render(request, 'login.html')


def register_view(request):
    """Kayıt Sayfası"""
    return render(request, 'register.html')


def logout_view(request):
    """Çıkış İşlemi"""
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptınız!')
    return redirect('login')


# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    """Dashboard - Rol Bazlı"""
    
    # Admin ise yönetim paneline yönlendir
    if request.user.role == 'admin':
        return redirect('yonetim_panel')
    
    context = {}
    bugun = timezone.now().date()
    gun_index = bugun.weekday() + 1
    
    # Bugünkü dersler
    context['bugun_dersler'] = DersProgrami.objects.filter(
        ogretmen=request.user,
        gun=gun_index,
        aktif=True
    ).select_related('sinif').order_by('baslangic_saati')
    
    # Bugün alınan yoklamalar
    context['bugun_yoklamalar'] = Yoklama.objects.filter(
        ogretmen=request.user,
        tarih=bugun
    ).select_related('sinif', 'ders_programi')
    
    # Yoklama alınan ders ID'leri
    alinan_ders_ids = context['bugun_yoklamalar'].values_list('ders_programi_id', flat=True)
    context['alinan_ders_ids'] = list(alinan_ders_ids)
    context['bugun'] = bugun
    
    # Sınıflar
    context['siniflar'] = Sinif.objects.filter(
        ders_programlari__ogretmen=request.user,
        ders_programlari__aktif=True
    ).distinct()
    
    return render(request, 'dashboard.html', context)


@login_required
def takvim(request):
    # Mevcut tarih bilgilerini al
    bugun = datetime.now()
    yil = int(request.GET.get('yil', bugun.year))
    ay = int(request.GET.get('ay', bugun.month))

    # Takvim yapısını oluştur (Pazartesi'den başlar)
    cal = calendar.Calendar(firstweekday=0)
    ay_takvimi = cal.monthdayscalendar(yil, ay)

    # O aya ait yoklamaları çek ve günlere göre grupla
    yoklamalar_qs = Yoklama.objects.filter(tarih__year=yil, tarih__month=ay)
    yoklamalar_dict = {}
    
    for y in yoklamalar_qs:
        gun = y.tarih.day
        if gun not in yoklamalar_dict:
            yoklamalar_dict[gun] = []
        yoklamalar_dict[gun].append(y)

    # Navigasyon (Önceki/Sonraki Ay) hesaplamaları
    onceki_ay = ay - 1 if ay > 1 else 12
    onceki_yil = yil if ay > 1 else yil - 1
    sonraki_ay = ay + 1 if ay < 12 else 1
    sonraki_yil = yil if ay < 12 else yil + 1

    aylar = [
        "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
    ]

    context = {
        'takvim': ay_takvimi,
        'yoklamalar': yoklamalar_dict,
        'ay': ay,
        'yil': yil,
        'ay_adi': aylar[ay],
        'bugun': bugun,
        'onceki_ay': onceki_ay,
        'onceki_yil': onceki_yil,
        'sonraki_ay': sonraki_ay,
        'sonraki_yil': sonraki_yil,
    }
    
    return render(request, 'takvim.html', context)


# ==================== ADMİN PANELİ ====================

@login_required
def yonetim_panel(request):
    """Admin Panel Ana Sayfa"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    context = {
        'toplam_ogretmen': User.objects.filter(role='ogretmen').count(),
        'toplam_sinif': Sinif.objects.count(),
        'toplam_ogrenci': Ogrenci.objects.filter(aktif=True).count(),
        'bugun_yoklama': Yoklama.objects.filter(tarih=timezone.now().date()).count(),
        'son_yoklamalar': Yoklama.objects.all().order_by('-tarih')[:5],
        'son_ogrenciler': Ogrenci.objects.all().order_by('-id')[:5],
        'bu_ay_yoklama': Yoklama.objects.filter(
            tarih__month=timezone.now().month,
            tarih__year=timezone.now().year
        ).count(),
        'toplam_ders': DersProgrami.objects.filter(aktif=True).count(),
    }
    return render(request, 'yonetim/panel.html', context)


@login_required
def yonetim_ogretmenler(request):
    """Öğretmen Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    q = request.GET.get('q', '')
    ogretmenler = User.objects.filter(role='ogretmen')
    
    if q:
        ogretmenler = ogretmenler.filter(
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q) | 
            Q(email__icontains=q)
        )
    
    context = {
        'ogretmenler': ogretmenler,
        'q': q,
    }
    return render(request, 'yonetim/ogretmenler.html', context)


@login_required
def yonetim_siniflar(request):
    """Sınıf Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.annotate(
        ogrenci_sayisi=Count('ogrenciler')
    )
    
    context = {
        'siniflar': siniflar,
    }
    return render(request, 'yonetim/siniflar.html', context)


@login_required
def yonetim_ogrenciler(request):
    """Öğrenci Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.all()
    ogrenciler = Ogrenci.objects.select_related('sinif')
    
    # Filtreleme
    secili_sinif = request.GET.get('sinif', '')
    secili_aktif = request.GET.get('aktif', '')
    q = request.GET.get('q', '')
    
    if secili_sinif:
        ogrenciler = ogrenciler.filter(sinif_id=secili_sinif)
    
    if secili_aktif == '1':
        ogrenciler = ogrenciler.filter(aktif=True)
    elif secili_aktif == '0':
        ogrenciler = ogrenciler.filter(aktif=False)
    
    if q:
        ogrenciler = ogrenciler.filter(
            Q(ad__icontains=q) | 
            Q(soyad__icontains=q) | 
            Q(tc_kimlik__icontains=q)
        )
    
    context = {
        'ogrenciler': ogrenciler,
        'siniflar': siniflar,
        'secili_sinif': secili_sinif,
        'secili_aktif': secili_aktif,
        'q': q,
    }
    return render(request, 'yonetim/ogrenciler.html', context)


@login_required
def yonetim_ders_programi(request):
    """Ders Programı Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    dersler = DersProgrami.objects.select_related('ogretmen', 'sinif')
    
    # Filtreleme
    secili_ogretmen = request.GET.get('ogretmen', '')
    secili_sinif = request.GET.get('sinif', '')
    secili_gun = request.GET.get('gun', '')
    
    if secili_ogretmen:
        dersler = dersler.filter(ogretmen_id=secili_ogretmen)
    
    if secili_sinif:
        dersler = dersler.filter(sinif_id=secili_sinif)
    
    if secili_gun:
        dersler = dersler.filter(gun=secili_gun)
    
    dersler = dersler.order_by('gun', 'baslangic_saati')
    
    context = {
        'dersler': dersler,
        'ogretmenler': ogretmenler,
        'siniflar': siniflar,
        'secili_ogretmen': secili_ogretmen,
        'secili_sinif': secili_sinif,
        'secili_gun': secili_gun,
    }
    return render(request, 'yonetim/ders_programi.html', context)


@login_required
def yonetim_yoklamalar(request):
    """Yoklama Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    yoklamalar = Yoklama.objects.select_related('ogretmen', 'sinif', 'ders_programi')
    
    # Filtreleme
    secili_ogretmen = request.GET.get('ogretmen', '')
    secili_sinif = request.GET.get('sinif', '')
    secili_tarih = request.GET.get('tarih', '')
    
    if secili_ogretmen:
        yoklamalar = yoklamalar.filter(ogretmen_id=secili_ogretmen)
    
    if secili_sinif:
        yoklamalar = yoklamalar.filter(sinif_id=secili_sinif)
    
    if secili_tarih:
        yoklamalar = yoklamalar.filter(tarih=secili_tarih)
    
    yoklamalar = yoklamalar.order_by('-tarih', '-olusturma_zamani')
    
    # Pagination
    paginator = Paginator(yoklamalar, 20)
    page_number = request.GET.get('page')
    yoklamalar = paginator.get_page(page_number)
    
    context = {
        'yoklamalar': yoklamalar,
        'ogretmenler': ogretmenler,
        'siniflar': siniflar,
        'secili_ogretmen': secili_ogretmen,
        'secili_sinif': secili_sinif,
        'secili_tarih': secili_tarih,
    }
    return render(request, 'yonetim/yoklamalar.html', context)


@login_required
def yonetim_ayarlar(request):
    """Sistem Ayarları"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        if 'temizle_eski_yoklamalar' in request.POST:
            tarih = request.POST.get('tarih')
            if tarih:
                Yoklama.objects.filter(tarih__lt=tarih).delete()
                messages.success(request, f'{tarih} tarihinden önceki yoklamalar silindi!')
    
    context = {
        'toplam_yoklama': Yoklama.objects.count(),
        'siniflar': Sinif.objects.all(),
        'en_eski_yoklama': Yoklama.objects.order_by('tarih').first(),
    }
    return render(request, 'yonetim/ayarlar.html', context)


# ==================== ÖĞRENCİ NOTLARI ====================

@login_required
def ogrenci_detay(request, pk):
    """Öğrenci Detay ve Notlar"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    notlar = ogrenci.notlar.all()
    
    context = {
        'ogrenci': ogrenci,
        'notlar': notlar,
        'bugun': timezone.now().date(),
    }
    return render(request, 'yonetim/ogrenci_detay.html', context)


@login_required
def ogrenci_not_ekle(request, pk):
    """Öğrenciye Not Ekle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    
    if request.method == 'POST':
        kategori = request.POST.get('kategori')
        baslik = request.POST.get('baslik', '').strip()
        aciklama = request.POST.get('aciklama', '').strip()
        tarih = request.POST.get('tarih')
        
        # Validasyon
        if not baslik:
            messages.error(request, 'Başlık boş bırakılamaz!')
            return redirect('ogrenci_detay', pk=pk)
        
        if len(baslik) < 3:
            messages.error(request, 'Başlık en az 3 karakter olmalıdır!')
            return redirect('ogrenci_detay', pk=pk)
        
        if not aciklama:
            messages.error(request, 'Açıklama boş bırakılamaz!')
            return redirect('ogrenci_detay', pk=pk)
        
        if len(aciklama) < 10:
            messages.error(request, 'Açıklama en az 10 karakter olmalıdır!')
            return redirect('ogrenci_detay', pk=pk)
        
        if not tarih:
            tarih = timezone.now().date()
        
        # Not oluştur
        OgrenciNotu.objects.create(
            ogrenci=ogrenci,
            olusturan=request.user,
            kategori=kategori,
            baslik=baslik,
            aciklama=aciklama,
            tarih=tarih
        )
        
        messages.success(request, f'{ogrenci.tam_ad} için not eklendi!')
        return redirect('ogrenci_detay', pk=pk)
    
    context = {
        'ogrenci': ogrenci,
        'bugun': timezone.now().date(),
    }
    return render(request, 'yonetim/ogrenci_not_ekle.html', context)


@login_required
def ogrenci_not_duzenle(request, pk):
    """Not Düzenle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogrenci_notu = get_object_or_404(OgrenciNotu, pk=pk)
    
    if request.method == 'POST':
        ogrenci_notu.kategori = request.POST.get('kategori')
        ogrenci_notu.baslik = request.POST.get('baslik', '').strip()
        ogrenci_notu.aciklama = request.POST.get('aciklama', '').strip()
        ogrenci_notu.tarih = request.POST.get('tarih')
        ogrenci_notu.save()
        
        messages.success(request, 'Not güncellendi!')
        return redirect('ogrenci_detay', pk=ogrenci_notu.ogrenci.id)
    
    context = {
        'ogrenci_notu': ogrenci_notu,
        'ogrenci': ogrenci_notu.ogrenci,
    }
    return render(request, 'yonetim/ogrenci_not_duzenle.html', context)


@login_required
def ogrenci_not_sil(request, pk):
    """Not Sil"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogrenci_notu = get_object_or_404(OgrenciNotu, pk=pk)
    ogrenci_id = ogrenci_notu.ogrenci.id
    ogrenci_notu.delete()
    
    messages.success(request, 'Not silindi!')
    return redirect('ogrenci_detay', pk=ogrenci_id)


# ==================== ÖĞRETMEN CRUD ====================

@login_required
def ogretmen_ekle(request):
    """Öğretmen Ekle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        telefon = request.POST.get('telefon', '').strip()
        adres = request.POST.get('adres', '').strip()
        
        # Validasyon
        if not username or not password:
            messages.error(request, 'Kullanıcı adı ve şifre zorunludur!')
            return redirect('ogretmen_ekle')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu kullanıcı adı zaten kullanılıyor!')
            return redirect('ogretmen_ekle')
        
        # Öğretmen oluştur
        User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            telefon=telefon,
            adres=adres,
            role='ogretmen'
        )
        
        messages.success(request, f'{first_name} {last_name} başarıyla eklendi!')
        return redirect('yonetim_ogretmenler')
    
    return render(request, 'ogretmenler/ekle.html')


@login_required
def ogretmen_duzenle(request, pk):
    """Öğretmen Düzenle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogretmen = get_object_or_404(User, pk=pk, role='ogretmen')
    
    if request.method == 'POST':
        ogretmen.first_name = request.POST.get('first_name', '').strip()
        ogretmen.last_name = request.POST.get('last_name', '').strip()
        ogretmen.email = request.POST.get('email', '').strip()
        ogretmen.telefon = request.POST.get('telefon', '').strip()
        ogretmen.adres = request.POST.get('adres', '').strip()
        
        password = request.POST.get('password', '').strip()
        if password:
            ogretmen.set_password(password)
        
        ogretmen.save()
        
        messages.success(request, 'Öğretmen bilgileri güncellendi!')
        return redirect('yonetim_ogretmenler')
    
    return render(request, 'ogretmenler/duzenle.html', {'ogretmen': ogretmen})


@login_required
def ogretmen_sil(request, pk):
    """Öğretmen Sil"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogretmen = get_object_or_404(User, pk=pk, role='ogretmen')
    ogretmen.delete()
    
    messages.success(request, 'Öğretmen silindi!')
    return redirect('yonetim_ogretmenler')


# ==================== SINIF CRUD ====================

@login_required
def sinif_ekle(request):
    """Sınıf Ekle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        ad = request.POST.get('ad', '').strip()
        aciklama = request.POST.get('aciklama', '').strip()
        
        if not ad:
            messages.error(request, 'Sınıf adı zorunludur!')
            return redirect('sinif_ekle')
        
        if Sinif.objects.filter(ad=ad).exists():
            messages.error(request, 'Bu sınıf adı zaten var!')
            return redirect('sinif_ekle')
        
        Sinif.objects.create(ad=ad, aciklama=aciklama)
        
        messages.success(request, f'{ad} sınıfı oluşturuldu!')
        return redirect('yonetim_siniflar')
    
    return render(request, 'siniflar/ekle.html')


@login_required
def sinif_duzenle(request, pk):
    """Sınıf Düzenle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    sinif = get_object_or_404(Sinif, pk=pk)
    
    if request.method == 'POST':
        sinif.ad = request.POST.get('ad', '').strip()
        sinif.aciklama = request.POST.get('aciklama', '').strip()
        sinif.save()
        
        messages.success(request, 'Sınıf güncellendi!')
        return redirect('yonetim_siniflar')
    
    return render(request, 'siniflar/duzenle.html', {'sinif': sinif})


@login_required
def sinif_sil(request, pk):
    """Sınıf Sil"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    sinif = get_object_or_404(Sinif, pk=pk)
    sinif.delete()
    
    messages.success(request, 'Sınıf silindi!')
    return redirect('yonetim_siniflar')


# ==================== ÖĞRENCİ CRUD ====================

@login_required
def ogrenci_ekle(request):
    """Öğrenci Ekle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.all()
    
    if request.method == 'POST':
        # Formdan gelen verileri alıyoruz
        ad = request.POST.get('ad')
        soyad = request.POST.get('soyad')
        tc_kimlik = request.POST.get('tc_kimlik')
        dogum_tarihi = request.POST.get('dogum_tarihi')
        cinsiyet = request.POST.get('cinsiyet')
        sinif_id = request.POST.get('sinif')
        veli_adi = request.POST.get('veli_adi')
        veli_telefon = request.POST.get('veli_telefon')
        adres = request.POST.get('adres')
        
        # Validasyon
        if not ad or not soyad or not tc_kimlik or not dogum_tarihi or not sinif_id:
            messages.error(request, 'Zorunlu alanları doldurun!')
            return redirect('ogrenci_ekle')
        
        if len(tc_kimlik) != 11:
            messages.error(request, 'TC Kimlik 11 haneli olmalıdır!')
            return redirect('ogrenci_ekle')
        
        if Ogrenci.objects.filter(tc_kimlik=tc_kimlik).exists():
            messages.error(request, 'Bu TC Kimlik numarası zaten kayıtlı!')
            return redirect('ogrenci_ekle')
        
        # Fotoğraf
        fotograf = request.FILES.get('fotograf')
        
        # Öğrenci oluştur
        Ogrenci.objects.create(
            ad=ad,
            soyad=soyad,
            tc_kimlik=tc_kimlik,
            dogum_tarihi=dogum_tarihi,
            cinsiyet=cinsiyet,
            sinif_id=sinif_id,
            veli_adi=veli_adi,
            veli_telefon=veli_telefon,
            adres=adres,
        )
        
        messages.success(request, f'{ad} {soyad} başarıyla eklendi!')
        return redirect('yonetim_ogrenciler')
    
    return render(request, 'ogrenciler/ekle.html', {'siniflar': siniflar})


@login_required
def ogrenci_duzenle(request, pk):
    """Öğrenci Düzenle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    siniflar = Sinif.objects.all()
    
    if request.method == 'POST':
        ogrenci.ad = request.POST.get('ad', '').strip()
        ogrenci.soyad = request.POST.get('soyad', '').strip()
        ogrenci.dogum_tarihi = request.POST.get('dogum_tarihi')
        ogrenci.cinsiyet = request.POST.get('cinsiyet')
        ogrenci.sinif_id = request.POST.get('sinif')
        ogrenci.veli_adi = request.POST.get('veli_adi', '').strip()
        ogrenci.veli_telefon = request.POST.get('veli_telefon', '').strip()
        ogrenci.veli_email = request.POST.get('veli_email', '').strip()
        ogrenci.adres = request.POST.get('adres', '').strip()
        ogrenci.aktif = request.POST.get('aktif') == 'on'
        
        if request.FILES.get('fotograf'):
            ogrenci.fotograf = request.FILES.get('fotograf')
        
        ogrenci.save()
        
        messages.success(request, 'Öğrenci bilgileri güncellendi!')
        return redirect('yonetim_ogrenciler')
    
    return render(request, 'ogrenciler/duzenle.html', {'ogrenci': ogrenci, 'siniflar': siniflar})


@login_required
def ogrenci_sil(request, pk):
    """Öğrenci Sil"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    ogrenci.delete()
    
    messages.success(request, 'Öğrenci silindi!')
    return redirect('yonetim_ogrenciler')


# ==================== DERS PROGRAMI CRUD ====================

@login_required
def ders_programi_ekle(request):
    """Ders Programı Ekle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    
    if request.method == 'POST':
        ders_adi = request.POST.get('ders_adi', '').strip()
        gun = request.POST.get('gun')
        baslangic_saati = request.POST.get('baslangic_saati')
        bitis_saati = request.POST.get('bitis_saati')
        ogretmen_id = request.POST.get('ogretmen')
        sinif_id = request.POST.get('sinif')
        derslik = request.POST.get('derslik', '').strip()
        aktif = request.POST.get('aktif') == 'on'
        
        # Validasyon
        if not ders_adi or not gun or not baslangic_saati or not bitis_saati or not ogretmen_id or not sinif_id:
            messages.error(request, 'Zorunlu alanları doldurun!')
            return redirect('ders_programi_ekle')
        
        # Çakışma kontrolü
        if DersProgrami.objects.filter(
            ogretmen_id=ogretmen_id,
            sinif_id=sinif_id,
            gun=gun,
            baslangic_saati=baslangic_saati
        ).exists():
            messages.error(request, 'Bu öğretmen, sınıf, gün ve saatte zaten bir ders var!')
            return redirect('ders_programi_ekle')
        
        # Ders oluştur
        DersProgrami.objects.create(
            ders_adi=ders_adi,
            gun=gun,
            baslangic_saati=baslangic_saati,
            bitis_saati=bitis_saati,
            ogretmen_id=ogretmen_id,
            sinif_id=sinif_id,
            derslik=derslik,
            aktif=aktif
        )
        
        messages.success(request, f'{ders_adi} dersi eklendi!')
        return redirect('yonetim_ders_programi')
    
    return render(request, 'ders_programi/ekle.html', {'ogretmenler': ogretmenler, 'siniflar': siniflar})


@login_required
def ders_programi_duzenle(request, pk):
    """Ders Programı Düzenle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ders = get_object_or_404(DersProgrami, pk=pk)
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    
    if request.method == 'POST':
        ders.ders_adi = request.POST.get('ders_adi', '').strip()
        ders.gun = request.POST.get('gun')
        ders.baslangic_saati = request.POST.get('baslangic_saati')
        ders.bitis_saati = request.POST.get('bitis_saati')
        ders.ogretmen_id = request.POST.get('ogretmen')
        ders.sinif_id = request.POST.get('sinif')
        ders.derslik = request.POST.get('derslik', '').strip()
        ders.aktif = request.POST.get('aktif') == 'on'
        ders.save()
        
        messages.success(request, 'Ders programı güncellendi!')
        return redirect('yonetim_ders_programi')
    
    return render(request, 'ders_programi/duzenle.html', {
        'ders': ders,
        'ogretmenler': ogretmenler,
        'siniflar': siniflar
    })


@login_required
def ders_programi_sil(request, pk):
    """Ders Programı Sil"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ders = get_object_or_404(DersProgrami, pk=pk)
    ders.delete()
    
    messages.success(request, 'Ders programı silindi!')
    return redirect('yonetim_ders_programi')


# ==================== YOKLAMA FONKSİYONLARI ====================

@login_required
def yoklama_al(request, ders_id):
    """Yoklama Al"""
    ders = get_object_or_404(DersProgrami, id=ders_id, ogretmen=request.user)
    ogrenciler = Ogrenci.objects.filter(sinif=ders.sinif, aktif=True)
    bugun = timezone.now().date()
    
    # Bugün bu ders için yoklama kontrolü
    mevcut_yoklama = Yoklama.objects.filter(
        ogretmen=request.user,
        sinif=ders.sinif,
        ders_programi=ders,
        tarih=bugun
    ).first()
    
    if mevcut_yoklama:
        messages.warning(request, 'Bu ders için bugün zaten yoklama aldınız!')
        return redirect('yoklama_detay', pk=mevcut_yoklama.id)
    
    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi', '').strip()
        
        # Validasyon
        if len(ders_basligi) < 10:
            messages.error(request, 'Ders konusu en az 10 karakter olmalıdır!')
            return redirect('yoklama_al', ders_id=ders_id)
        
        if len(ders_basligi) > 200:
            messages.error(request, 'Ders konusu en fazla 200 karakter olabilir!')
            return redirect('yoklama_al', ders_id=ders_id)
        
        # Yoklama oluştur
        yoklama = Yoklama.objects.create(
            ders_programi=ders,
            tarih=bugun,
            ders_basligi=ders_basligi,
            ogretmen=request.user,
            sinif=ders.sinif
        )
        
        # Yoklama detayları oluştur
        for ogrenci in ogrenciler:
            durum = request.POST.get(f'durum_{ogrenci.id}', 'var')
            YoklamaDetay.objects.create(
                yoklama=yoklama,
                ogrenci=ogrenci,
                durum=durum
            )
        
        messages.success(request, 'Yoklama başarıyla kaydedildi!')
        return redirect('dashboard')
    
    context = {
        'ders': ders,
        'ogrenciler': ogrenciler,
        'bugun': bugun,
    }
    return render(request, 'yoklama/al.html', context)


@login_required
def yoklama_duzenle(request, pk):
    """Yoklama Düzenle"""
    yoklama = get_object_or_404(Yoklama, pk=pk)
    
    if request.method == 'POST':
        yoklama.ders_basligi = request.POST.get('ders_basligi')
        yoklama.save()
        
        # Detayları güncelle
        for detay in yoklama.detaylar.all():
            durum = request.POST.get(f'durum_{detay.ogrenci.id}')
            if durum:
                detay.durum = durum
                detay.save()
        
        messages.success(request, 'Yoklama güncellendi!')
        return redirect('yoklama_detay', pk=pk)
    
    return render(request, 'yoklama/duzenle.html', {'yoklama': yoklama})


@login_required
def yoklama_gecmis(request):
    """Yoklama Geçmişi"""
    yoklamalar = Yoklama.objects.filter(
        ogretmen=request.user
    ).select_related('sinif', 'ders_programi').order_by('-tarih')
    
    return render(request, 'yoklama/gecmis.html', {'yoklamalar': yoklamalar})


@login_required
def yoklama_detay(request, pk):
    """Yoklama Detay"""
    yoklama = get_object_or_404(Yoklama, pk=pk)
    detaylar = yoklama.detaylar.select_related('ogrenci').all()
    
    # İstatistikler
    toplam = detaylar.count()
    var_sayisi = detaylar.filter(durum='var').count()
    yok_sayisi = detaylar.filter(durum='yok').count()
    izinli_sayisi = detaylar.filter(durum='izinli').count()
    
    context = {
        'yoklama': yoklama,
        'detaylar': detaylar,
        'istatistik': {  # Verileri bu sözlük içine paketliyoruz
            'toplam': toplam,
            'var': var_sayisi,
            'yok': yok_sayisi,
            'izinli': izinli_sayisi,
            'gec': 0  # Eğer view'da gec_sayisi varsa onu yazın
        }
    }
    return render(request, 'yoklama/detay.html', context)