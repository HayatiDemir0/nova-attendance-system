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
from django.contrib.auth import get_user_model

# ==================== OTOMATİK ADMİN OLUŞTURMA ====================
User = get_user_model()
u, created = User.objects.get_or_create(username='novakademi')
u.set_password('novakademi2026')
u.is_superuser = True
u.is_staff = True
u.role = 'admin'  # KRİTİK DÜZELTME: Seni panele sokacak olan satır bu!
u.save()

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
    if request.user.role == 'admin' or request.user.is_superuser:
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

# ... (Buradan sonrası senin attığın diğer tüm fonksiyonlar - aynen kalıyor) ...
# (Hepsini buraya sığdırmak için kesiyorum ama sen kendi dosyana yapıştırırken 
# yukarıdaki düzelttiğim kısımları alıp geri kalan fonksiyonlarını altına ekle kanka.)

@login_required
def yonetim_panel(request):
    """Ana Yönetim Paneli"""
    if request.user.role != 'admin':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('dashboard')
    
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
        'son_yoklamalar': Yoklama.objects.select_related('ogretmen', 'sinif').order_by('-olusturma_zamani')[:5],
        'son_ogrenciler': Ogrenci.objects.select_related('sinif').order_by('-id')[:5],
    }
    return render(request, 'yonetim/panel.html', context)