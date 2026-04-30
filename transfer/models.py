from django.db import models


class Transfer(models.Model):
    email_member_1 = models.ForeignKey(
        'main.Member',
        on_delete=models.CASCADE,
        db_column='email_member_1',
        related_name='transfer_keluar',
    )
    email_member_2 = models.ForeignKey(
        'main.Member',
        on_delete=models.CASCADE,
        db_column='email_member_2',
        related_name='transfer_masuk',
    )
    timestamp = models.DateTimeField(primary_key=True)
    jumlah = models.IntegerField()
    catatan = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'transfer'
        managed = False
        verbose_name = 'Transfer'
        verbose_name_plural = 'Transfer'
        constraints = [
            models.UniqueConstraint(
                fields=['email_member_1', 'email_member_2', 'timestamp'],
                name='pk_transfer',
            )
        ]

    def __str__(self):
        return f"{self.email_member_1_id} -> {self.email_member_2_id} : {self.jumlah}"
