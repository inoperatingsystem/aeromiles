from django.db import models


MASKAPAI_CHOICES = [
    ('GA', 'GA - Garuda Indonesia'),
    ('SQ', 'SQ - Singapore Airlines'),
    ('JT', 'JT - Lion Air'),
    ('QG', 'QG - Citilink'),
    ('ID', 'ID - Batik Air'),
    ('EK', 'EK - Emirates'),
    ('AA', 'AA - American Airlines'),
]

BANDARA_CHOICES = [
    ('CGK', 'CGK - Soekarno-Hatta, Jakarta'),
    ('DPS', 'DPS - Ngurah Rai, Bali'),
    ('SUB', 'SUB - Juanda, Surabaya'),
    ('UPG', 'UPG - Sultan Hasanuddin, Makassar'),
    ('MDN', 'MDN - Kualanamu, Medan'),
    ('SIN', 'SIN - Changi, Singapore'),
    ('NRT', 'NRT - Narita, Tokyo'),
    ('KUL', 'KUL - KLIA, Kuala Lumpur'),
    ('SYD', 'SYD - Kingsford Smith, Sydney'),
    ('HKG', 'HKG - Hong Kong International'),
]

KELAS_CHOICES = [
    ('Economy', 'Economy'),
    ('Premium Economy', 'Premium Economy'),
    ('Business', 'Business'),
    ('First', 'First'),
]

STATUS_CHOICES = [
    ('Menunggu', 'Menunggu'),
    ('Disetujui', 'Disetujui'),
    ('Ditolak', 'Ditolak'),
]


def generate_no_klaim():
    last = Klaim.objects.order_by('-no_klaim').first()
    if not last:
        return 'CLM-001'
    try:
        num = int(last.no_klaim.split('-')[1]) + 1
    except (IndexError, ValueError):
        num = Klaim.objects.count() + 1
    return f'CLM-{num:03d}'


class Klaim(models.Model):
    no_klaim            = models.CharField(max_length=20, primary_key=True)
    email_member        = models.CharField(max_length=100, blank=True, null=True)
    nama_member         = models.CharField(max_length=100, blank=True, null=True)
    maskapai            = models.CharField(max_length=5, choices=MASKAPAI_CHOICES)
    bandara_asal        = models.CharField(max_length=5, choices=BANDARA_CHOICES)
    bandara_tujuan      = models.CharField(max_length=5, choices=BANDARA_CHOICES)
    tanggal_penerbangan = models.DateField()
    flight_number       = models.CharField(max_length=20)
    kelas_kabin         = models.CharField(max_length=20, choices=KELAS_CHOICES)
    nomor_tiket         = models.CharField(max_length=50)
    pnr                 = models.CharField(max_length=20)
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Menunggu')
    tanggal_pengajuan   = models.DateTimeField(auto_now_add=True)
    email_staf          = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table         = 'klaim'
        verbose_name     = 'Klaim'
        verbose_name_plural = 'Klaim'
        ordering         = ['-tanggal_pengajuan']

    def get_rute(self):
        return f'{self.bandara_asal} → {self.bandara_tujuan}'

    def __str__(self):
        return f'{self.no_klaim} — {self.maskapai} {self.get_rute()}'
