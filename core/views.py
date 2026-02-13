from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, OgrenciNotu, YoklamaDetay

# ==================== GENEL VE KİMLİK DOĞRULAMA ====================

def login_view(request):
    """Giriş Sayfası"""
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
    
    # Sınıflar
    context['siniflar'] = Sinif.objects.filter(
        ders_programlari__ogretmen=request.user,
        ders_programlari__aktif=True
    ).distinct()
    
    return render(request, 'dashboard.html', context)


@login_required
def takvim(request):
    """Takvim Görünümü"""
    return render(request, 'takvim.html')


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
    
    from django.core.paginator import Paginator
    
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
            return redirect('ogrenci_not_ekle', pk=pk)
        
        if len(baslik) < 3:
            messages.error(request, 'Başlık en az 3 karakter olmalıdır!')
            return redirect('ogrenci_not_ekle', pk=pk)
        
        if not aciklama:
            messages.error(request, 'Açıklama boş bırakılamaz!')
            return redirect('ogrenci_not_ekle', pk=pk)
        
        if len(aciklama) < 10:
            messages.error(request, 'Açıklama en az 10 karakter olmalıdır!')
            return redirect('ogrenci_not_ekle', pk=pk)
        
        if not tarih:
            messages.error(request, 'Tarih seçilmelidir!')
            return redirect('ogrenci_not_ekle', pk=pk)
        
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


# ==================== BOŞLUK CRUD FONKSİYONLARI ====================
# Bu fonksiyonlar daha sonra doldurulacak

@login_required
def ogretmen_listesi(request): 
    return render(request, 'ogretmenler/liste.html')

@login_required
def ogretmen_ekle(request): 
    return render(request, 'ogretmenler/ekle.html')

@login_required
def ogretmen_duzenle(request, pk): 
    return render(request, 'ogretmenler/duzenle.html')

@login_required
def ogretmen_sil(request, pk): 
    return redirect('ogretmen_listesi')

@login_required
def sinif_listesi(request): 
    return render(request, 'siniflar/liste.html')

@login_required
def sinif_ekle(request): 
    return render(request, 'siniflar/ekle.html')

@login_required
def sinif_duzenle(request, pk): 
    return render(request, 'siniflar/duzenle.html')

@login_required
def sinif_sil(request, pk): 
    return redirect('sinif_listesi')

@login_required
def ogrenci_listesi(request): 
    return render(request, 'ogrenciler/liste.html')

@login_required
def ogrenci_ekle(request): 
    return render(request, 'ogrenciler/ekle.html')

@login_required
def ogrenci_duzenle(request, pk): 
    return render(request, 'ogrenciler/duzenle.html')

@login_required
def ogrenci_sil(request, pk): 
    return redirect('ogrenci_listesi')

@login_required
def ders_programi_listesi(request): 
    return render(request, 'ders/liste.html')

@login_required
def ders_programi_ekle(request): 
    return render(request, 'ders/ekle.html')

@login_required
def ders_programi_duzenle(request, pk): 
    return render(request, 'ders/duzenle.html')

@login_required
def ders_programi_sil(request, pk): 
    return redirect('ders_programi_listesi')

@login_required
def yoklama_al(request, ders_id): 
    return render(request, 'yoklama/al.html')

@login_required
def yoklama_duzenle(request, pk): 
    return render(request, 'yoklama/duzenle.html')

@login_required
def yoklama_gecmis(request): 
    return render(request, 'yoklama/gecmis.html')

@login_required
def yoklama_detay(request, pk): 
    return render(request, 'yoklama/detay.html')