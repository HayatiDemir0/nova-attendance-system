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
    
    context['alinan_ders_ids'] = list(context['bugun_yoklamalar'].values_list('ders_programi_id', flat=True))
    context['siniflar'] = Sinif.objects.filter(ders_programlari__ogretmen=request.user).distinct()
    context['bugun'] = bugun
    return render(request, 'dashboard.html', context)

# ==================== ADMİN PANELİ VE LİSTELEME ====================

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
    }
    return render(request, 'yonetim/panel.html', context)

@login_required
def yonetim_yoklamalar(request):
    """Filtrelemeli ve Sayfalamalı Yoklama Listesi"""
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    yoklamalar_sorgu = Yoklama.objects.select_related('ogretmen', 'sinif').order_by('-tarih', '-id')
    
    # Filtreleme Parametreleri
    ogretmen_id = request.GET.get('ogretmen')
    sinif_id = request.GET.get('sinif')
    tarih = request.GET.get('tarih')

    if ogretmen_id: yoklamalar_sorgu = yoklamalar_sorgu.filter(ogretmen_id=ogretmen_id)
    if sinif_id: yoklamalar_sorgu = yoklamalar_sorgu.filter(sinif_id=sinif_id)
    if tarih: yoklamalar_sorgu = yoklamalar_sorgu.filter(tarih=tarih)

    # Sayfalama
    paginator = Paginator(yoklamalar_sorgu, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'yonetim/yoklamalar.html', {
        'yoklamalar': page_obj,
        'ogretmenler': User.objects.filter(role='ogretmen'),
        'siniflar': Sinif.objects.all(),
        'secili_ogretmen': ogretmen_id,
        'secili_sinif': sinif_id,
        'secili_tarih': tarih
    })

# ==================== YOKLAMA SİSTEMİ (KRİTİK) ====================

@login_required
def yoklama_al(request, ders_id):
    ders = get_object_or_404(DersProgrami, id=ders_id)
    ogrenciler = Ogrenci.objects.filter(sinif=ders.sinif, aktif=True)
    
    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi', '').strip()
        
        # --- TAM 3 KELİME KONTROLÜ ---
        if len(ders_basligi.split()) != 3:
            messages.error(request, f"Hata: Ders konusu tam 3 kelime olmalıdır! (Girdiğiniz: {len(ders_basligi.split())})")
            return render(request, 'yoklama/al.html', {'ders': ders, 'ogrenciler': ogrenciler, 'hata_baslik': ders_basligi})

        yoklama = Yoklama.objects.create(
            ders_programi=ders, ders_basligi=ders_basligi,
            ogretmen=request.user, sinif=ders.sinif, tarih=timezone.now().date()
        )

        for ogrenci in ogrenciler:
            durum = request.POST.get(f'durum_{ogrenci.id}', 'var')
            not_alani = request.POST.get(f'not_{ogrenci.id}', '')
            YoklamaDetay.objects.create(yoklama=yoklama, ogrenci=ogrenci, durum=durum, not_durumu=not_alani)
        
        messages.success(request, 'Yoklama başarıyla sisteme işlendi.')
        return redirect('dashboard')

    return render(request, 'yoklama/al.html', {'ders': ders, 'ogrenciler': ogrenciler})

@login_required
def yoklama_duzenle(request, pk):
    """Adminin yoklamaları ana sayfaya atılmadan düzenlemesini sağlar"""
    yoklama = get_object_or_404(Yoklama, pk=pk)
    
    if request.user.role != 'admin' and yoklama.ogretmen != request.user:
        messages.error(request, "Bu işlemi yapmaya yetkiniz yok!")
        return redirect('dashboard')

    detaylar = yoklama.detaylar.all().select_related('ogrenci')

    if request.method == 'POST':
        ders_basligi = request.POST.get('ders_basligi', '').strip()
        
        # --- TAM 3 KELİME KONTROLÜ (DÜZENLEMEDE DE GEÇERLİ) ---
        if len(ders_basligi.split()) != 3:
            messages.error(request, "Hata: Ders başlığı tam 3 kelime olmalıdır!")
            return render(request, 'yoklama/duzenle.html', {'yoklama': yoklama, 'detaylar': detaylar})

        yoklama.ders_basligi = ders_basligi
        yoklama.save()

        for detay in detaylar:
            detay.durum = request.POST.get(f'durum_{detay.ogrenci.id}')
            detay.not_durumu = request.POST.get(f'not_{detay.ogrenci.id}')
            detay.save()

        messages.success(request, "Yoklama başarıyla güncellendi.")
        return redirect('yonetim_yoklamalar')

    return render(request, 'yoklama/duzenle.html', {'yoklama': yoklama, 'detaylar': detaylar})

@login_required
def yoklama_detay(request, pk):
    yoklama = get_object_or_404(Yoklama, pk=pk)
    detaylar = yoklama.detaylar.all().select_related('ogrenci')
    istatistik = {
        'toplam': detaylar.count(),
        'var': detaylar.filter(durum='var').count(),
        'yok': detaylar.filter(durum='yok').count(),
        'izinli': detaylar.filter(durum='izinli').count(),
    }
    return render(request, 'yoklama/detay.html', {'yoklama': yoklama, 'detaylar': detaylar, 'istatistik': istatistik})

# ==================== ÖĞRENCİ VE DİĞER İŞLEMLER ====================

@login_required
def ogrenci_not_ekle(request, ogrenci_id):
    if request.method == 'POST':
        ogrenci = get_object_or_404(Ogrenci, id=ogrenci_id)
        aciklama = request.POST.get('aciklama', '').strip()
        if len(aciklama.split()) < 5:
            messages.error(request, "Not çok kısa! En az 5 kelime yazmalısınız.")
            return redirect('ogrenci_detay', pk=ogrenci_id)
            
        OgrenciNotu.objects.create(
            ogrenci=ogrenci, olusturan=request.user,
            baslik=request.POST.get('baslik'), aciklama=aciklama, tarih=timezone.now().date()
        )
        messages.success(request, "Not eklendi.")
    return redirect('ogrenci_detay', pk=ogrenci_id)

@login_required
def ogretmen_sil(request, pk):
    if request.user.role == 'admin':
        User.objects.filter(pk=pk).delete()
        messages.success(request, "Öğretmen silindi.")
    return redirect('yonetim_ogretmenler')

@login_required
def sinif_sil(request, pk):
    if request.user.role == 'admin':
        Sinif.objects.filter(pk=pk).delete()
        messages.success(request, "Sınıf silindi.")
    return redirect('yonetim_siniflar')