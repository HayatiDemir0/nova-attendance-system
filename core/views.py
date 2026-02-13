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
    if request.user.role == 'admin':
        return redirect('yonetim_panel')
    
    context = {}
    bugun = timezone.now().date()
    gun_index = bugun.weekday() + 1
    
    # Burada da derslik hatasını önlemek için only() kullanıyoruz
    context['bugun_dersler'] = DersProgrami.objects.filter(
        ogretmen=request.user,
        gun=gun_index,
        aktif=True
    ).select_related('sinif').only(
        'id', 'ders_adi', 'gun', 'baslangic_saati', 'bitis_saati', 'ogretmen', 'sinif', 'aktif'
    ).order_by('baslangic_saati')
    
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
        'son_ogrenciler': Ogrenci.objects.only('ad', 'soyad', 'sinif', 'aktif').select_related('sinif').order_by('-id')[:5],
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
    
    context = {'ogretmenler': ogretmenler, 'q': q}
    return render(request, 'yonetim/ogretmenler.html', context)

@login_required
def yonetim_siniflar(request):
    """Sınıf Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.annotate(ogrenci_sayisi=Count('ogrenciler'))
    return render(request, 'yonetim/siniflar.html', {'siniflar': siniflar})

@login_required
def yonetim_ogrenciler(request):
    """Öğrenci Yönetimi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.all()
    ogrenciler = Ogrenci.objects.only('ad', 'soyad', 'tc_kimlik', 'sinif', 'veli_adi', 'veli_telefon', 'aktif').select_related('sinif')
    
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
            Q(ad__icontains=q) | Q(soyad__icontains=q) | Q(tc_kimlik__icontains=q)
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
    """Ders Programı Yönetimi - Derslik Hatası Giderildi"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    
    # Kritik Fix: .only() ile sadece veritabanında var olan alanları çağırıyoruz
    dersler = DersProgrami.objects.select_related('ogretmen', 'sinif').only(
        'id', 'ders_adi', 'gun', 'baslangic_saati', 'bitis_saati', 'ogretmen', 'sinif', 'aktif'
    )
    
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

# ==================== ÖĞRENCİ CRUD ====================

@login_required
def ogrenci_ekle(request):
    """Öğrenci Ekle"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('dashboard')
    
    siniflar = Sinif.objects.all()
    if request.method == 'POST':
        ad = request.POST.get('ad', '').strip()
        soyad = request.POST.get('soyad', '').strip()
        tc_kimlik = request.POST.get('tc_kimlik', '').strip()
        dogum_tarihi = request.POST.get('dogum_tarihi')
        cinsiyet = request.POST.get('cinsiyet')
        sinif_id = request.POST.get('sinif')
        veli_adi = request.POST.get('veli_adi', '').strip()
        veli_telefon = request.POST.get('veli_telefon', '').strip()
        veli_email = request.POST.get('veli_email', '').strip()
        adres = request.POST.get('adres', '').strip()
        
        if not ad or not soyad or not tc_kimlik or not dogum_tarihi or not sinif_id:
            messages.error(request, 'Zorunlu alanları doldurun!')
            return redirect('ogrenci_ekle')
        
        if Ogrenci.objects.filter(tc_kimlik=tc_kimlik).exists():
            messages.error(request, 'Bu TC Kimlik numarası zaten kayıtlı!')
            return redirect('ogrenci_ekle')
        
        Ogrenci.objects.create(
            ad=ad, soyad=soyad, tc_kimlik=tc_kimlik,
            dogum_tarihi=dogum_tarihi, cinsiyet=cinsiyet,
            sinif_id=sinif_id, veli_adi=veli_adi,
            veli_telefon=veli_telefon, veli_email=veli_email, adres=adres
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

@login_required
def ogrenci_detay(request, pk):
    """Öğrenci Detay"""
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    notlar = ogrenci.notlar.all()
    return render(request, 'yonetim/ogrenci_detay.html', {'ogrenci': ogrenci, 'notlar': notlar})

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
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu kullanıcı adı zaten var!')
            return redirect('ogretmen_ekle')
            
        User.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name,
            email=email, role='ogretmen'
        )
        messages.success(request, 'Öğretmen eklendi!')
        return redirect('yonetim_ogretmenler')
    return render(request, 'ogretmenler/ekle.html')

@login_required
def ogretmen_duzenle(request, pk):
    """Öğretmen Düzenle"""
    ogretmen = get_object_or_404(User, pk=pk, role='ogretmen')
    if request.method == 'POST':
        ogretmen.first_name = request.POST.get('first_name', '').strip()
        ogretmen.last_name = request.POST.get('last_name', '').strip()
        ogretmen.email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        if password:
            ogretmen.set_password(password)
        ogretmen.save()
        messages.success(request, 'Öğretmen güncellendi!')
        return redirect('yonetim_ogretmenler')
    return render(request, 'ogretmenler/duzenle.html', {'ogretmen': ogretmen})

@login_required
def ogretmen_sil(request, pk):
    """Öğretmen Sil"""
    ogretmen = get_object_or_404(User, pk=pk, role='ogretmen')
    ogretmen.delete()
    messages.success(request, 'Öğretmen silindi!')
    return redirect('yonetim_ogretmenler')

# ==================== SINIF CRUD ====================

@login_required
def sinif_ekle(request):
    """Sınıf Ekle"""
    if request.method == 'POST':
        ad = request.POST.get('ad', '').strip()
        aciklama = request.POST.get('aciklama', '').strip()
        Sinif.objects.create(ad=ad, aciklama=aciklama)
        messages.success(request, 'Sınıf eklendi!')
        return redirect('yonetim_siniflar')
    return render(request, 'siniflar/ekle.html')

@login_required
def sinif_duzenle(request, pk):
    """Sınıf Düzenle"""
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
    sinif = get_object_or_404(Sinif, pk=pk)
    sinif.delete()
    messages.success(request, 'Sınıf silindi!')
    return redirect('yonetim_siniflar')

# ==================== DERS PROGRAMI CRUD ====================

@login_required
def ders_programi_ekle(request):
    """Ders Programı Ekle"""
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    if request.method == 'POST':
        DersProgrami.objects.create(
            ders_adi=request.POST.get('ders_adi'),
            gun=request.POST.get('gun'),
            baslangic_saati=request.POST.get('baslangic_saati'),
            bitis_saati=request.POST.get('bitis_saati'),
            ogretmen_id=request.POST.get('ogretmen'),
            sinif_id=request.POST.get('sinif'),
            aktif=request.POST.get('aktif') == 'on'
        )
        messages.success(request, 'Ders programı eklendi!')
        return redirect('yonetim_ders_programi')
    return render(request, 'ders/ekle.html', {'ogretmenler': ogretmenler, 'siniflar': siniflar})

@login_required
def ders_programi_duzenle(request, pk):
    """Ders Programı Düzenle"""
    ders = get_object_or_404(DersProgrami, pk=pk)
    ogretmenler = User.objects.filter(role='ogretmen')
    siniflar = Sinif.objects.all()
    if request.method == 'POST':
        ders.ders_adi = request.POST.get('ders_adi')
        ders.gun = request.POST.get('gun')
        ders.baslangic_saati = request.POST.get('baslangic_saati')
        ders.bitis_saati = request.POST.get('bitis_saati')
        ders.ogretmen_id = request.POST.get('ogretmen')
        ders.sinif_id = request.POST.get('sinif')
        ders.aktif = request.POST.get('aktif') == 'on'
        ders.save()
        messages.success(request, 'Ders programı güncellendi!')
        return redirect('yonetim_ders_programi')
    return render(request, 'ders/duzenle.html', {'ders': ders, 'ogretmenler': ogretmenler, 'siniflar': siniflar})

@login_required
def ders_programi_sil(request, pk):
    """Ders Programı Sil"""
    ders = get_object_or_404(DersProgrami, pk=pk)
    ders.delete()
    messages.success(request, 'Ders silindi!')
    return redirect('yonetim_ders_programi')

# ==================== YOKLAMA VE NOTLAR ====================

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

@login_required
def ogrenci_not_ekle(request, pk):
    ogrenci = get_object_or_404(Ogrenci, pk=pk)
    if request.method == 'POST':
        OgrenciNotu.objects.create(
            ogrenci=ogrenci, olusturan=request.user,
            kategori=request.POST.get('kategori'),
            baslik=request.POST.get('baslik'),
            aciklama=request.POST.get('aciklama'),
            tarih=request.POST.get('tarih')
        )
        messages.success(request, 'Not eklendi!')
        return redirect('ogrenci_detay', pk=pk)
    return render(request, 'yonetim/ogrenci_not_ekle.html', {'ogrenci': ogrenci, 'bugun': timezone.now().date()})

@login_required
def ogrenci_not_duzenle(request, pk):
    ogrenci_notu = get_object_or_404(OgrenciNotu, pk=pk)
    if request.method == 'POST':
        ogrenci_notu.baslik = request.POST.get('baslik')
        ogrenci_notu.aciklama = request.POST.get('aciklama')
        ogrenci_notu.save()
        return redirect('ogrenci_detay', pk=ogrenci_notu.ogrenci.id)
    return render(request, 'yonetim/ogrenci_not_duzenle.html', {'ogrenci_notu': ogrenci_notu})

@login_required
def ogrenci_not_sil(request, pk):
    ogrenci_notu = get_object_or_404(OgrenciNotu, pk=pk)
    oid = ogrenci_notu.ogrenci.id
    ogrenci_notu.delete()
    return redirect('ogrenci_detay', pk=oid)