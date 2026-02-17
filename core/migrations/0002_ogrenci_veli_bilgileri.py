from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ogrenci',
            name='veli_adi',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='ogrenci',
            name='veli_telefon',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='ogrenci',
            name='veli_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='ogrenci',
            name='fotograf',
            field=models.ImageField(blank=True, null=True, upload_to='ogrenci_fotograflari/'),
        ),
        migrations.AddField(
            model_name='dersprogrami',
            name='derslik',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]