from django.db import models


class Pengguna(models.Model):
    SALUTATION_CHOICES = [
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
        ('Ms.', 'Ms.'),
        ('Dr.', 'Dr.'),
    ]

    email = models.EmailField(max_length=100, primary_key=True)
    password = models.CharField(max_length=255)
    salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES)
    first_mid_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=5)
    mobile_number = models.CharField(max_length=20)
    tanggal_lahir = models.DateField()
    kewarganegaraan = models.CharField(max_length=50)

    class Meta:
        db_table = 'pengguna'
        managed = False

    @property
    def full_name(self):
        return f"{self.salutation} {self.first_mid_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class UserProfile(Pengguna):
    class Meta:
        proxy = True


class Tier(models.Model):
    id_tier = models.CharField(max_length=10, primary_key=True)
    nama = models.CharField(max_length=50)
    minimal_frekuensi_terbang = models.IntegerField()
    minimal_tier_miles = models.IntegerField()

    class Meta:
        db_table = 'tier'
        managed = False

    def __str__(self):
        return f"{self.id_tier} - {self.nama}"


class Member(models.Model):
    email = models.OneToOneField(
        Pengguna,
        primary_key=True,
        on_delete=models.DO_NOTHING,
        related_name='member',
        db_column='email',
    )
    nomor_member = models.CharField(max_length=20, unique=True)
    tanggal_bergabung = models.DateField()
    id_tier = models.ForeignKey(
        Tier,
        on_delete=models.DO_NOTHING,
        db_column='id_tier',
        related_name='members',
    )
    award_miles = models.IntegerField(null=True, blank=True)
    total_miles = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'member'
        managed = False

    def __str__(self):
        return self.nomor_member


class Bandara(models.Model):
    iata_code = models.CharField(max_length=3, primary_key=True)
    nama = models.CharField(max_length=100)
    kota = models.CharField(max_length=100)
    negara = models.CharField(max_length=100)

    class Meta:
        db_table = 'bandara'
        managed = False

    def __str__(self):
        return f"{self.iata_code} - {self.nama}"


class Maskapai(models.Model):
    kode_maskapai = models.CharField(max_length=10, primary_key=True)
    nama_maskapai = models.CharField(max_length=100)
    id_penyedia = models.ForeignKey(
        'hadiah.Penyedia',
        on_delete=models.DO_NOTHING,
        db_column='id_penyedia',
        related_name='maskapai_list',
    )

    class Meta:
        db_table = 'maskapai'
        managed = False

    def __str__(self):
        return f"{self.kode_maskapai} - {self.nama_maskapai}"


class AwardMilesPackage(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    harga_paket = models.DecimalField(max_digits=15, decimal_places=2)
    jumlah_award_miles = models.IntegerField()

    class Meta:
        db_table = 'award_miles_package'
        managed = False

    def __str__(self):
        return self.id


class MemberAwardMilesPackage(models.Model):
    id_award_miles_package = models.ForeignKey(
        AwardMilesPackage,
        on_delete=models.DO_NOTHING,
        db_column='id_award_miles_package',
        related_name='member_purchases',
    )
    email_member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        db_column='email_member',
        related_name='award_miles_purchases',
    )
    timestamp = models.DateTimeField(primary_key=True)

    class Meta:
        db_table = 'member_award_miles_package'
        managed = False
        constraints = [
            models.UniqueConstraint(
                fields=['id_award_miles_package', 'email_member', 'timestamp'],
                name='pk_member_award_miles_package',
            )
        ]

    def __str__(self):
        return f"{self.email_member_id} - {self.id_award_miles_package_id}"


class Staf(models.Model):
    email = models.OneToOneField(
        Pengguna,
        primary_key=True,
        on_delete=models.DO_NOTHING,
        related_name='staf',
        db_column='email',
    )
    id_staf = models.CharField(max_length=20, unique=True)
    kode_maskapai = models.ForeignKey(
        Maskapai,
        on_delete=models.DO_NOTHING,
        db_column='kode_maskapai',
        related_name='staf_list',
    )

    class Meta:
        db_table = 'staf'
        managed = False

    def __str__(self):
        return self.id_staf


class Identitas(models.Model):
    JENIS_CHOICES = [
        ('Paspor', 'Paspor'),
        ('KTP', 'KTP'),
        ('SIM', 'SIM'),
    ]

    nomor = models.CharField(max_length=50, primary_key=True)
    email_member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        db_column='email_member',
        related_name='identitas_list',
    )
    tanggal_habis = models.DateField()
    tanggal_terbit = models.DateField()
    negara_penerbit = models.CharField(max_length=50)
    jenis = models.CharField(max_length=30, choices=JENIS_CHOICES)

    class Meta:
        db_table = 'identitas'
        managed = False

    def __str__(self):
        return f"{self.jenis} - {self.nomor}"


class Redeem(models.Model):
    email_member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        db_column='email_member',
        related_name='redeems',
    )
    kode_hadiah = models.ForeignKey(
        'hadiah.Hadiah',
        on_delete=models.DO_NOTHING,
        db_column='kode_hadiah',
        related_name='redeems',
    )
    timestamp = models.DateTimeField(primary_key=True)

    class Meta:
        db_table = 'redeem'
        managed = False
        constraints = [
            models.UniqueConstraint(
                fields=['email_member', 'kode_hadiah', 'timestamp'],
                name='pk_redeem',
            )
        ]

    def __str__(self):
        return f"{self.email_member_id} - {self.kode_hadiah_id}"
