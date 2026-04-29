from django.db import models
from django.contrib.auth.models import User
import random

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('staf', 'Staf'),
    ]
    SALUTATION_CHOICES = [
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
        ('Ms.', 'Ms.'),
    ]
    TIER_CHOICES = [
        ('Blue', 'Blue'),
        ('Silver', 'Silver'),
        ('Gold', 'Gold'),
        ('Platinum', 'Platinum'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    salutation = models.CharField(max_length=5, choices=SALUTATION_CHOICES)
    first_mid_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=5)
    phone_number = models.CharField(max_length=20)
    dob = models.DateField()
    nationality = models.CharField(max_length=50)

    # Khusus Member
    member_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='Blue', blank=True, null=True)
    total_miles = models.IntegerField(default=0)
    award_miles = models.IntegerField(default=0)
    join_date = models.DateField(auto_now_add=True)

    # Khusus Staf
    staf_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    kode_maskapai = models.CharField(max_length=5, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.role == 'member' and not self.member_number:
            self.member_number = f"M{random.randint(1000, 9999)}"
        elif self.role == 'staf' and not self.staf_id:
            self.staf_id = f"S{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.salutation} {self.first_mid_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Identitas(models.Model):
    JENIS_CHOICES = [
        ('Paspor', 'Paspor'),
        ('KTP', 'KTP'),
        ('SIM', 'SIM'),
    ]
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='identitas')
    no_dokumen = models.CharField(max_length=50, unique=True)
    jenis = models.CharField(max_length=10, choices=JENIS_CHOICES)
    negara_penerbit = models.CharField(max_length=50)
    tanggal_terbit = models.DateField()
    tanggal_habis = models.DateField()

    def __str__(self):
        return f"{self.jenis} - {self.no_dokumen}"
