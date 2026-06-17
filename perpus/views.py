from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from datetime import date, timedelta

# ==============================================================================
# 1. MODUL DASHBOARD
# ==============================================================================
def dashboard_view(request):
    with connection.cursor() as cursor:
        # 1. Hitung Total Seluruh Stok Fisik Buku
        cursor.execute("SELECT COALESCE(SUM(stok), 0) FROM perpus_buku")
        total_buku = cursor.fetchone()[0]

        # 2. Hitung Total Judul Buku yang Ada
        cursor.execute("SELECT COUNT(*) FROM perpus_buku")
        total_judul = cursor.fetchone()[0]

        # 3. Hitung Jumlah Transaksi yang Statusnya 'Dipinjam'
        cursor.execute("SELECT COUNT(*) FROM perpus_peminjaman WHERE LOWER(status_pinjam) = 'dipinjam'")
        sedang_dipinjam = cursor.fetchone()[0]

        # 4. Hitung Jumlah Transaksi yang Statusnya 'Dikembalikan'
        cursor.execute("SELECT COUNT(*) FROM perpus_peminjaman WHERE LOWER(status_pinjam) = 'dikembalikan'")
        sudah_dikembalikan = cursor.fetchone()[0]

        # 5. Ambil Daftar Buku untuk Grafik Distribusi Stok (Maksimal 5 Buku)
        cursor.execute("SELECT judul, stok FROM perpus_buku ORDER BY stok DESC LIMIT 5")
        buku_rows = cursor.fetchall()
        
        # Cari stok tertinggi untuk menghitung persentase lebar grafik batang (%)
        max_stok = max([row[1] for row in buku_rows]) if buku_rows else 1
        
        daftar_buku_grafik = []
        for row in buku_rows:
            judul_buku = row[0]
            stok_buku = row[1]
            # Menghitung persentase lebar bar (misal: stok 5 dari max 10 = 50%)
            persentase = int((stok_buku / max_stok) * 100)
            daftar_buku_grafik.append({
                'judul': judul_buku,
                'stok': stok_buku,
                'persentase': persentase
            })

    # Bungkus semua variabel ke dalam context untuk dikirim ke template HTML
    context = {
        'total_buku': total_buku,
        'total_judul': total_judul,
        'sedang_dipinjam': sedang_dipinjam,
        'sudah_dikembalikan': sudah_dikembalikan,
        'daftar_buku_grafik': daftar_buku_grafik,
    }
    return render(request, 'perpus/index.html', context)


# ==============================================================================
# 2. MODUL SISWA
# ==============================================================================
def users_view(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nama, kelas, nis, status FROM perpus_usersiswa ORDER BY id DESC")
        columns = [col[0] for col in cursor.description]
        data_siswa = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return render(request, 'perpus/users.html', {'data_siswa': data_siswa})

def add_user_view(request):
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        kelas = request.POST.get('kelas', '').strip()
        nis = request.POST.get('nis', '').strip()
        status = request.POST.get('status', 'Aktif')

        if not nama or not kelas or not nis:
            messages.error(request, "Gagal: Semua kolom wajib diisi!")
            return redirect('add_user')

        with connection.cursor() as cursor:
            # Menginput data siswa baru ke tabel database PostgreSQL
            cursor.execute(
                """
                INSERT INTO perpus_usersiswa (nama, kelas, nis, status) 
                VALUES (%s, %s, %s, %s)
                """,
                [nama, kelas, nis, status]
            )

        messages.success(request, f"Anggota baru bernama {nama} berhasil ditambahkan!")
        return redirect('users')

    return render(request, 'perpus/add-user.html')

def detail_user_view(request, user_id):
    with connection.cursor() as cursor:
        # Ambil data profil siswa
        cursor.execute("SELECT id, nama, kelas, nis, status FROM perpus_usersiswa WHERE id = %s", [user_id])
        row = cursor.fetchone()
        
        if not row:
            messages.error(request, "User tidak ditemukan!")
            return redirect('users')
            
        columns = [col[0] for col in cursor.description]
        user_data = dict(zip(columns, row))

        # Hitung total peminjaman sejarah (Total Peminjaman)
        cursor.execute("SELECT COUNT(*) FROM perpus_peminjaman WHERE siswa_id = %s", [user_id])
        total_peminjaman = cursor.fetchone()[0]

        # Hitung buku yang saat ini statusnya masih dipinjam (Peminjaman Aktif)
        cursor.execute("SELECT COUNT(*) FROM perpus_peminjaman WHERE siswa_id = %s AND LOWER(status_pinjam) = 'dipinjam'", [user_id])
        peminjaman_aktif = cursor.fetchone()[0]

    context = {
        'user': user_data,
        'total_peminjaman': total_peminjaman,
        'peminjaman_aktif': peminjaman_aktif,
    }
    return render(request, 'perpus/detail-user.html', context)


# 2. VIEW EDIT USER
def edit_user_view(request, user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, nama, kelas, nis, status FROM perpus_usersiswa WHERE id = %s", [user_id])
        row = cursor.fetchone()
        
        if not row:
            messages.error(request, "User tidak ditemukan!")
            return redirect('users')
            
        columns = [col[0] for col in cursor.description]
        user_data = dict(zip(columns, row))

    if request.method == 'POST':
        nama = request.POST.get('nama')
        kelas = request.POST.get('kelas')
        nis = request.POST.get('nis')
        status = request.POST.get('status')

        with connection.cursor() as cursor:
            # FIX: Sekarang urutan data sudah pas 5 parameter sesuai jumlah %s
            cursor.execute(
                "UPDATE perpus_usersiswa SET nama = %s, kelas = %s, nis = %s, status = %s WHERE id = %s",
                [nama, kelas, nis, status, user_id]
            )
        messages.success(request, "Data user berhasil diperbarui!")
        return redirect('users')

    return render(request, 'perpus/edit-user.html', {'user': user_data})


# 3. VIEW HAPUS USER
def hapus_user_view(request, user_id):
    with connection.cursor() as cursor:
        # Ambil data profil siswa untuk ditampilkan di halaman konfirmasi
        cursor.execute("SELECT id, nama, kelas, nis FROM perpus_usersiswa WHERE id = %s", [user_id])
        row = cursor.fetchone()
        
        if not row:
            messages.error(request, "User tidak ditemukan!")
            return redirect('users')
            
        columns = [col[0] for col in cursor.description]
        user_data = dict(zip(columns, row))

        # Cek apakah siswa masih punya pinjaman aktif (buku belum dikembalikan)
        cursor.execute("SELECT COUNT(*) FROM perpus_peminjaman WHERE siswa_id = %s AND LOWER(status_pinjam) = 'dipinjam'", [user_id])
        masih_pinjam = cursor.fetchone()[0]

    # JIKA TOMBOL "YA, HAPUS PERMANEN" DIKLIK (POST)
    if request.method == 'POST':
        if masih_pinjam > 0:
            messages.error(request, f"Gagal menghapus! {user_data['nama']} masih memiliki pinjaman buku yang aktif.")
            return redirect('users')
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM perpus_usersiswa WHERE id = %s", [user_id])
            
        messages.success(request, f"User {user_data['nama']} berhasil dihapus dari sistem!")
        return redirect('users')

    # JIKA BARU DIKLIK DARI HALAMAN DAFTAR USER (GET) -> TAMPILKAN HALAMAN PINDAH
    context = {
        'user': user_data,
        'masih_pinjam': masih_pinjam
    }
    return render(request, 'perpus/hapus-user.html', context)

# ==============================================================================
# 3. MODUL BUKU
# ==============================================================================
def buku_view(request):
    with connection.cursor() as cursor:
        # 💡 Pastikan ada kolom 'id' di awal query SELECT ini!
        cursor.execute("SELECT id, judul, pengarang, kategori, penerbit, tahun_terbit, rak, stok, isbn FROM perpus_buku ORDER BY id DESC")
        columns = [col[0] for col in cursor.description]
        data_buku = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'perpus/buku.html', {'data_buku': data_buku})

def add_buku_view(request):
    if request.method == 'POST':
        judul = request.POST.get('judul', '').strip()
        pengarang = request.POST.get('pengarang', '').strip()
        kategori = request.POST.get('kategori', '').strip()
        penerbit = request.POST.get('penerbit', '').strip()
        tahun_terbit = request.POST.get('tahun_terbit', '').strip()
        rak = request.POST.get('rak', '').strip()
        stok = request.POST.get('stok', '').strip()
        isbn = request.POST.get('isbn', '').strip()

        if not judul or not pengarang or not kategori or not rak or not stok or not isbn:
            messages.error(request, "Gagal: Kolom tanda bintang (*) wajib diisi!")
            return render(request, 'perpus/add-buku.html')

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM perpus_buku WHERE isbn = %s", [isbn])
            if cursor.fetchone()[0] > 0:
                messages.error(request, "Gagal: ISBN duplikat!")
                return render(request, 'perpus/add-buku.html')

            cursor.execute(
                """
                INSERT INTO perpus_buku (judul, pengarang, kategori, penerbit, tahun_terbit, rak, stok, isbn)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    judul, 
                    pengarang, 
                    kategori, 
                    penerbit, 
                    int(tahun_terbit) if tahun_terbit else 2026, 
                    rak, 
                    int(stok), 
                    isbn
                ]
            )
        messages.success(request, "Buku berhasil ditambah!")
        return redirect('buku')
    return render(request, 'perpus/add-buku.html')

def kembalikan_buku_view(request, pinjam_id):
    with connection.cursor() as cursor:
        # 1. Ambil data buku_id terlebih dahulu dari transaksi peminjaman ini
        cursor.execute("SELECT buku_id FROM perpus_peminjaman WHERE id = %s", [pinjam_id])
        row = cursor.fetchone()
        
        if row:
            buku_id = row[0]
            # 2. Update status peminjaman menjadi 'Dikembalikan'
            cursor.execute(
                "UPDATE perpus_peminjaman SET status_pinjam = 'Dikembalikan' WHERE id = %s", 
                [pinjam_id]
            )
            # 3. Kembalikan stok buku di database (tambah 1)
            cursor.execute("UPDATE perpus_buku SET stok = stok + 1 WHERE id = %s", [buku_id])
            
            messages.success(request, "Buku berhasil dikembalikan dan stok telah diperbarui!")
        else:
            messages.error(request, "Transaksi peminjaman tidak ditemukan!")
            
    return redirect('pinjam')


# ==============================================================================
# 4. MODUL TRANSAKSI PEMINJAMAN (RELASI FOREIGN KEY - RAW SQL MURNI)
# ==============================================================================

# A. LOG DAFTAR PEMINJAMAN (MENGGUNAKAN TEKNIK SQL INNER JOIN)
def pinjam_view(request):
    with connection.cursor() as cursor:
        # Menggunakan INNER JOIN murni untuk menyatukan data Peminjaman, Siswa, dan Buku
        cursor.execute("""
            SELECT 
                p.id, 
                s.nama AS nama_siswa, 
                b.judul AS judul_buku, 
                p.tanggal_pinjam, 
                p.status_pinjam
            FROM perpus_peminjaman p
            INNER JOIN perpus_usersiswa s ON p.siswa_id = s.id
            INNER JOIN perpus_buku b ON p.buku_id = b.id
            ORDER BY p.id ASC
        """)
        columns = [col[0] for col in cursor.description]
        raw_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Rekayasa data Jatuh Tempo (+7 hari) & Keperluan/Petugas dinamis sesuai gambar target
    import datetime
    data_peminjaman = []
    for item in raw_data:
        # Menghitung jatuh tempo otomatis 7 hari setelah tanggal pinjam
        if item['tanggal_pinjam']:
            jatuh_tempo = item['tanggal_pinjam'] + datetime.timedelta(days=7)
        else:
            jatuh_tempo = "-"

        data_peminjaman.append({
            'id': item['id'],
            'nama_siswa': item['nama_siswa'],
            'judul_buku': item['judul_buku'],
            'tanggal_pinjam': item['tanggal_pinjam'],
            'jatuh_tempo': jatuh_tempo,
            'keperluan': 'Tugas sekolah / Referensi bacaan' if item['id'] % 2 == 1 else 'Bacaan pribadi',
            'petugas': 'Budi Siregar', # Sesuai nama admin di gambar target
            'status_pinjam': item['status_pinjam']
        })

    return render(request, 'perpus/pinjam.html', {'data_peminjaman': data_peminjaman})


# B. PROSES VALIDASI INPUT TRANSAKSI BARU (STOK BUKU BERKURANG OTOMATIS)
def add_pinjam_view(request):
    with connection.cursor() as cursor:
        # Menarik data siswa Aktif untuk dropdown form
        cursor.execute("SELECT id, nama, kelas, nis FROM perpus_usersiswa WHERE status = 'Aktif'")
        siswa_cols = [col[0] for col in cursor.description]
        daftar_siswa = [dict(zip(siswa_cols, row)) for row in cursor.fetchall()]

        # Menarik data buku yang stoknya tersedia
        cursor.execute("SELECT id, judul, stok FROM perpus_buku WHERE stok > 0")
        buku_cols = [col[0] for col in cursor.description]
        daftar_buku = [dict(zip(buku_cols, row)) for row in cursor.fetchall()]

    # Set tanggal otomatis untuk kalender HTML
    tgl_sekarang = date.today().strftime('%Y-%m-%d')
    tgl_kembali = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')

    if request.method == 'POST':
        siswa_id = request.POST.get('siswa_id')
        buku_id = request.POST.get('buku_id')
        tanggal_pinjam = request.POST.get('tanggal_pinjam')

        with connection.cursor() as cursor:
            # 1. Catat transaksi baru ke database
            cursor.execute(
                "INSERT INTO perpus_peminjaman (siswa_id, buku_id, tanggal_pinjam, status_pinjam) VALUES (%s, %s, %s, 'Dipinjam')",
                [siswa_id, buku_id, tanggal_pinjam]
            )
            # 2. Potong stok buku sebanyak 1 unit
            cursor.execute("UPDATE perpus_buku SET stok = stok - 1 WHERE id = %s", [buku_id])

        messages.success(request, "Buku berhasil dipinjam!")
        return redirect('pinjam')

    context = {
        'daftar_siswa': daftar_siswa,
        'daftar_buku': daftar_buku,
        'tgl_pinjam': tgl_sekarang,
        'tgl_kembali': tgl_kembali,
    }
    return render(request, 'perpus/add-pinjam.html', context)


# C. PROSES PENGEMBALIAN BUKU (STOK BUKU KEMBALI BERTAMBAH +1)
def kembalikan_buku_view(request, pinjam_id):
    with connection.cursor() as cursor:
        # 1. Cari tahu buku apa yang dipinjam
        cursor.execute("SELECT buku_id FROM perpus_peminjaman WHERE id = %s", [pinjam_id])
        row = cursor.fetchone()
        
        if row:
            buku_id = row[0]
            # 2. Ubah status transaksi menjadi Dikembalikan
            cursor.execute("UPDATE perpus_peminjaman SET status_pinjam = 'Dikembalikan' WHERE id = %s", [pinjam_id])
            # 3. Pulangkan stok buku (tambah 1)
            cursor.execute("UPDATE perpus_buku SET stok = stok + 1 WHERE id = %s", [buku_id])
            messages.success(request, "Buku telah dikembalikan!")
        else:
            messages.error(request, "Data tidak ditemukan!")
            
    return redirect('pinjam')

# ==============================================================================
# FITUR TAMBAHAN MODUL BUKU: DETAIL, EDIT, HAPUS (RAW SQL MURNI)
# ==============================================================================

# 1. HALAMAN DETAIL BUKU
def detail_buku_view(request, buku_id):
    with connection.cursor() as cursor:
        # Mengambil satu data buku spesifik berdasarkan ID
        cursor.execute("SELECT id, judul, pengarang, kategori, penerbit, tahun_terbit, rak, stok, isbn, deskripsi FROM perpus_buku WHERE id = %s", [buku_id])
        row = cursor.fetchone()
        
        if not row:
            messages.error(request, "Buku tidak ditemukan!")
            return redirect('buku')
            
        columns = [col[0] for col in cursor.description]
        buku = dict(zip(columns, row))

    return render(request, 'perpus/detail-buku.html', {'buku': buku})


# 2. HALAMAN EDIT & PROSES UPDATE BUKU
def edit_buku_view(request, buku_id):
    with connection.cursor() as cursor:
        # Ambil data lama untuk ditampilkan di dalam form input
        cursor.execute("SELECT id, judul, pengarang, kategori, penerbit, tahun_terbit, rak, stok, isbn FROM perpus_buku WHERE id = %s", [buku_id])
        row = cursor.fetchone()
        
        if not row:
            messages.error(request, "Buku tidak ditemukan!")
            return redirect('buku')
            
        columns = [col[0] for col in cursor.description]
        buku = dict(zip(columns, row))

    if request.method == 'POST':
        judul = request.POST.get('judul', '').strip()
        pengarang = request.POST.get('pengarang', '').strip()
        kategori = request.POST.get('kategori', '').strip()
        penerbit = request.POST.get('penerbit', '').strip()
        tahun_terbit = request.POST.get('tahun_terbit', '').strip()
        rak = request.POST.get('rak', '').strip()
        stok = request.POST.get('stok', '').strip()
        isbn = request.POST.get('isbn', '').strip()

        with connection.cursor() as cursor:
            # Jalankan kueri UPDATE SQL manual ke PostgreSQL
            cursor.execute(
                """
                UPDATE perpus_buku 
                SET judul=%s, pengarang=%s, kategori=%s, penerbit=%s, tahun_terbit=%s, rak=%s, stok=%s, isbn=%s 
                WHERE id=%s
                """,
                [judul, pengarang, kategori, penerbit, int(tahun_terbit) if tahun_terbit else 2026, rak, int(stok), isbn, buku_id]
            )
        messages.success(request, f"Data buku '{judul}' berhasil diperbarui!")
        return redirect('buku')

    return render(request, 'perpus/edit-buku.html', {'buku': buku})


# 3. PROSES HAPUS BUKU (DELETE)
def hapus_buku_view(request, buku_id):
    if request.method == 'POST':
        with connection.cursor() as cursor:
            # Jalankan kueri DELETE SQL manual
            cursor.execute("DELETE FROM perpus_buku WHERE id = %s", [buku_id])
            
        messages.success(request, "Buku berhasil dihapus dari sistem!")
    return redirect('buku')

