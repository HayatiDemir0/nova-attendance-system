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
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Hatalı kullanıcı adı veya şifre!')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    return render(request, 'register.html')

# ==================== DASHBOARD VE TAKVİM ====================

@login_required
def dashboard(request):
    if request.user.role == 'admin': return redirect('yonetim_panel')
    bugun = timezone.now().date()
    gun_index = bugun.isoweekday() 
    bugun_dersler = DersProgrami.objects.filter(ogretmen=request.user, gun__in=[str(gun_index), gun_index], aktif=True).order_by('baslangic_saati')
    bugun_yoklamalar = Yoklama.objects.filter(ogretmen=request.user, tarih=bugun)
    alinan_ders_ids = list(bugun_yoklamalar.values_list('ders_programi_id', flat=True))
    return render(request, 'dashboard.html', {'bugun_dersler': bugun_dersler, 'bugun_yoklamalar': bugun_yoklamalar, 'alinan_ders_ids': alinan_ders_ids, 'bugun': bugun})

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
    return render(request, 'takvim.html', {'takvim': ay_takvimi, 'yoklamalar': yoklamalar_dict, 'ay': ay, 'yil': yil, 'ay_adi': "Ay Görünümü"})

# ==================== ADMİN YÖNETİM SAYFALARI (LİSTELER) ====================

@login_required
def yonetim_panel(request):
    if request.user.role != 'admin': return redirect('dashboard')
    context = {
        'toplam_ogretmen': User.objects.filter(role='ogretmen').count(),
        'toplam_sinif': Sinif.objects.count(),
        'toplam_ogrenci': Ogrenci.objects.filter(aktif=True).count(),
        'son_yoklamalar': Yoklama.objects.all().order_by('-tarih')[:5],
    }
    return render(request, 'yonetim/panel.html', context)

@login_required
def yonetim_yoklamalar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    yoklama_listesi = Yoklama.objects.all().order_by('-tarih', '-id')
    paginator = Paginator(yoklama_listesi, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'yonetim/yoklamalar.html', {'yoklamalar': page_obj, 'ogretmenler': User.objects.filter(role='ogretmen'), 'siniflar': Sinif.objects.all()})

@login_required
def yonetim_ogretmenler(request):
    if request.user.role != 'admin': return redirect('dashboard')
    return render(request, 'yonetim/ogretmenler.html', {'ogretmenler': User.objects.filter(role='ogretmen')})

@login_required
def yonetim_siniflar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    return render(request, 'yonetim/siniflar.html', {'siniflar': Sinif.objects.all()})

@login_required
def yonetim_ogrenciler(request):
    if request.user.role != 'admin': return redirect('dashboard')
    return render(request, 'yonetim/ogrenciler.html', {'ogrenciler': Ogrenci.objects.all(), 'siniflar': Sinif.objects.all()})

@login_required
def yonetim_ders_programi(request):
    if request.user.role != 'admin': return redirect('dashboard')
    return render(request, 'yonetim/ders_programi.html', {'dersler': DersProgrami.objects.all()})

@login_required
def yonetim_ayarlar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    return render(request, 'yonetim/ayarlar.html')

# ==================== EKLEME İŞLEMLERİ (YENİ FONKSİYONLAR) ====================

@login_required
def ogretmen_ekle(request):
    if request.user.role != 'admin': return redirect('dashboard')
    if request.method == 'POST':
        User.objects.create_user(username=request.POST.get('username'), password=request.POST.get('password'), first_name=request.POST.get('first_name'), last_name=request.POST.get('last_name'), role='ogretmen')
        messages.success(request, "Öğretmen eklendi.")
        return redirect('yonetim_ogretmenler')
    return render(request, 'ogretmenler/ekle.html')

@login_required
def sinif_ekle(request):
    if request.user.role != 'admin': return redirect('dashboard')
    if request.method == 'POST':
        Sinif.objects.create(ad=request.POST.get('ad'), aciklama=request.POST.get('aciklama'))
        return redirect('yonetim_siniflar')
    return render(request, 'siniflar/ekle.html')

@login_required
def ogrenci_ekle(request):
    if request.user.role != 'admin': return redirect('dashboard')
    if request.method == 'POST':
        Ogrenci.objects.create(ad=request.POST.get('ad'), soyad=request.POST.get('soyad'), sinif_id=request.POST.get('sinif'), tc_kimlik=request.POST.get('tc_kimlik'))
        return redirect('yonetim_ogrenciler')
    return render(request, 'ogrenciler/ekle.html', {'siniflar': Sinif.objects.all()})

@login_required
def ders_programi_ekle(request):
    if request.user.role != 'admin': return redirect('dashboard')
    if request.method == 'POST':
        DersProgrami.objects.create(ders_adi=request.POST.get('ders_adi'), gun=request.POST.get('gun'), baslangic_saati=request.POST.get('baslangic_saati'), bitis_saati=request.POST.get('bitis_saati'), ogretmen_id=request.POST.get('ogretmen'), sinif_id=request.POST.get('sinif'))
        return redirect('yonetim_ders_programi')
    return render(request, 'ders_programi/ekle.html', {'ogretmenler': User.objects.filter(role='ogretmen'), 'siniflar': Sinif.objects.all()})

# ==================== YOKLAMA VE NOTLAR ====================

@login_required
def yoklama_al(request, ders_id):
    ders = get_object_or_404(DersProgrami, id=ders_id)
    ogrenciler = Ogrenci.objects.filter(sinif=ders.sinif, aktif=True)
    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi', '').strip()
        if len(ders_basligi.split()) != 3:
            messages.error(request, "Ders başlığı tam 3 kelime olmalı!")
            return render(request, 'yoklama/al.html', {'ders': ders, 'ogrenciler': ogrenciler, 'hata_baslik': ders_basligi})
        yoklama = Yoklama.objects.create(ders_programi=ders, ders_basligi=ders_basligi, ogretmen=request.user, sinif=ders.sinif, tarih=timezone.now().date())
        for o in ogrenciler:
            YoklamaDetay.objects.create(yoklama=yoklama, ogrenci=o, durum=request.POST.get(f'durum_{o.id}', 'var'))
        return redirect('dashboard')
    return render(request, 'yoklama/al.html', {'ders': ders, 'ogrenciler': ogrenciler})

@login_required
def yoklama_duzenle(request, pk):
    yoklama = get_object_or_404(Yoklama, pk=pk)
    detaylar = yoklama.detaylar.all()
    if request.method == 'POST':
        yoklama.ders_basligi = request.POST.get('ders_basligi')
        yoklama.save()
        for d in detaylar:
            d.durum = request.POST.get(f'durum_{d.ogrenci.id}')
            d.save()
        return redirect('yonetim_yoklamalar')
    return render(request, 'yoklama/duzenle.html', {'yoklama': yoklama, 'detaylar': detaylar})

@login_required
def yoklama_detay(request, pk):
    yoklama = get_object_or_404(Yoklama, pk=pk)
    return render(request, 'yoklama/detay.html', {'yoklama': yoklama, 'detaylar': yoklama.detaylar.all(), 'istatistik': {'toplam': yoklama.detaylar.count()}})

@login_required
def ogrenci_not_ekle(request, ogrenci_id):
    if request.method == 'POST':
        OgrenciNotu.objects.create(ogrenci_id=ogrenci_id, olusturan=request.user, baslik=request.POST.get('baslik'), aciklama=request.POST.get('aciklama'))
    return redirect('ogrenci_detay', pk=ogrenci_id)

# ==================== SİLME VE REDIRECTLER ====================

@login_required
def ogretmen_sil(request, pk):
    User.objects.filter(pk=pk).delete()
    return redirect('yonetim_ogretmenler')

@login_required
def sinif_sil(request, pk):
    Sinif.objects.filter(pk=pk).delete()
    return redirect('yonetim_siniflar')

@login_required
def ogrenci_sil(request, pk):
    Ogrenci.objects.filter(pk=pk).delete()
    return redirect('yonetim_ogrenciler')

@login_required
def ders_programi_sil(request, pk):
    DersProgrami.objects.filter(pk=pk).delete()
    return redirect('yonetim_ders_programi')

@login_required
def ogrenci_detay(request, pk): return render(request, 'ogrenciler/ogrenci_detay.html', {'ogrenci': get_object_or_404(Ogrenci, pk=pk)})
@login_required
def ogretmen_duzenle(request, pk): return redirect('yonetim_ogretmenler')
@login_required
def sinif_duzenle(request, pk): return redirect('yonetim_siniflar')
@login_required
def ogrenci_duzenle(request, pk): return redirect('yonetim_ogrenciler')
@login_required
def ders_programi_duzenle(request, pk): return redirect('yonetim_ders_programi')
@login_required
def yoklama_gecmis(request): return redirect('dashboard')