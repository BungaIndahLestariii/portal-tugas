# Portal Tugas — Vercel

Versi ini memindahkan Portal Tugas ke Vercel. Antarmuka tetap memakai desain soft pink dan daftar mata kuliah dari file sebelumnya. Data tugas disimpan di PostgreSQL (Neon), sedangkan lampiran diunggah langsung ke Vercel Blob.

## Isi folder

```text
portal-tugas-vercel/
├── app.py                 # Flask API + halaman utama
├── index.html             # Tampilan Portal Tugas
├── requirements.txt       # Paket Python
├── vercel.json            # Pengaturan fungsi Vercel
├── package.json           # Paket JavaScript untuk Blob
├── .env.example           # Contoh variabel rahasia
├── .gitignore
├── README.md
└── api/
    └── blob-upload.js     # Endpoint token unggah langsung ke Blob
```

## Sebelum deploy

Aplikasi memerlukan dua layanan penyimpanan:

1. **Neon PostgreSQL** untuk menyimpan data daftar tugas dan materi.
2. **Vercel Blob** untuk menyimpan file lampiran.

Keduanya diperlukan supaya data dan lampiran tidak hilang saat aplikasi di-deploy ulang. Jangan menyimpan file unggahan di folder proyek Vercel.

### 1. Buat database Neon

1. Buka https://neon.tech/ lalu buat akun dan project PostgreSQL.
2. Di halaman project Neon, salin connection string PostgreSQL.
3. Pastikan connection string menggunakan SSL (`sslmode=require`).
4. Nanti masukkan string tersebut sebagai `DATABASE_URL` di Vercel.

Tabel `portal_data` akan dibuat otomatis oleh `app.py` saat aplikasi pertama kali mengakses database. Tidak perlu menjalankan SQL secara manual.

### 2. Buat Vercel Blob

1. Buka https://vercel.com/dashboard dan pilih project Portal Tugas.
2. Buka menu **Storage**.
3. Pilih **Create Database** lalu pilih **Blob**.
4. Buat Blob Store dan hubungkan ke project Portal Tugas.
5. Pastikan environment variable `BLOB_READ_WRITE_TOKEN` dibuat untuk project tersebut.

**Catatan privasi:** contoh ini menggunakan akses Blob `public` agar tautan lampiran bisa dibuka langsung dari daftar tugas. Artinya, siapa pun yang memperoleh URL file dapat membukanya. Jangan unggah dokumen yang sangat rahasia. Login aplikasi tetap diperlukan untuk melihat dan mengubah daftar tugas, tetapi URL file publik bukan pengganti izin akses file privat.

### 3. Atur Environment Variables di Vercel

Buka **Project → Settings → Environment Variables**, lalu tambahkan:

| Nama | Isi |
|---|---|
| `PORTAL_USERNAME` | `BungaIndahLestari` atau username pilihanmu |
| `PORTAL_PASSWORD` | Buat password baru yang kuat |
| `SECRET_KEY` | String acak panjang minimal 32 karakter |
| `DATABASE_URL` | Connection string Neon PostgreSQL |
| `BLOB_READ_WRITE_TOKEN` | Dibuat otomatis saat Blob Store dihubungkan; pastikan tersedia |

Contoh membuat `SECRET_KEY` di komputer:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Jangan unggah file `.env` yang berisi password atau token ke GitHub. File `.env.example` hanya contoh nama variabel dan bukan tempat menyimpan rahasia asli.

### 4. Deploy ke Vercel

1. Buat repository GitHub baru, misalnya `portal-tugas`.
2. Upload seluruh isi folder ini ke bagian paling atas/root repository. Jangan upload folder luarnya sebagai satu folder bertingkat.
3. Buka https://vercel.com/new lalu pilih **Import Git Repository**.
4. Pilih repository `portal-tugas`.
5. Biarkan pengaturan build default; Vercel akan mendeteksi Flask/Python dan fungsi JavaScript.
6. Pastikan semua Environment Variables pada langkah 3 sudah dimasukkan.
7. Klik **Deploy**.
8. Setelah deploy selesai, buka alamat website Vercel.

Jika baru menambahkan atau mengubah Environment Variables, lakukan **Redeploy** agar variabel tersebut terbaca oleh deployment baru.

## Login

Gunakan username dan password yang kamu masukkan pada `PORTAL_USERNAME` dan `PORTAL_PASSWORD` di Vercel. Password tidak ditulis di `index.html`.

## Cara kerja penyimpanan

- Tugas, materi, deadline, status selesai, dan URL lampiran disimpan dalam satu baris JSONB di Neon.
- File lampiran dikirim langsung dari browser ke Vercel Blob; file tidak melewati fungsi Python sehingga menghindari batas request body fungsi Vercel sebesar 4.5 MB.
- Batas ukuran yang diminta aplikasi adalah 1 GB per file. Penerimaan aktual tetap bergantung pada batas dan ketentuan akun/layanan Blob yang berlaku.
- Data tetap ada setelah redeploy selama database Neon dan Blob Store yang sama tidak dihapus.

## Penting tentang data lama

Data yang sebelumnya tersimpan hanya di browser (`localStorage`) atau di folder upload server Flask lama **tidak otomatis dipindahkan** ke Neon dan Blob. Sebelum beralih, simpan/cadangkan data lama dan file lampirannya. Lampiran yang sudah ada di server lama perlu diunggah ulang ke Blob agar tautannya tetap berfungsi.

## Menjalankan lokal (opsional)

1. Buat virtual environment dan install dependensi:

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Atur environment variables sesuai `.env.example` melalui terminal atau gunakan Vercel CLI (`vercel env pull`).
3. Untuk pengujian yang mendekati deployment, install Vercel CLI lalu jalankan:

```bash
npm install
npx vercel dev
```

Upload Blob lokal memerlukan endpoint publik/callback Vercel; pengujian upload sebaiknya dilakukan setelah deploy preview.

## Troubleshooting

- **Login tidak berhasil:** periksa `PORTAL_USERNAME`, `PORTAL_PASSWORD`, dan `SECRET_KEY` di Vercel. Pastikan deployment sudah di-redeploy.
- **Data tidak bisa dimuat/disimpan:** periksa `DATABASE_URL`, status Neon, dan log fungsi Python di Vercel.
- **Unggah file gagal:** periksa `BLOB_READ_WRITE_TOKEN`, pastikan Blob Store terhubung ke project yang benar, dan cek batas ukuran/jenis file.
- **File lama tidak terbuka:** file tersebut mungkin masih menunjuk ke lokasi penyimpanan server lama; unggah ulang ke Blob.

## Referensi resmi

- Flask di Vercel: https://vercel.com/docs/frameworks/backend/flask
- Vercel Blob client uploads: https://vercel.com/docs/vercel-blob/client-upload
- Environment Variables Vercel: https://vercel.com/docs/environment-variables
- Neon: https://neon.tech/docs
