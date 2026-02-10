from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, YoklamaDetay
from django.contrib.auth.forms import UserCreationForm
from .forms import (LoginForm, OgretmenForm, SinifForm, OgrenciForm, 
                    DersProgramiForm, YoklamaForm)

# ==================== GENEL VİEWLER ====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Hoş geldiniz, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        if password1 != password2:
            messages.error(request, 'Şifreler eşleşmiyor!')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu kullanıcı adı zaten kullanılıyor!')
            return render(request, 'register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            role='ogretmen'
        )
        
        messages.success(request, 'Kayıt başarılı! Giriş yapabilirsiniz.')
        return redirect('login')
    
    return render(request, 'register.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Başarıyla çıkış yaptınız.')
    return redirect('login')

@login_required
def dashboard(request):
    """
    Öğretmenler için Dashboard
    Adminler Yönetim Paneline yönlendirilir
    """
    
    # KONTROL: Admin ise Yönetim Paneline yönlendir
    if request.user.role == 'admin':
        return redirect('yonetim_panel')
    
    # Öğretmen Dashboard
    context = {}
    bugun = timezone.now().date()
    gun_index = bugun.weekday() + 1
    
    context['bugun_dersler'] = DersProgrami.objects.filter(
        ogretmen=request.user,
        gun=gun_index,
        aktif=True
    ).select_related('sinif').order_by('baslangic_saati')
    
    context['siniflar'] = Sinif.objects.filter(
        ders_programlari__ogretmen=request.user,
        ders_programlari__aktif=True
    ).distinct()
    
    context['bugun_yoklamalar'] = Yoklama.objects.filter(
        ogretmen=request.user,
        tarih=bugun
    ).select_related('sinif', 'ders_programi')
    
    return render(request, 'dashboard.html', context)
# ==================== ÖĞRETMEN İŞLEMLERİ (ADMIN) ====================

@login_required
def ogretmen_listesi(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogretmenler = User.objects.filter(role='ogretmen').order_by('first_name', 'last_name')
    return render(request, 'ogretmenler/liste.html', {'ogretmenler': ogretmenler})

@login_required
def ogretmen_ekle(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = OgretmenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Öğretmen başarıyla eklendi.')
            return redirect('ogretmen_listesi')
    else:
        form = OgretmenForm()
    
    return render(request, 'ogretmenler/ekle.html', {'form': form})

@login_required
def ogretmen_duzenle(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogretmen = get_object_or_404(User, pk=pk, role='ogretmen')
    
    if request.method == 'POST':
        ogretmen.first_name = request.POST.get('first_name')
        ogretmen.last_name = request.POST.get('last_name')
        ogretmen.email = request.POST.get('email')
        ogretmen.telefon = request.POST.get('telefon')
        ogretmen.adres = request.POST.get('adres')
        ogretmen.save()
        
        messages.success(request, 'Öğretmen bilgileri güncellendi.')
        return redirect('ogretmen_listesi')
    
    return render(request, 'ogretmenler/duzenle.html', {'ogretmen': ogretmen})

@login_required
def ogretmen_sil(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogretmen = get_object_or_404(User, pk=pk, role='ogretmen')
    ogretmen.delete()
    messages.success(request, 'Öğretmen silindi.')
    return redirect('ogretmen_listesi')

# ==================== SINIF İŞLEMLERİ (ADMIN) ====================

@login_required
def sinif_listesi(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.annotate(
        ogrenci_sayisi=Count('ogrenciler', filter=Q(ogrenciler__aktif=True))
    ).order_by('ad')
    
    return render(request, 'siniflar/liste.html', {'siniflar': siniflar})

@login_required
def sinif_ekle(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SinifForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sınıf başarıyla oluşturuldu.')
            return redirect('sinif_listesi')
    else:
        form = SinifForm()
    
    return render(request, 'siniflar/ekle.html', {'form': form})

@login_required
def sinif_duzenle(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    sinif = get_object_or_404(Sinif, pk=pk)
    
    if request.method == 'POST':
        form = SinifForm(request.POST, instance=sinif)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sınıf bilgileri güncellendi.')
            return redirect('sinif_listesi')
    else:
        form = SinifForm(instance=sinif)
    
    return render(request, 'siniflar/duzenle.html', {'form': form, 'sinif': sinif})

@login_required
def sinif_sil(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    sinif = get_object_or_404(Sinif, pk=pk)
    sinif.delete()
    messages.success(request, 'Sınıf silindi.')
    return redirect('sinif_listesi')

# ==================== ÖĞRENCİ İŞLEMLERİ (ADMIN) ====================

@login_required
def ogrenci_listesi(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogrenciler = Ogrenci.objects.select_related('sinif').order_by('sinif__ad', 'ad', 'soyad')
    
    sinif_id = request.GET.get('sinif')
    if sinif_id:
        ogrenciler = ogrenciler.filter(sinif_id=sinif_id)
    
    siniflar = Sinif.objects.all()
    
    return render(request, 'ogrenciler/liste.html', {
        'ogrenciler': ogrenciler,
        'siniflar': siniflar,
        'secili_sinif': sinif_id
    })

@login_required
def ogrenci_ekle(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = OgrenciForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Öğrenci başarıyla eklendi.')
            return redirect('ogrenci_listesi')
    else:
        form = OgrenciForm()
    
    return render(request, 'ogrenciler/ekle.html', {'form': form})

@login_required
def ogrenci_duzenle(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    
    if request.method == 'POST':
        form = OgrenciForm(request.POST, request.FILES, instance=ogrenci)
        if form.is_valid():
            form.save()
            messages.success(request, 'Öğrenci bilgileri güncellendi.')
            return redirect('ogrenci_listesi')
    else:
        form = OgrenciForm(instance=ogrenci)
    
    return render(request, 'ogrenciler/duzenle.html', {'form': form, 'ogrenci': ogrenci})

@login_required
def ogrenci_sil(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    ogrenci.delete()
    messages.success(request, 'Öğrenci silindi.')
    return redirect('ogrenci_listesi')

# ==================== DERS PROGRAMI İŞLEMLERİ (ADMIN) ====================

@login_required
def ders_programi_listesi(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    dersler = DersProgrami.objects.select_related('ogretmen', 'sinif').order_by('gun', 'baslangic_saati')
    
    ogretmen_id = request.GET.get('ogretmen')
    sinif_id = request.GET.get('sinif')
    
    if ogretmen_id:
        dersler = dersler.filter(ogretmen_id=ogretmen_id)
    if sinif_id:
        dersler = dersler.filter(sinif_id=sinif_id)
    
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    
    return render(request, 'ders_programi/liste.html', {
        'dersler': dersler,
        'ogretmenler': ogretmenler,
        'siniflar': siniflar
    })

@login_required
def ders_programi_ekle(request):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DersProgramiForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ders programı başarıyla eklendi.')
            return redirect('ders_programi_listesi')
    else:
        form = DersProgramiForm()
    
    return render(request, 'ders_programi/ekle.html', {'form': form})

@login_required
def ders_programi_duzenle(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ders = get_object_or_404(DersProgrami, pk=pk)
    
    if request.method == 'POST':
        form = DersProgramiForm(request.POST, instance=ders)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ders programı güncellendi.')
            return redirect('ders_programi_listesi')
    else:
        form = DersProgramiForm(instance=ders)
    
    return render(request, 'ders_programi/duzenle.html', {'form': form, 'ders': ders})

@login_required
def ders_programi_sil(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ders = get_object_or_404(DersProgrami, pk=pk)
    ders.delete()
    messages.success(request, 'Ders programı silindi.')
    return redirect('ders_programi_listesi')

# ==================== YOKLAMA İŞLEMLERİ (ÖĞRETMEN) ====================

@login_required
def yoklama_al(request, ders_id):
    if request.user.role != 'ogretmen':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ders = get_object_or_404(DersProgrami, pk=ders_id, ogretmen=request.user)
    bugun = timezone.now().date()
    
    # YENİ: Her seferinde yeni yoklama oluştur (birden fazla yoklama alınabilir)
    yoklama = Yoklama.objects.create(
        ders_programi=ders,
        tarih=bugun,
        ogretmen=request.user,
        sinif=ders.sinif,
        ders_basligi=''
    )
    
    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi')
        
        if not ders_basligi:
            messages.error(request, 'Lütfen ders konusunu yazın!')
            ogrenciler = ders.sinif.ogrenciler.filter(aktif=True).order_by('ad', 'soyad')
            return render(request, 'yoklama/al.html', {
                'ders': ders,
                'yoklama': yoklama,
                'ogrenciler': ogrenciler,
                'bugun': bugun,
                'yoklama_detaylari': {}
            })
        
        yoklama.ders_basligi = ders_basligi
        yoklama.save()
        
        ogrenciler = ders.sinif.ogrenciler.filter(aktif=True)
        
        for ogrenci in ogrenciler:
            durum = request.POST.get(f'durum_{ogrenci.id}', 'var')
            not_durumu = request.POST.get(f'not_{ogrenci.id}', '')
            
            YoklamaDetay.objects.create(
                yoklama=yoklama,
                ogrenci=ogrenci,
                durum=durum,
                not_durumu=not_durumu
            )
        
        messages.success(request, '✅ Yoklama başarıyla kaydedildi!')
        return redirect('yoklama_detay', pk=yoklama.id)
    
    ogrenciler = ders.sinif.ogrenciler.filter(aktif=True).order_by('ad', 'soyad')
    yoklama_detaylari = {}
    
    return render(request, 'yoklama/al.html', {
        'ders': ders,
        'yoklama': yoklama,
        'ogrenciler': ogrenciler,
        'bugun': bugun,
        'yoklama_detaylari': yoklama_detaylari
    })

@login_required
def yoklama_duzenle(request, pk):
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    yoklama = get_object_or_404(Yoklama, pk=pk)
    
    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi')
        yoklama.ders_basligi = ders_basligi
        yoklama.save()
        
        ogrenciler = yoklama.sinif.ogrenciler.filter(aktif=True)
        
        for ogrenci in ogrenciler:
            durum = request.POST.get(f'durum_{ogrenci.id}', 'var')
            not_durumu = request.POST.get(f'not_{ogrenci.id}', '')
            
            YoklamaDetay.objects.update_or_create(
                yoklama=yoklama,
                ogrenci=ogrenci,
                defaults={
                    'durum': durum,
                    'not_durumu': not_durumu
                }
            )
        
        messages.success(request, 'Yoklama güncellendi.')
        return redirect('yoklama_detay', pk=yoklama.id)
    
    ogrenciler = yoklama.sinif.ogrenciler.filter(aktif=True).order_by('ad', 'soyad')
    yoklama_detaylari = {
        detay.ogrenci_id: detay 
        for detay in yoklama.detaylar.all()
    }
    
    return render(request, 'yoklama/duzenle.html', {
        'yoklama': yoklama,
        'ogrenciler': ogrenciler,
        'yoklama_detaylari': yoklama_detaylari,
    })

@login_required
def yoklama_gecmis(request):
    if request.user.role == 'admin':
        yoklamalar = Yoklama.objects.select_related('ogretmen', 'sinif', 'ders_programi').order_by('-tarih', '-olusturma_zamani')
        
        ogretmen_id = request.GET.get('ogretmen')
        sinif_id = request.GET.get('sinif')
        tarih = request.GET.get('tarih')
        
        if ogretmen_id:
            yoklamalar = yoklamalar.filter(ogretmen_id=ogretmen_id)
        if sinif_id:
            yoklamalar = yoklamalar.filter(sinif_id=sinif_id)
        if tarih:
            yoklamalar = yoklamalar.filter(tarih=tarih)
        
        ogretmenler = User.objects.filter(role='ogretmen')
        siniflar = Sinif.objects.all()
        
        context = {
            'yoklamalar': yoklamalar,
            'ogretmenler': ogretmenler,
            'siniflar': siniflar
        }
        
        return render(request, 'yoklama/gecmis.html', context)
    else:
        yoklamalar = Yoklama.objects.filter(
            ogretmen=request.user
        ).select_related('sinif', 'ders_programi').order_by('-tarih', '-olusturma_zamani')
        
        context = {
            'yoklamalar': yoklamalar
        }
        
        return render(request, 'yoklama/gecmis.html', context)

@login_required
def yoklama_detay(request, pk):
    yoklama = get_object_or_404(Yoklama, pk=pk)
    
    if request.user.role == 'ogretmen' and yoklama.ogretmen != request.user:
        messages.error(request, 'Bu yoklamayı görüntüleme yetkiniz yok.')
        return redirect('dashboard')
    
    detaylar = yoklama.detaylar.select_related('ogrenci').order_by('ogrenci__ad', 'ogrenci__soyad')
    
    toplam = detaylar.count()
    var = detaylar.filter(durum='var').count()
    yok = detaylar.filter(durum='yok').count()
    izinli = detaylar.filter(durum='izinli').count()
    gec = detaylar.filter(durum='gec').count()
    
    return render(request, 'yoklama/detay.html', {
        'yoklama': yoklama,
        'detaylar': detaylar,
        'istatistik': {
            'toplam': toplam,
            'var': var,
            'yok': yok,
            'izinli': izinli,
            'gec': gec
        }
    })

# ==================== TAKVİM ====================

@login_required
def takvim(request):
    import calendar
    from datetime import date
    
    bugun = date.today()
    yil = int(request.GET.get('yil', bugun.year))
    ay = int(request.GET.get('ay', bugun.month))
    
    cal = calendar.monthcalendar(yil, ay)
    
    ay_adlari = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
        5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
        9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }
    ay_adi = ay_adlari.get(ay, 'Bilinmeyen')
    
    if request.user.role == 'admin':
        yoklamalar = Yoklama.objects.filter(
            tarih__year=yil,
            tarih__month=ay
        ).select_related('ogretmen', 'sinif')
    else:
        yoklamalar = Yoklama.objects.filter(
            ogretmen=request.user,
            tarih__year=yil,
            tarih__month=ay
        ).select_related('sinif')
    
    yoklama_dict = {}
    for yoklama in yoklamalar:
        gun = yoklama.tarih.day
        if gun not in yoklama_dict:
            yoklama_dict[gun] = []
        yoklama_dict[gun].append(yoklama)
    
    if ay == 1:
        onceki_ay = 12
        onceki_yil = yil - 1
    else:
        onceki_ay = ay - 1
        onceki_yil = yil
    
    if ay == 12:
        sonraki_ay = 1
        sonraki_yil = yil + 1
    else:
        sonraki_ay = ay + 1
        sonraki_yil = yil
    
    context = {
        'takvim': cal,
        'yil': yil,
        'ay': ay,
        'ay_adi': ay_adi,
        'bugun': bugun,
        'yoklamalar': yoklama_dict,
        'onceki_ay': onceki_ay,
        'onceki_yil': onceki_yil,
        'sonraki_ay': sonraki_ay,
        'sonraki_yil': sonraki_yil
    }
    
    return render(request, 'takvim.html', context)

# ==================== RAPORLAR ====================

@login_required
def raporlar(request):
    context = {}
    
    if request.user.role == 'admin':
        context['siniflar'] = Sinif.objects.all()
        context['ogrenciler'] = Ogrenci.objects.filter(aktif=True).select_related('sinif').order_by('sinif__ad', 'ad', 'soyad')
    else:
        context['siniflar'] = Sinif.objects.filter(
            ders_programlari__ogretmen=request.user,
            ders_programlari__aktif=True
        ).distinct()
        
        sinif_ids = context['siniflar'].values_list('id', flat=True)
        context['ogrenciler'] = Ogrenci.objects.filter(
            sinif_id__in=sinif_ids,
            aktif=True
        ).select_related('sinif').order_by('sinif__ad', 'ad', 'soyad')
    
    return render(request, 'raporlar/index.html', context)

@login_required
def ogrenci_devamsizlik_raporu(request):
    ogrenci_id = request.GET.get('ogrenci_id')
    baslangic = request.GET.get('baslangic')
    bitis = request.GET.get('bitis')
    
    if not ogrenci_id:
        messages.error(request, 'Lütfen bir öğrenci seçin.')
        return redirect('raporlar')
    
    ogrenci = get_object_or_404(Ogrenci, pk=ogrenci_id)
    
    detaylar = YoklamaDetay.objects.filter(ogrenci=ogrenci).select_related('yoklama__ogretmen')
    
    if baslangic:
        detaylar = detaylar.filter(yoklama__tarih__gte=baslangic)
    if bitis:
        detaylar = detaylar.filter(yoklama__tarih__lte=bitis)
    
    detaylar = detaylar.order_by('-yoklama__tarih')
    
    toplam = detaylar.count()
    var = detaylar.filter(durum='var').count()
    yok = detaylar.filter(durum='yok').count()
    izinli = detaylar.filter(durum='izinli').count()
    gec = detaylar.filter(durum='gec').count()
    
    devamsizlik_yuzdesi = 0
    if toplam > 0:
        devamsizlik_yuzdesi = round((yok / toplam) * 100, 1)
    
    context = {
        'ogrenci': ogrenci,
        'detaylar': detaylar,
        'baslangic': baslangic or '',
        'bitis': bitis or '',
        'istatistik': {
            'toplam': toplam,
            'var': var,
            'yok': yok,
            'izinli': izinli,
            'gec': gec,
            'devamsizlik_yuzdesi': devamsizlik_yuzdesi
        }
    }
    
    return render(request, 'raporlar/ogrenci_devamsizlik.html', context)

@login_required
def sinif_yoklama_raporu(request):
    sinif_id = request.GET.get('sinif_id')
    baslangic = request.GET.get('baslangic')
    bitis = request.GET.get('bitis')
    
    if not sinif_id:
        messages.error(request, 'Lütfen bir sınıf seçin.')
        return redirect('raporlar')
    
    sinif = get_object_or_404(Sinif, pk=sinif_id)
    
    yoklamalar = Yoklama.objects.filter(sinif=sinif)
    
    if baslangic:
        yoklamalar = yoklamalar.filter(tarih__gte=baslangic)
    if bitis:
        yoklamalar = yoklamalar.filter(tarih__lte=bitis)
    
    yoklamalar = yoklamalar.select_related('ogretmen').order_by('-tarih')
    
    ogrenciler = sinif.ogrenciler.filter(aktif=True).order_by('ad', 'soyad')
    
    ogrenci_stats = []
    for ogrenci in ogrenciler:
        detaylar = YoklamaDetay.objects.filter(
            ogrenci=ogrenci,
            yoklama__sinif=sinif
        )
        
        if baslangic:
            detaylar = detaylar.filter(yoklama__tarih__gte=baslangic)
        if bitis:
            detaylar = detaylar.filter(yoklama__tarih__lte=bitis)
        
        toplam = detaylar.count()
        var = detaylar.filter(durum='var').count()
        yok = detaylar.filter(durum='yok').count()
        izinli = detaylar.filter(durum='izinli').count()
        gec = detaylar.filter(durum='gec').count()
        
        devamsizlik_yuzdesi = 0
        if toplam > 0:
            devamsizlik_yuzdesi = round((yok / toplam) * 100, 1)
        
        ogrenci_stats.append({
            'ogrenci': ogrenci,
            'toplam': toplam,
            'var': var,
            'yok': yok,
            'izinli': izinli,
            'gec': gec,
            'devamsizlik_yuzdesi': devamsizlik_yuzdesi
        })
    
    context = {
        'sinif': sinif,
        'yoklamalar': yoklamalar,
        'ogrenci_stats': ogrenci_stats,
        'baslangic': baslangic or '',
        'bitis': bitis or '',
    }
    
    return render(request, 'raporlar/sinif_yoklama.html', context)

# ==================== ÖZEL YÖNETİM PANELİ ====================

@login_required
def yonetim_panel(request):
    """Ana Yönetim Paneli"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    # İstatistikler
    context = {
        'toplam_ogretmen': User.objects.filter(role='ogretmen').count(),
        'toplam_sinif': Sinif.objects.count(),
        'toplam_ogrenci': Ogrenci.objects.filter(aktif=True).count(),
        'toplam_ders': DersProgrami.objects.filter(aktif=True).count(),
        'bu_ay_yoklama': Yoklama.objects.filter(
            tarih__month=timezone.now().month,
            tarih__year=timezone.now().year
        ).count(),
        'bugun_yoklama': Yoklama.objects.filter(tarih=timezone.now().date()).count(),
        
        # Son Aktiviteler
        'son_yoklamalar': Yoklama.objects.select_related('ogretmen', 'sinif').order_by('-olusturma_zamani')[:5],
        'son_ogrenciler': Ogrenci.objects.select_related('sinif').order_by('-id')[:5],
    }
    
    return render(request, 'yonetim/panel.html', context)

@login_required
def yonetim_ogretmenler(request):
    """Öğretmen Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogretmenler = User.objects.filter(role='ogretmen').order_by('first_name', 'last_name')
    
    # Arama
    q = request.GET.get('q')
    if q:
        ogretmenler = ogretmenler.filter(
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q) | 
            Q(email__icontains=q)
        )
    
    return render(request, 'yonetim/ogretmenler.html', {'ogretmenler': ogretmenler, 'q': q})

@login_required
def yonetim_siniflar(request):
    """Sınıf Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.annotate(
        ogrenci_sayisi=Count('ogrenciler', filter=Q(ogrenciler__aktif=True))
    ).order_by('ad')
    
    return render(request, 'yonetim/siniflar.html', {'siniflar': siniflar})

@login_required
def yonetim_ogrenciler(request):
    """Öğrenci Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    ogrenciler = Ogrenci.objects.select_related('sinif').order_by('sinif__ad', 'ad', 'soyad')
    
    # Filtreleme
    sinif_id = request.GET.get('sinif')
    if sinif_id:
        ogrenciler = ogrenciler.filter(sinif_id=sinif_id)
    
    aktif = request.GET.get('aktif')
    if aktif == '1':
        ogrenciler = ogrenciler.filter(aktif=True)
    elif aktif == '0':
        ogrenciler = ogrenciler.filter(aktif=False)
    
    # Arama
    q = request.GET.get('q')
    if q:
        ogrenciler = ogrenciler.filter(
            Q(ad__icontains=q) | 
            Q(soyad__icontains=q) | 
            Q(tc_kimlik__icontains=q)
        )
    
    siniflar = Sinif.objects.all()
    
    return render(request, 'yonetim/ogrenciler.html', {
        'ogrenciler': ogrenciler,
        'siniflar': siniflar,
        'q': q,
        'secili_sinif': sinif_id,
        'secili_aktif': aktif
    })

@login_required
def yonetim_ders_programi(request):
    """Ders Programı Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    dersler = DersProgrami.objects.select_related('ogretmen', 'sinif').order_by('gun', 'baslangic_saati')
    
    # Filtreleme
    ogretmen_id = request.GET.get('ogretmen')
    if ogretmen_id:
        dersler = dersler.filter(ogretmen_id=ogretmen_id)
    
    sinif_id = request.GET.get('sinif')
    if sinif_id:
        dersler = dersler.filter(sinif_id=sinif_id)
    
    gun = request.GET.get('gun')
    if gun:
        dersler = dersler.filter(gun=gun)
    
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    
    return render(request, 'yonetim/ders_programi.html', {
        'dersler': dersler,
        'ogretmenler': ogretmenler,
        'siniflar': siniflar,
        'secili_ogretmen': ogretmen_id,
        'secili_sinif': sinif_id,
        'secili_gun': gun
    })

@login_required
def yonetim_yoklamalar(request):
    """Yoklama Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    yoklamalar = Yoklama.objects.select_related('ogretmen', 'sinif').order_by('-tarih', '-olusturma_zamani')
    
    # Filtreleme
    ogretmen_id = request.GET.get('ogretmen')
    if ogretmen_id:
        yoklamalar = yoklamalar.filter(ogretmen_id=ogretmen_id)
    
    sinif_id = request.GET.get('sinif')
    if sinif_id:
        yoklamalar = yoklamalar.filter(sinif_id=sinif_id)
    
    tarih = request.GET.get('tarih')
    if tarih:
        yoklamalar = yoklamalar.filter(tarih=tarih)
    
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    
    # Pagination (sayfa başına 50)
    from django.core.paginator import Paginator
    paginator = Paginator(yoklamalar, 50)
    page = request.GET.get('page')
    yoklamalar = paginator.get_page(page)
    
    return render(request, 'yonetim/yoklamalar.html', {
        'yoklamalar': yoklamalar,
        'ogretmenler': ogretmenler,
        'siniflar': siniflar,
        'secili_ogretmen': ogretmen_id,
        'secili_sinif': sinif_id,
        'secili_tarih': tarih
    })

@login_required
def yonetim_ayarlar(request):
    """Sistem Ayarları"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Veritabanı temizleme
        if 'temizle_eski_yoklamalar' in request.POST:
            tarih = request.POST.get('tarih')
            if tarih:
                silinen = Yoklama.objects.filter(tarih__lt=tarih).delete()
                messages.success(request, f'{silinen[0]} adet eski yoklama silindi.')
        
        # Toplu öğrenci aktiflik güncelleme
        if 'pasif_yap' in request.POST:
            sinif_id = request.POST.get('sinif_id')
            if sinif_id:
                guncellenen = Ogrenci.objects.filter(sinif_id=sinif_id).update(aktif=False)
                messages.success(request, f'{guncellenen} öğrenci pasif yapıldı.')
        
        return redirect('yonetim_ayarlar')
    
    context = {
        'siniflar': Sinif.objects.all(),
        'toplam_yoklama': Yoklama.objects.count(),
        'en_eski_yoklama': Yoklama.objects.order_by('tarih').first(),
    }
    
    return render(request, 'yonetim/ayarlar.html', context)