from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('ogretmen', 'Öğretmen'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='ogretmen')
    telefon = models.CharField(max_length=15, blank=True)
    adres = models.TextField(blank=True)
    profil_resmi = models.ImageField(upload_to='profil_resimleri/', blank=True, null=True)
    
    class Meta:
        db_table = 'kullanicilar'
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username}"


class Sinif(models.Model):
    ad = models.CharField(max_length=50, unique=True)
    aciklama = models.TextField(blank=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'siniflar'
        verbose_name = 'Sınıf'
        verbose_name_plural = 'Sınıflar'
        ordering = ['ad']
    
    def __str__(self):
        return self.ad


class Ogrenci(models.Model):
    CINSIYET_CHOICES = (
        ('E', 'Erkek'),
        ('K', 'Kız'),
    )
    
    ad = models.CharField(max_length=50)
    soyad = models.CharField(max_length=50)
    tc_kimlik = models.CharField(max_length=11, unique=True)
    dogum_tarihi = models.DateField()
    cinsiyet = models.CharField(max_length=1, choices=CINSIYET_CHOICES)
    sinif = models.ForeignKey(Sinif, on_delete=models.CASCADE, related_name='ogrenciler')
    fotograf = models.ImageField(upload_to='ogrenciler/', blank=True, null=True) # EKLENDİ
    veli_adi = models.CharField(max_length=100)
    veli_telefon = models.CharField(max_length=15)
    veli_email = models.EmailField(max_length=100, blank=True, null=True) # EKLENDİ
    adres = models.TextField(blank=True)
    kayit_tarihi = models.DateTimeField(auto_now_add=True)
    aktif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ogrenciler'
        verbose_name = 'Öğrenci'
        verbose_name_plural = 'Öğrenciler'
        ordering = ['ad', 'soyad']
    
    def __str__(self):
        return f"{self.ad} {self.soyad}"
    
    @property
    def tam_ad(self):
        return f"{self.ad} {self.soyad}"


class DersProgrami(models.Model):
    GUNLER = (
        (1, 'Pazartesi'),
        (2, 'Salı'),
        (3, 'Çarşamba'),
        (4, 'Perşembe'),
        (5, 'Cuma'),
        (6, 'Cumartesi'),
        (7, 'Pazar'),
    )
    
    ogretmen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ders_programlari')
    sinif = models.ForeignKey(Sinif, on_delete=models.CASCADE, related_name='ders_programlari')
    ders_adi = models.CharField(max_length=100)
    gun = models.IntegerField(choices=GUNLER)
    baslangic_saati = models.TimeField()
    bitis_saati = models.TimeField()
    derslik = models.CharField(max_length=50, blank=True, null=True)
    aktif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'ders_programlari'
        verbose_name = 'Ders Programı'
        verbose_name_plural = 'Ders Programları'
        ordering = ['gun', 'baslangic_saati']
        unique_together = ['ogretmen', 'sinif', 'gun', 'baslangic_saati']
    
    def __str__(self):
        return f"{self.ders_adi} - {self.sinif.ad} - {self.get_gun_display()}"


class Yoklama(models.Model):
    ders_programi = models.ForeignKey(DersProgrami, on_delete=models.CASCADE, related_name='yoklamalar')
    tarih = models.DateField()
    ders_basligi = models.CharField(max_length=200)
    ogretmen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yoklamalar')
    sinif = models.ForeignKey(Sinif, on_delete=models.CASCADE, related_name='yoklamalar')
    olusturma_zamani = models.DateTimeField(auto_now_add=True)
    guncelleme_zamani = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'yoklamalar'
        verbose_name = 'Yoklama'
        verbose_name_plural = 'Yoklamalar'
        ordering = ['-tarih', '-olusturma_zamani']
    
    def __str__(self):
        return f"{self.ders_basligi} - {self.tarih}"


class YoklamaDetay(models.Model):
    DURUM_CHOICES = (
        ('var', 'Var'),
        ('yok', 'Yok'),
        ('izinli', 'İzinli'),
        ('gec', 'Geç Kaldı'),
    )
    
    yoklama = models.ForeignKey(Yoklama, on_delete=models.CASCADE, related_name='detaylar')
    ogrenci = models.ForeignKey(Ogrenci, on_delete=models.CASCADE, related_name='yoklama_detaylari')
    durum = models.CharField(max_length=10, choices=DURUM_CHOICES, default='var')
    not_durumu = models.TextField(blank=True)
    
    class Meta:
        db_table = 'yoklama_detaylari'
        verbose_name = 'Yoklama Detayı'
        verbose_name_plural = 'Yoklama Detayları'
        unique_together = ['yoklama', 'ogrenci']
    
    def __str__(self):
        return f"{self.ogrenci.tam_ad} - {self.durum}"

class OgrenciNotu(models.Model):
    KATEGORI_CHOICES = [
        ('tatil', 'Tatil/İzin'),
        ('disiplin', 'Disiplin'),
        ('saglik', 'Sağlık'),
        ('basari', 'Başarı/Ödül'),
        ('genel', 'Genel Not'),
    ]
    
    ogrenci = models.ForeignKey(Ogrenci, on_delete=models.CASCADE, related_name='notlar')
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES, default='genel')
    baslik = models.CharField(max_length=100)
    aciklama = models.TextField()
    tarih = models.DateField()
    olusturma_zamani = models.DateTimeField(auto_now_add=True)
    guncelleme_zamani = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ogrenci_notlari'
        ordering = ['-tarih', '-olusturma_zamani']
        verbose_name = 'Öğrenci Notu'
        verbose_name_plural = 'Öğrenci Notları'
    
    def __str__(self):
        return f"{self.ogrenci.tam_ad} - {self.baslik} ({self.tarih})"
    
    def get_kategori_icon(self):
        icons = {
            'tatil': 'ti-beach',
            'disiplin': 'ti-alert-triangle',
            'saglik': 'ti-heartbeat',
            'basari': 'ti-trophy',
            'genel': 'ti-note',
        }
        return icons.get(self.kategori, 'ti-note')
    
    def get_kategori_color(self):
        colors = {
            'tatil': 'info',
            'disiplin': 'danger',
            'saglik': 'warning',
            'basari': 'success',
            'genel': 'secondary',
        }
        return colors.get(self.kategori, 'secondary')