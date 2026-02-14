from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
import calendar
from datetime import datetime
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
    if request.user.role == 'admin':
        return redirect('yonetim_panel')
    
    context = {}
    bugun = timezone.now().date()
    gun_index = bugun.isoweekday() 
    
    context['bugun_dersler'] = DersProgrami.objects.filter(
        ogretmen=request.user,
        gun__in=[str(gun_index), gun_index],
        aktif=True
    ).select_related('sinif').order_by('baslangic_saati')
    
    context['bugun_yoklamalar'] = Yoklama.objects.filter(
        ogretmen=request.user,
        tarih=bugun
    ).select_related('sinif', 'ders_programi')
    
    alinan_ders_ids = context['bugun_yoklamalar'].values_list('ders_programi_id', flat=True)
    context['alinan_ders_ids'] = list(alinan_ders_ids)
    
    context['siniflar'] = Sinif.objects.filter(
        ders_programlari__ogretmen=request.user,
        ders_programlari__aktif=True
    ).distinct()
    
    context['bugun'] = bugun
    return render(request, 'dashboard.html', context)

@login_required
def takvim(request):
    """Gelişmiş Takvim Görünümü"""
    bugun = timezone.now().date()
    yil = int(request.GET.get('yil', bugun.year))
    ay = int(request.GET.get('ay', bugun.month))

    cal = calendar.Calendar(firstweekday=0)
    ay_takvimi = cal.monthdayscalendar(yil, ay)
    
    # .select_related('siniflar') hatası 'sinif' olarak düzeltildi
    yoklamalar_sorgu = Yoklama.objects.filter(
        tarih__year=yil, 
        tarih__month=ay
    ).select_related('sinif')

    yoklamalar_dict = {}
    for y in yoklamalar_sorgu:
        gun = y.tarih.day
        if gun not in yoklamalar_dict:
            yoklamalar_dict[gun] = []
        yoklamalar_dict[gun].append(y)

    onceki_ay = ay - 1 if ay > 1 else 12
    onceki_yil = yil if ay > 1 else yil - 1
    sonraki_ay = ay + 1 if ay < 12 else 1
    sonraki_yil = yil if ay < 12 else yil + 1

    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

    context = {
        'takvim': ay_takvimi,
        'yoklamalar': yoklamalar_dict,
        'ay': ay, 'yil': yil, 'ay_adi': aylar[ay-1],
        'bugun': bugun, 'onceki_ay': onceki_ay, 'onceki_yil': onceki_yil,
        'sonraki_ay': sonraki_ay, 'sonraki_yil': sonraki_yil,
    }
    return render(request, 'takvim.html', context)

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
        'son_ogrenciler': Ogrenci.objects.select_related('sinif').order_by('-id')[:5],
        'bu_ay_yoklama': Yoklama.objects.filter(tarih__month=timezone.now().month, tarih__year=timezone.now().year).count(),
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
        ogretmenler = ogretmenler.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    return render(request, 'yonetim/ogretmenler.html', {'ogretmenler': ogretmenler, 'q': q})

@login_required
def yonetim_siniflar(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    siniflar = Sinif.objects.annotate(ogrenci_sayisi=Count('ogrenciler'))
    return render(request, 'yonetim/siniflar.html', {'siniflar': siniflar})

@login_required
def yonetim_ogrenciler(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    siniflar = Sinif.objects.all()
    ogrenciler = Ogrenci.objects.select_related('sinif')
    
    secili_sinif = request.GET.get('sinif', '')
    secili_aktif = request.GET.get('aktif', '')
    q = request.GET.get('q', '')
    
    if secili_sinif: ogrenciler = ogrenciler.filter(sinif_id=secili_sinif)
    if secili_aktif == '1': ogrenciler = ogrenciler.filter(aktif=True)
    elif secili_aktif == '0': ogrenciler = ogrenciler.filter(aktif=False)
    if q: ogrenciler = ogrenciler.filter(Q(ad__icontains=q) | Q(soyad__icontains=q) | Q(tc_kimlik__icontains=q))
    
    return render(request, 'yonetim/ogrenciler.html', {
        'ogrenciler': ogrenciler, 'siniflar': siniflar, 
        'secili_sinif': secili_sinif, 'secili_aktif': secili_aktif, 'q': q
    })

@login_required
def yonetim_ders_programi(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    dersler = DersProgrami.objects.select_related('ogretmen', 'sinif').order_by('gun', 'baslangic_saati')
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    
    return render(request, 'yonetim/ders_programi.html', {
        'dersler': dersler, 'ogretmenler': ogretmenler, 'siniflar': siniflar
    })

@login_required
def yonetim_yoklamalar(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    yoklamalar = Yoklama.objects.select_related('ogretmen', 'sinif', 'ders_programi').order_by('-tarih')
    return render(request, 'yonetim/yoklamalar.html', {'yoklamalar': yoklamalar})

@login_required
def yonetim_ayarlar(request):
    if request.user.role != 'admin': return redirect('dashboard')
    return render(request, 'yonetim/ayarlar.html', {
        'toplam_yoklama': Yoklama.objects.count(),
        'siniflar': Sinif.objects.all(),
    })

# ==================== ÖĞRENCİ VE SINIF İŞLEMLERİ ====================

@login_required
def ogrenci_ekle(request):
    if request.user.role != 'admin': return redirect('dashboard')
    siniflar = Sinif.objects.all()
    if request.method == 'POST':
        Ogrenci.objects.create(
            ad=request.POST.get('ad'), soyad=request.POST.get('soyad'),
            tc_kimlik=request.POST.get('tc_kimlik'), dogum_tarihi=request.POST.get('dogum_tarihi'),
            cinsiyet=request.POST.get('cinsiyet'), sinif_id=request.POST.get('sinif'),
            veli_adi=request.POST.get('veli_adi'), veli_telefon=request.POST.get('veli_telefon'),
            adres=request.POST.get('adres')
        )
        messages.success(request, 'Öğrenci eklendi!')
        return redirect('yonetim_ogrenciler')
    return render(request, 'ogrenciler/ekle.html', {'siniflar': siniflar})

@login_required
def ogrenci_duzenle(request, pk):
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    siniflar = Sinif.objects.all()
    if request.method == 'POST':
        ogrenci.ad = request.POST.get('ad')
        ogrenci.soyad = request.POST.get('soyad')
        ogrenci.sinif_id = request.POST.get('sinif')
        ogrenci.aktif = request.POST.get('aktif') == 'on'
        ogrenci.save()
        messages.success(request, 'Öğrenci güncellendi!')
        return redirect('yonetim_ogrenciler')
    return render(request, 'ogrenciler/duzenle.html', {'ogrenci': ogrenci, 'siniflar': siniflar})

@login_required
def ogrenci_sil(request, pk):
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    ogrenci.delete()
    return redirect('yonetim_ogrenciler')

@login_required
def ogrenci_detay(request, pk):
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    notlar = ogrenci.notlar.all()
    return render(request, 'ogrenciler/ogrenci_detay.html', {'ogrenci': ogrenci, 'notlar': notlar})

# ==================== YOKLAMA SİSTEMİ (KRİTİK GÜNCELLEME) ====================

@login_required
def yoklama_al(request, ders_id):
    """Öğretmenin sınıf listesini gördüğü ve yoklama aldığı yer"""
    ders = get_object_or_404(DersProgrami, id=ders_id)
    sinif = ders.sinif
    ogrenciler = Ogrenci.objects.filter(sinif=sinif, aktif=True)
    
    if request.method == 'POST':
        yoklama = Yoklama.objects.create(
            ders_programi=ders, tarih=timezone.now().date(),
            ders_basligi=request.POST.get('ders_basligi', ders.ders_adi),
            ogretmen=request.user, sinif=sinif
        )
        for ogrenci in ogrenciler:
            durum = request.POST.get(f'durum_{ogrenci.id}', 'var')
            YoklamaDetay.objects.create(yoklama=yoklama, ogrenci=ogrenci, durum=durum)
        
        messages.success(request, 'Yoklama kaydedildi!')
        return redirect('dashboard')

    return render(request, 'yoklama/al.html', {'ders': ders, 'ogrenciler': ogrenciler, 'sinif': sinif})

@login_required
def yoklama_detay(request, pk):
    yoklama = get_object_or_404(Yoklama, pk=pk)
    return render(request, 'yoklama/detay.html', {'yoklama': yoklama})

# ==================== ÖĞRENCİ NOTLARI (CRUD) ====================

@login_required
def ogrenci_not_ekle(request, ogrenci_id):
    ogrenci = get_object_or_404(Ogrenci, id=ogrenci_id)
    if request.method == 'POST':
        OgrenciNotu.objects.create(
            ogrenci=ogrenci, olusturan=request.user,
            kategori=request.POST.get('kategori', 'genel'),
            baslik=request.POST.get('baslik'),
            aciklama=request.POST.get('aciklama'),
            tarih=request.POST.get('tarih') or timezone.now().date()
        )
        messages.success(request, 'Not eklendi!')
        return redirect('ogrenci_detay', pk=ogrenci_id)
    return render(request, 'ogrenciler/ogrenci_not_ekle.html', {'ogrenci': ogrenci})

@login_required
def ogrenci_not_duzenle(request, pk):
    not_obj = get_object_or_404(OgrenciNotu, pk=pk)
    if request.method == 'POST':
        not_obj.baslik = request.POST.get('baslik')
        not_obj.aciklama = request.POST.get('aciklama')
        not_obj.save()
        return redirect('ogrenci_detay', pk=not_obj.ogrenci.id)
    return render(request, 'ogrenciler/ogrenci_not_duzenle.html', {'not_obj': not_obj})

@login_required
def ogrenci_not_sil(request, pk):
    not_obj = get_object_or_404(OgrenciNotu, pk=pk)
    oid = not_obj.ogrenci.id
    not_obj.delete()
    return redirect('ogrenci_detay', pk=oid)

# ==================== DİĞER İŞLEMLER ====================
# (Öğretmen ve Sınıf CRUD'ları yukarıdaki mantıkla devam eder...)

@login_required
def ogretmen_ekle(request):
    if request.user.role != 'admin': return redirect('dashboard')
    if request.method == 'POST':
        User.objects.create_user(
            username=request.POST.get('username'), password=request.POST.get('password'),
            first_name=request.POST.get('first_name'), last_name=request.POST.get('last_name'),
            role='ogretmen'
        )
        return redirect('yonetim_ogretmenler')
    return render(request, 'ogretmenler/ekle.html')

@login_required
def sinif_ekle(request):
    if request.method == 'POST':
        Sinif.objects.create(ad=request.POST.get('ad'), aciklama=request.POST.get('aciklama'))
        return redirect('yonetim_siniflar')
    return render(request, 'siniflar/ekle.html')

@login_required
def ders_programi_ekle(request):
    if request.method == 'POST':
        DersProgrami.objects.create(
            ders_adi=request.POST.get('ders_adi'), gun=request.POST.get('gun'),
            baslangic_saati=request.POST.get('baslangic_saati'), bitis_saati=request.POST.get('bitis_saati'),
            ogretmen_id=request.POST.get('ogretmen'), sinif_id=request.POST.get('sinif'),
            aktif=request.POST.get('aktif') == 'on'
        )
        return redirect('yonetim_ders_programi')
    return render(request, 'ders_programi/ekle.html', {
        'ogretmenler': User.objects.filter(role='ogretmen'), 'siniflar': Sinif.objects.all()
    })

# Eksik kalan basit redirect'ler
@login_required
def yoklama_gecmis(request): return redirect('dashboard')
@login_required
def yoklama_duzenle(request, pk): return redirect('dashboard')
@login_required
def ogretmen_duzenle(request, pk): return redirect('yonetim_ogretmenler')
@login_required
def ogretmen_sil(request, pk): 
    User.objects.filter(pk=pk).delete()
    return redirect('yonetim_ogretmenler')
@login_required
def sinif_duzenle(request, pk): return redirect('yonetim_siniflar')
@login_required
def sinif_sil(request, pk):
    Sinif.objects.filter(pk=pk).delete()
    return redirect('yonetim_siniflar')
@login_required
def ders_programi_duzenle(request, pk): return redirect('yonetim_ders_programi')
@login_required
def ders_programi_sil(request, pk):
    DersProgrami.objects.filter(pk=pk).delete()
    return redirect('yonetim_ders_programi')