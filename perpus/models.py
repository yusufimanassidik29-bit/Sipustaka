from django.db import models

# ==============================================================================
# 1. TABEL DATA ANGGOTA / SISWA
# ==============================================================================
class UserSiswa(models.Model):
    nama = models.CharField(max_length=100)
    kelas = models.CharField(max_length=20)
    nis = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=15, default='Aktif')

    class Meta:
        # Mengunci nama tabel di database agar sinkron dengan kueri Raw SQL
        db_table = 'perpus_usersiswa'


# ==============================================================================
# 2. TABEL DATA KOLEKSI BUKU
# ==============================================================================
class Buku(models.Model):
    judul = models.CharField(max_length=150)
    pengarang = models.CharField(max_length=100)
    kategori = models.CharField(max_length=50)
    penerbit = models.CharField(max_length=100, null=True, blank=True)
    tahun_terbit = models.IntegerField(default=2026)
    rak = models.CharField(max_length=20)
    stok = models.IntegerField(default=0)
    isbn = models.CharField(max_length=30, unique=True)
    deskripsi = models.TextField(null=True, blank=True)

    class Meta:
        # Mengunci nama tabel di database
        db_table = 'perpus_buku'


# ==============================================================================
# 3. TABEL TRANSAKSI PEMINJAMAN (MENGGUNAKAN RELASI FOREIGN KEY)
# ==============================================================================
class Peminjaman(models.Model):
    # Relasi Foreign Key ke tabel UserSiswa
    siswa = models.ForeignKey(UserSiswa, on_delete=models.CASCADE, db_column='siswa_id')
    
    # Relasi Foreign Key ke tabel Buku
    buku = models.ForeignKey(Buku, on_delete=models.CASCADE, db_column='buku_id')
    
    tanggal_pinjam = models.DateField(auto_now_add=True)
    tanggal_kembali = models.DateField(null=True, blank=True)
    status_pinjam = models.CharField(max_length=20, default='Dipinjam') # Status: Dipinjam / Kembali

    class Meta:
        # Mengunci nama tabel di database
        db_table = 'perpus_peminjaman'