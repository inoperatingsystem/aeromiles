from django.db import models
from django.utils import timezone


class Penyedia(models.Model):
    class Meta:
        db_table = 'penyedia'
        verbose_name = 'Penyedia'
        verbose_name_plural = 'Penyedia'

    def get_nama(self):
        # relasi ke Mitra ada di app mitra (related_name='mitra')
        if hasattr(self, 'mitra'):
            return self.mitra.nama_mitra
        return f'Penyedia #{self.id}'

    def __str__(self):
        return self.get_nama()


class Hadiah(models.Model):
    kode_hadiah = models.CharField(max_length=20, primary_key=True)
    nama = models.CharField(max_length=100)
    miles = models.IntegerField()
    deskripsi = models.TextField(blank=True, null=True)
    valid_start_date = models.DateField()
    program_end = models.DateField()
    id_penyedia = models.ForeignKey(
        Penyedia,
        on_delete=models.CASCADE,
        related_name='hadiah_list',
        db_column='id_penyedia',
    )

    class Meta:
        db_table = 'hadiah'
        verbose_name = 'Hadiah'
        verbose_name_plural = 'Hadiah'

    def is_active(self):
        today = timezone.now().date()
        return self.valid_start_date <= today <= self.program_end

    def is_expired(self):
        return timezone.now().date() > self.program_end

    def __str__(self):
        return f'{self.kode_hadiah} — {self.nama}'


def generate_kode_hadiah():
    last = Hadiah.objects.order_by('-kode_hadiah').first()
    if not last:
        return 'RWD-001'
    try:
        num = int(last.kode_hadiah.split('-')[1]) + 1
    except (IndexError, ValueError):
        num = Hadiah.objects.count() + 1
    return f'RWD-{num:03d}'