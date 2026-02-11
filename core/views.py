from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama
from django.db.models import Q, Count

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