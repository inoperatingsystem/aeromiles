from django.db import models
from hadiah.models import Penyedia


class Mitra(models.Model):
    """
    Tabel MITRA — penyedia berjenis partner eksternal.
    email_mitra sebagai PK.
    id_penyedia OneToOne → Penyedia (dari app hadiah).
    """
    email_mitra = models.EmailField(max_length=100, primary_key=True)
    id_penyedia = models.OneToOneField(
        Penyedia,
        on_delete=models.CASCADE,
        related_name='mitra',
        db_column='id_penyedia',
    )
    nama_mitra = models.CharField(max_length=100)
    tanggal_kerja_sama = models.DateField()

    class Meta:
        db_table = 'mitra'
        managed = False
        verbose_name = 'Mitra'
        verbose_name_plural = 'Mitra'

    def __str__(self):
        return self.nama_mitra