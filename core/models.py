from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Eğer özel alanların varsa buraya ekle, yoksa pas geç
    pass