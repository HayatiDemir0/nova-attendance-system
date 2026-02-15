from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Sinif, Ogrenci, DersProgrami, Yoklama, YoklamaDetay

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kullanıcı Adı'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Şifre'
        })
    )

class OgretmenForm(UserCreationForm):
    first_name = forms.CharField(
        label='Ad',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Soyad',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='E-posta',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    telefon = forms.CharField(
        label='Telefon',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    adres = forms.CharField(
        label='Adres',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telefon', 'adres', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'ogretmen'
        if commit:
            user.save()
        return user

class SinifForm(forms.ModelForm):
    class Meta:
        model = Sinif
        fields = ['ad', 'aciklama']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 9-A'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Sınıf açıklaması (opsiyonel)'}),
        }
        labels = {
            'ad': 'Sınıf Adı',
            'aciklama': 'Açıklama'
        }

class OgrenciForm(forms.ModelForm):
    class Meta:
        model = Ogrenci
        fields = ['ad', 'soyad', 'tc_kimlik', 'dogum_tarihi', 'cinsiyet', 'sinif', 
                  'veli_adi', 'veli_telefon', 'adres', 'profil_resmi', 'aktif']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'soyad': forms.TextInput(attrs={'class': 'form-control'}),
            'tc_kimlik': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '11'}),
            'dogum_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cinsiyet': forms.Select(attrs={'class': 'form-control'}),
            'sinif': forms.Select(attrs={'class': 'form-control'}),
            'veli_adi': forms.TextInput(attrs={'class': 'form-control'}),
            'veli_telefon': forms.TextInput(attrs={'class': 'form-control'}),
            'adres': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'ad': 'Ad',
            'soyad': 'Soyad',
            'tc_kimlik': 'TC Kimlik No',
            'dogum_tarihi': 'Doğum Tarihi',
            'cinsiyet': 'Cinsiyet',
            'sinif': 'Sınıf',
            'veli_adi': 'Veli Adı',
            'veli_telefon': 'Veli Telefon',
            'adres': 'Adres',
            'profil_resmi': 'Profil Resmi',
            'aktif': 'Aktif',
        }

class DersProgramiForm(forms.ModelForm):
    class Meta:
        model = DersProgrami
        fields = ['ogretmen', 'sinif', 'ders_adi', 'gun', 'baslangic_saati', 'bitis_saati', 'aktif']
        widgets = {
            'ogretmen': forms.Select(attrs={'class': 'form-control'}),
            'sinif': forms.Select(attrs={'class': 'form-control'}),
            'ders_adi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Matematik'}),
            'gun': forms.Select(attrs={'class': 'form-control'}),
            'baslangic_saati': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'bitis_saati': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'ogretmen': 'Öğretmen',
            'sinif': 'Sınıf',
            'ders_adi': 'Ders Adı',
            'gun': 'Gün',
            'baslangic_saati': 'Başlangıç Saati',
            'bitis_saati': 'Bitiş Saati',
            'aktif': 'Aktif',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sadece öğretmenleri göster
        self.fields['ogretmen'].queryset = User.objects.filter(role='ogretmen')

class YoklamaForm(forms.ModelForm):
    class Meta:
        model = Yoklama
        fields = ['ders_basligi']
        widgets = {
            'ders_basligi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bugünkü ders konusu'
            })
        }
        labels = {
            'ders_basligi': 'Ders Başlığı/Konusu'
        }