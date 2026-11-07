# Menjalankan dengan Docker

Butuh Docker Desktop (Windows/macOS) atau Docker Engine + Compose (Linux). Tidak perlu Python atau Node.js.

1. Salin `.env.example` menjadi `.env`, lalu isi `APIFY_TOKEN=` dengan token dari apify.com
   (Settings → API & Integrations). Tulis token saja, tanpa kata "Bearer".
2. Jalankan dari folder proyek:
   ```
   docker compose up -d --build
   ```
3. Buka http://localhost:5678 dan buat akun owner n8n (hanya pertama kali). Simpan emailnya.
   Cek menu Workflows: "Harga pasaran HP (Facebook via Apify)" harus sudah ada dan berstatus aktif.
   Kalau belum ada atau belum aktif, import `n8n/workflow_facebook_apify.json` secara manual,
   ganti `GANTI_DENGAN_TOKEN_APIFY` di node HTTP Request dengan tokenmu, lalu aktifkan.
4. Buka website di http://localhost:8000.

Perintah berguna:
- Lihat log: `docker compose logs -f` (atau `docker compose logs n8n`)
- Hentikan: `docker compose down` (data n8n tetap tersimpan)
- Mulai ulang dari nol, termasuk akun dan workflow n8n: `docker compose down -v`
- Ganti token Apify: ubah `.env`, lalu `docker compose down -v` dan `docker compose up -d --build`

## Membagikan ke teman
- Zip folder proyek **tanpa** `.env`, `venv`, dan `__pycache__`. File `.env` berisi tokenmu.
- Tiap teman memakai token Apify-nya sendiri (akun gratis cukup), supaya saldo tidak habis bersama.
- Versi scikit-learn di `requirements.txt` harus sama dengan versi yang melatih file `.joblib`
  (cek di Colab: `import sklearn; print(sklearn.__version__)`), mis. `scikit-learn==1.5.2`.
- Jika image `n8nio/n8n:2.46.6` tidak ditemukan, ganti tagnya jadi `latest` di `docker-compose.yml`.
