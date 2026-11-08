# Taksir Harga HP Bekas

Website + API untuk model Random Forest. Harga pasaran bisa diambil otomatis dari Facebook Marketplace lewat n8n dan Apify.

```
Browser ──► FastAPI (:8000) ──► model .joblib
                 └──► n8n (:5678) ──► Apify ──► Facebook Marketplace
```

## Isi folder
- `backend/main.py` : API (`/api/predict`, `/api/harga-pasaran`, `/api/meta`) sekaligus penyaji website
- `static/index.html` : tampilan website
- `model/` : `rf_harga_spk.joblib` dan `daftar_model.json`
- `n8n/workflow_facebook_apify.json` : workflow n8n (Webhook → Apify → filter → balasan)
- `n8n/entrypoint.sh` : mengimpor dan mempublish workflow otomatis saat Docker pertama kali jalan
- `Dockerfile`, `docker-compose.yml`, `.env.example` : untuk menjalankan dengan Docker

## Sebelum mulai (sekali saja)
1. Buka `requirements.txt` dan kunci versi scikit-learn sesuai versi yang melatih modelmu, misalnya `scikit-learn==1.9.1`.
   Cek di Colab: `import sklearn; print(sklearn.__version__)`. Versi yang berbeda bisa membuat model gagal dimuat.
2. Daftar di apify.com (gratis, tanpa kartu kredit), lalu ambil API token di Settings → API & Integrations.
3. Pastikan di `backend/main.py` fungsi `harga_pasaran` memakai `timeout=300`.

## Cara 1: Docker (disarankan)
Butuh Docker Desktop (Windows/macOS) atau Docker Engine dengan Compose (Linux). Tidak perlu Python atau Node.js.

1. Salin `.env.example` menjadi `.env`, lalu isi `APIFY_TOKEN=` dengan tokennya (token saja, tanpa kata "Bearer").
2. Jalankan:
   ```
   docker compose up -d --build
   ```
3. Cek log n8n dan cari tulisan "Workflow berhasil diimpor dan dipublish":
   ```
   docker compose logs n8n
   ```
4. Buka http://localhost:5678, buat akun owner n8n (hanya pertama kali, catat emailnya), lalu pastikan workflow
   "Harga pasaran HP (Facebook via Apify)" ada di menu Workflows dan berstatus aktif.
   Kalau belum ada atau belum aktif, import `n8n/workflow_facebook_apify.json` secara manual,
   ganti `GANTI_DENGAN_TOKEN_APIFY` di node HTTP Request dengan tokenmu, lalu aktifkan.
5. Buka website di http://localhost:8000.

Perintah berguna:
- Lihat log: `docker compose logs -f`
- Hentikan: `docker compose down` (akun dan workflow n8n tetap tersimpan)
- Mulai dari nol, seperti di laptop baru: `docker compose down -v`, lalu `docker compose up -d --build`
- Ganti token Apify: ubah `.env`, lalu `docker compose down -v` dan `docker compose up -d --build`

Port 5678 dan 8000 harus kosong. Hentikan dulu n8n atau uvicorn yang berjalan di luar Docker (`Ctrl+C`).
Di Linux, tambahkan `sudo` di depan perintah `docker` jika muncul "permission denied".

## Cara 2: Tanpa Docker
Butuh Python 3.10+ dan Node.js.

1. Siapkan Python:
   ```
   python3 -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Jalankan n8n: `npx n8n`, buka http://localhost:5678, dan buat akun owner.
3. Import `n8n/workflow_facebook_apify.json` (menu ⋯ → Import from file). Di node HTTP Request, ganti
   `GANTI_DENGAN_TOKEN_APIFY` dengan tokenmu (format `Bearer <token>`), lalu aktifkan workflow (toggle Active).
4. Di terminal baru, jalankan dua perintah ini **terpisah** (jangan digabung dalam satu baris):
   ```
   export N8N_WEBHOOK_URL=http://localhost:5678/webhook/harga-pasaran
   uvicorn backend.main:app --reload --port 8000
   ```
   Di PowerShell Windows, gunakan `$env:N8N_WEBHOOK_URL="http://localhost:5678/webhook/harga-pasaran"`.
5. Buka http://localhost:8000.

## Cara kerja pengambilan harga pasaran
Tombol "Ambil dari medsos" memanggil backend, lalu backend memanggil webhook n8n dengan data:
```json
{"model": "Vivo V29", "ram_gb": 8, "storage_gb": 256}
```
n8n mencari iklan di Marketplace lewat Apify (10 iklan), membuang iklan yang tidak sesuai
(terjual, harga di bawah Rp 500 ribu, varian atau kapasitas berbeda, aksesoris, pencilan), lalu membalas:
```json
{"harga_pasaran": 3400000, "jumlah_iklan": 5}
```
Harga pasaran adalah median iklan yang lolos. Setiap klik tombol memakai saldo Apify (akun gratis: $5 per bulan,
sekitar $0,10 per pencarian 20 iklan), jadi pakai seperlunya. Harga juga bisa diketik manual.

Ubah kota di URL pada node HTTP Request (`.../marketplace/jakarta/search/...`) untuk memakai kota lain.

## Masalah umum
- **"N8N_WEBHOOK_URL belum diatur"** (Cara 2): variabel belum di-set di terminal yang sama dengan uvicorn.
- **n8n 404**: workflow belum aktif, atau memakai alamat `webhook-test` (hanya hidup saat "Listen for test event" ditekan).
- **"Error in workflow"**: buka tab Executions di n8n dan baca pesan node yang merah.
- **401 / "token not provided"** dari Apify: token salah, tidak terisi, atau formatnya bukan `Bearer <token>` (di node, bukan di `.env`).
- **"Apify tidak mengembalikan iklan"** atau **"Tidak ada iklan valid"**: kata kunci tidak menemukan iklan yang cocok. Coba model lain atau isi harga manual.
- **"Model ... belum ada di data training"**: hanya model di `daftar_model.json` yang bisa ditaksir. Tambah datanya lalu latih ulang di Colab.
- **Lupa akun n8n**: Docker: `docker compose down -v` lalu jalankan lagi. Tanpa Docker: hentikan n8n, lalu `npx n8n user-management:reset`.