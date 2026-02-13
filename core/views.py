from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, OgrenciNotu

# ==================== GENEL VE KİMLİK DOĞRULAMA ====================

def login_view(request):
    """Giriş Sayfası"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    # Buraya giriş mantığını veya formunu eklemelisin
    return render(request, 'registration/login.html')

def register_view(request):
    """Kayıt Sayfası"""
    return render(request, 'registration/register.html')

def logout_view(request):
    """Çıkış İşlemi"""
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    """Genel Dashboard"""
    if request.user.role == 'admin':
        return redirect('yonetim_panel')
    return render(request, 'dashboard.html')

@login_required
def takvim(request):
    """Takvim Görünümü"""
    return render(request, 'takvim.html')

# ==================== ADMİN PANELİ ====================

@login_required
def yonetim_panel(request):
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
    if request.user.role != 'admin':
        return redirect('dashboard')
    q = request.GET.get('q', '')
    ogretmenler = User.objects.filter(role='ogretmen')
    if q:
        ogretmenler = ogretmenler.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
    return render(request, 'yonetim/ogretmenler.html', {'ogretmenler': ogretmenler, 'q': q})

@login_required
def yonetim_siniflar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    siniflar = Sinif.objects.annotate(ogrenci_sayisi=Count('ogrenciler'))
    return render(request, 'yonetim/siniflar.html', {'siniflar': siniflar})

@login_required
def yonetim_ogrenciler(request):
    if request.user.role != 'admin': return redirect('dashboard')
    ogrenciler = Ogrenci.objects.select_related('sinif')
    # ... (Filtreleme mantığı buraya gelecek)
    return render(request, 'yonetim/ogrenciler.html', {'ogrenciler': ogrenciler})

# --- CRUD ÖĞRETMEN ---
@login_required
def ogretmen_listesi(request): return render(request, 'ogretmenler/liste.html')
@login_required
def ogretmen_ekle(request): return render(request, 'ogretmenler/ekle.html')
@login_required
def ogretmen_duzenle(request, pk): return render(request, 'ogretmenler/duzenle.html')
@login_required
def ogretmen_sil(request, pk): return redirect('ogretmen_listesi')

# --- CRUD SINIF ---
@login_required
def sinif_listesi(request): return render(request, 'siniflar/liste.html')
@login_required
def sinif_ekle(request): return render(request, 'siniflar/ekle.html')
@login_required
def sinif_duzenle(request, pk): return render(request, 'siniflar/duzenle.html')
@login_required
def sinif_sil(request, pk): return redirect('sinif_listesi')

# --- ÖĞRENCİ VE NOTLAR ---
@login_required
def ogrenci_listesi(request): return render(request, 'ogrenciler/liste.html')
@login_required
def ogrenci_ekle(request): return render(request, 'ogrenciler/ekle.html')
@login_required
def ogrenci_duzenle(request, pk): return render(request, 'ogrenciler/duzenle.html')
@login_required
def ogrenci_sil(request, pk): return redirect('ogrenci_listesi')

@login_required
def ogrenci_detay(request, pk):
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    return render(request, 'yonetim/ogrenci_detay.html', {'ogrenci': ogrenci, 'notlar': ogrenci.notlar.all()})

@login_required
def ogrenci_not_ekle(request, pk):
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    if request.method == 'POST':
        # Form işlemleri...
        pass
    return render(request, 'yonetim/ogrenci_not_ekle.html', {'ogrenci': ogrenci})

@login_required
def ogrenci_not_duzenle(request, pk):
    ogrenci_notu = get_object_or_404(OgrenciNotu, pk=pk)
    return render(request, 'yonetim/ogrenci_not_duzenle.html', {'ogrenci_notu': ogrenci_notu})

@login_required
def ogrenci_not_sil(request, pk):
    ogrenci_notu = get_object_or_404(OgrenciNotu, pk=pk)
    oid = ogrenci_notu.ogrenci.id
    ogrenci_notu.delete()
    return redirect('ogrenci_detay', pk=oid)

# --- YOKLAMA VE DERS PROGRAMI ---
@login_required
def yonetim_ders_programi(request): return render(request, 'yonetim/ders_programi.html')
@login_required
def yonetim_yoklamalar(request): return render(request, 'yonetim/yoklamalar.html')
@login_required
def yonetim_ayarlar(request): return render(request, 'yonetim/ayarlar.html')

@login_required
def ders_programi_listesi(request): return render(request, 'ders/liste.html')
@login_required
def ders_programi_ekle(request): return render(request, 'ders/ekle.html')
@login_required
def ders_programi_duzenle(request, pk): return render(request, 'ders/duzenle.html')
@login_required
def ders_programi_sil(request, pk): return redirect('ders_programi_listesi')

@login_required
def yoklama_al(request, ders_id): return render(request, 'yoklama/al.html')
@login_required
def yoklama_duzenle(request, pk): return render(request, 'yoklama/duzenle.html')
@login_required
def yoklama_gecmis(request): return render(request, 'yoklama/gecmis.html')
@login_required
def yoklama_detay(request, pk): return render(request, 'yoklama/detay.html')