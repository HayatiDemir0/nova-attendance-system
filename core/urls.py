from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User  # Kendi User modelin

# --- YÖNETİCİ KONTROLÜ ---
def admin_kontrol():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', '123456')

# --- GİRİŞ SAYFASI ---
def login_view(request):
    admin_kontrol()
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            # Giriş yapar yapmaz kontrol et: Adminse direkt panele!
            if user.username == 'admin':
                return redirect('yonetim_panel')
            return redirect('dashboard')
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı!")
            
    return render(request, 'core/login.html')

# --- TRAFİK POLİSİ (Dashboard) ---
@login_required
def dashboard(request):
    # İsimden yakalama (En garanti yöntem)
    if request.user.username == 'admin' or request.user.is_superuser:
        return redirect('yonetim_panel')
    
    # Öğretmense buraya düşer
    return render(request, 'core/dashboard.html')

# --- SENİN ÖZEL ADMİN PANELİN ---
@login_required
def yonetim_panel(request):
    # Eğer admin olmayan biri sızmaya çalışırsa kov
    if not request.user.is_superuser and request.user.username != 'admin':
        return redirect('dashboard')
        
    # Kendi HTML dosyanın ismi core/ içinde neyse onu yaz (Örn: admin_panel.html)
    return render(request, 'core/admin_panel.html') 

# --- ÇIKIŞ ---
def logout_view(request):
    logout(request)
    return redirect('login')