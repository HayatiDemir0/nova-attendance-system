from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
import calendar
from datetime import datetime
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, OgrenciNotu, YoklamaDetay

# ==================== KİMLİK DOĞRULAMA ====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Hoş geldiniz!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı!')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptınız!')
    return redirect('login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'register.html')

# ==================== DASHBOARD VE TAKVİM ====================

@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return redirect('yonetim_panel')
    
    bugun = timezone.now().date()
    gun_index = bugun.isoweekday() 
    
    bugun_dersler = DersProgrami.objects.filter(
        ogretmen=request.user, gun__in=[str(gun_index), gun_index], aktif=True
    ).select_related('sinif').order_by('baslangic_saati')
    
    bugun_yoklamalar = Yoklama.objects.filter(ogretmen=request.user, tarih=bugun)
    alinan_ders_ids = list(bugun_yoklamalar.values_list('ders_programi_id', flat=True))
    
    return render(request, 'dashboard.html', {
        'bugun_dersler': bugun_dersler,
        'bugun_yoklamalar': bugun_yoklamalar,
        'alinan_ders_ids': alinan_ders_ids,
        'bugun': bugun
    })

@login_required
def takvim(request):
    bugun = timezone.now().date()
    yil = int(request.GET.get('yil', bugun.year))
    ay = int(request.GET.get('ay', bugun.month))
    cal = calendar.Calendar(firstweekday=0)
    ay_takvimi = cal.monthdayscalendar(yil, ay)
    yoklamalar = Yoklama.objects.filter(tarih__year=yil, tarih__month=ay)
    
    yoklamalar_dict = {}
    for y in yoklamalar:
        gun = y.tarih.day
        if gun not in yoklamalar_dict: yoklamalar_dict[gun] = []
        yoklamalar_dict[gun].append(y)

    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    return render(request, 'takvim.html', {
        'takvim': ay_takvimi, 'yoklamalar': yoklamalar_dict, 'ay': ay, 'yil': yil, 'ay_adi': aylar[ay-1]
    })

# ==================== ADMİN YÖNETİM SAYFALARI ====================

@login_required
def yonetim_panel(request):
    if request.user.role != 'admin': return redirect('dashboard')
    context = {
        'toplam_ogretmen': User.objects.filter(role='ogretmen').count(),
        'toplam_sinif': Sinif.objects.count(),
        'toplam_ogrenci': Ogrenci.objects.filter(aktif=True).count(),
        'bugun_yoklama': Yoklama.objects.filter(tarih=timezone.now().date()).count(),
        'son_yoklamalar': Yoklama.objects.all().order_by('-tarih')[:5],
    }
    return render(request, 'yonetim/panel.html', context)

@login_required
def yonetim_yoklamalar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    yoklamalar_list = Yoklama.objects.select_related('ogretmen', 'sinif').order_by('-tarih', '-id')
    
    paginator = Paginator(yoklamalar_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'yonetim/yoklamalar.html', {
        'yoklamalar': page_obj,
        'ogretmenler': User.objects.filter(role='ogretmen'),
        'siniflar': Sinif.objects.all()
    })

@login_required
def yonetim_ogretmenler(request):
    if request.user.role != 'admin': return redirect('dashboard')
    ogretmenler = User.objects.filter(role='ogretmen')
    return render(request, 'yonetim/ogretmenler.html', {'ogretmenler': ogretmenler})

@login_required
def yonetim_siniflar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    siniflar = Sinif.objects.annotate(ogrenci_sayisi=Count('ogrenciler'))
    return render(request, 'yonetim/siniflar.html', {'siniflar': siniflar})

@login_required
def yonetim_ogrenciler(request):
    if request.user.role != 'admin': return redirect('dashboard')
    ogrenciler = Ogrenci.objects.select_related('sinif').all()
    return render(request, 'yonetim/ogrenciler.html', {'ogrenciler': ogrenciler})

@login_required
def yonetim_ders_programi(request):
    if request.user.role != 'admin': return redirect('dashboard')
    dersler = DersProgrami.objects.select_related('ogretmen', 'sinif').all()
    return render(request, 'yonetim/ders_programi.html', {'dersler': dersler})

@login_required
def yonetim_ayarlar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    return render(request, 'yonetim/ayarlar.html', {'toplam_yoklama': Yoklama.objects.count()})

# ==================== YOKLAMA İŞLEMLERİ (3 KELİME KURALI) ====================

@login_required
def yoklama_al(request, ders_id):
    ders = get_object_or_404(DersProgrami, id=ders_id)
    ogrenciler = Ogrenci.objects.filter(sinif=ders.sinif, aktif=True)
    
    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi', '').strip()
        if len(ders_basligi.split()) != 3:
            messages.error(request, "Ders konusu tam 3 kelime olmalı!")
            return render(request, 'yoklama/al.html', {'ders': ders, 'ogrenciler': ogrenciler, 'hata_baslik': ders_basligi})

        yoklama = Yoklama.objects.create(
            ders_programi=ders, ders_basligi=ders_basligi,
            ogretmen=request.user, sinif=ders.sinif, tarih=timezone.now().date()
        )
        for ogrenci in ogrenciler:
            durum = request.POST.get(f'durum_{ogrenci.id}', 'var')
            YoklamaDetay.objects.create(yoklama=yoklama, ogrenci=ogrenci, durum=durum)
        
        messages.success(request, 'Yoklama kaydedildi.')
        return redirect('dashboard')
    return render(request, 'yoklama/al.html', {'ders': ders, 'ogrenciler': ogrenciler})

@login_required
def yoklama_duzenle(request, pk):
    yoklama = get_object_or_404(Yoklama, pk=pk)
    if request.user.role != 'admin' and yoklama.ogretmen != request.user:
        return redirect('dashboard')

    detaylar = yoklama.detaylar.all().select_related('ogrenci')
    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi', '').strip()
        if len(ders_basligi.split()) != 3:
            messages.error(request, "Ders konusu tam 3 kelime olmalı!")
            return render(request, 'yoklama/duzenle.html', {'yoklama': yoklama, 'detaylar': detaylar})

        yoklama.ders_basligi = ders_basligi
        yoklama.save()
        for detay in detaylar:
            detay.durum = request.POST.get(f'durum_{detay.ogrenci.id}')
            detay.save()
        messages.success(request, "Yoklama güncellendi.")
        return redirect('yonetim_yoklamalar')
    return render(request, 'yoklama/duzenle.html', {'yoklama': yoklama, 'detaylar': detaylar})

@login_required
def yoklama_detay(request, pk):
    yoklama = get_object_or_404(Yoklama, pk=pk)
    detaylar = yoklama.detaylar.all()
    istatistik = {'toplam': detaylar.count(), 'var': detaylar.filter(durum='var').count()}
    return render(request, 'yoklama/detay.html', {'yoklama': yoklama, 'detaylar': detaylar, 'istatistik': istatistik})

# ==================== SİLME İŞLEMLERİ ====================

@login_required
def ogretmen_sil(request, pk):
    if request.user.role == 'admin': User.objects.filter(pk=pk).delete()
    return redirect('yonetim_ogretmenler')

@login_required
def sinif_sil(request, pk):
    if request.user.role == 'admin': Sinif.objects.filter(pk=pk).delete()
    return redirect('yonetim_siniflar')

@login_required
def ogrenci_sil(request, pk):
    if request.user.role == 'admin': Ogrenci.objects.filter(pk=pk).delete()
    return redirect('yonetim_ogrenciler')

@login_required
def ders_programi_sil(request, pk):
    if request.user.role == 'admin': DersProgrami.objects.filter(pk=pk).delete()
    return redirect('yonetim_ders_programi')

# ==================== DÜZENLEME REDIRECT'LERİ (BOŞ KALMAMASI İÇİN) ====================
@login_required
def ogretmen_duzenle(request, pk): return redirect('yonetim_ogretmenler')
@login_required
def sinif_duzenle(request, pk): return redirect('yonetim_siniflar')
@login_required
def ogrenci_duzenle(request, pk): return redirect('yonetim_ogrenciler')
@login_required
def ders_programi_duzenle(request, pk): return redirect('yonetim_ders_programi')
@login_required
def ogrenci_detay(request, pk): return render(request, 'ogrenciler/ogrenci_detay.html', {'ogrenci': get_object_or_404(Ogrenci, pk=pk)})