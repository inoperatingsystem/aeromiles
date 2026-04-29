from django.db import models

class Transfer(models.Model):
    pengirim_email    = models.EmailField()
    pengirim_nama     = models.CharField(max_length=100)
    penerima_email    = models.EmailField()
    penerima_nama     = models.CharField(max_length=100, default='Penerima Dummy')
    jumlah_miles      = models.PositiveIntegerField()
    catatan           = models.TextField(blank=True, null=True)
    waktu_transfer    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transfer'
        verbose_name = 'Transfer'
        verbose_name_plural = 'Transfer'
        ordering = ['-waktu_transfer']

    def __str__(self):
        return f"{self.pengirim_email} -> {self.penerima_email} : {self.jumlah_miles}"
