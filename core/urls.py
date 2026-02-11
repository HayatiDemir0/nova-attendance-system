from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User  # Kendi User modelin

# --- YÖNETİCİ KONTROLÜ (Admin yoksa oluşturur) ---
def admin_kontrol():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', '123456')

# --- GİRİŞ SAYFASI ---
def login_view(request):
    admin_kontrol() # Her girişte admini kontrol eder
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı!")
            
    return render(request, 'core/login.html')

# --- TRAFİK POLİSİ (Dashboard) ---
@login_required
def dashboard(request):
    # Eğer giriş yapan kişi süper adminse veya rolü adminse
    if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
        return redirect('yonetim_panel')
    
    # Değilse (Öğretmense) normal dashboard'a gider
    return render(request, 'core/dashboard.html')

# --- SENİN ÖZEL ADMİN PANELİN ---
@login_required
def yonetim_panel(request):
    if not request.user.is_superuser and getattr(request.user, 'role', '') != 'admin':
        return redirect('dashboard')
        
    # Burada senin hazırladığın o yakışıklı admin HTML'i olmalı
    return render(request, 'core/admin_panel.html') 

# --- DİĞER ADMİN SAYFALARI (Boş kalmasın diye) ---
@login_required
def yonetim_ogretmenler(request):
    return render(request, 'core/yonetim_ogretmenler.html')

# --- ÇIKIŞ ---
def logout_view(request):
    logout(request)
    return redirect('login')