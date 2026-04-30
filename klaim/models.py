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
    ('Business', 'Business'),
    ('First', 'First'),
]

STATUS_CHOICES = [
    ('Menunggu', 'Menunggu'),
    ('Disetujui', 'Disetujui'),
    ('Ditolak', 'Ditolak'),
]


def generate_no_klaim():
    last = Klaim.objects.order_by('-id').first()
    if not last:
        return 1
    return last.id + 1


class Klaim(models.Model):
    id = models.AutoField(primary_key=True)
    email_member = models.ForeignKey(
        'main.Member',
        on_delete=models.CASCADE,
        db_column='email_member',
        related_name='klaim_list',
    )
    email_staf = models.ForeignKey(
        'main.Staf',
        on_delete=models.DO_NOTHING,
        db_column='email_staf',
        related_name='klaim_list',
        null=True,
        blank=True,
    )
    maskapai = models.ForeignKey(
        'main.Maskapai',
        on_delete=models.DO_NOTHING,
        db_column='maskapai',
        related_name='klaim_list',
    )
    bandara_asal = models.ForeignKey(
        'main.Bandara',
        on_delete=models.DO_NOTHING,
        db_column='bandara_asal',
        related_name='klaim_berangkat',
    )
    bandara_tujuan = models.ForeignKey(
        'main.Bandara',
        on_delete=models.DO_NOTHING,
        db_column='bandara_tujuan',
        related_name='klaim_tujuan',
    )
    tanggal_penerbangan = models.DateField()
    flight_number = models.CharField(max_length=10)
    nomor_tiket = models.CharField(max_length=20)
    kelas_kabin = models.CharField(max_length=20, choices=KELAS_CHOICES)
    pnr = models.CharField(max_length=10)
    status_penerimaan = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Menunggu',
    )
    timestamp = models.DateTimeField()

    class Meta:
        db_table = 'claim_missing_miles'
        managed = False
        verbose_name = 'Klaim'
        verbose_name_plural = 'Klaim'
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'email_member',
                    'flight_number',
                    'tanggal_penerbangan',
                    'nomor_tiket',
                ],
                name='unique_claim_flight',
            )
        ]

    def get_rute(self):
        return f'{self.bandara_asal_id} -> {self.bandara_tujuan_id}'

    def __str__(self):
        return f'{self.id} - {self.maskapai_id} {self.get_rute()}'
