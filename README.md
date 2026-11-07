# Taksir Harga HP Bekas

Website + API untuk model Random Forest, dengan harga pasaran yang bisa diambil dari n8n lokal.

```
Browser ──► FastAPI (localhost:8000) ──► model .joblib
                 └──► n8n lokal (localhost:5678) ──► scraping medsos
```

## Isi folder
- `backend/main.py` : API (`/api/predict`, `/api/harga-pasaran`, `/api/meta`) sekaligus penyaji website
- `static/index.html` : tampilan website
- `model/` : `rf_harga_spk.joblib` dan `daftar_model.json`
- `n8n/workflow_stub.json` : workflow contoh (harga palsu) untuk tes koneksi

## 1. Siapkan Python
Butuh Python 3.10+. Dari dalam folder proyek:

Windows:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
macOS / Linux:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Pakai model hasil Colab
Folder `model/` sudah berisi file dari hasil download dari Colab.

Versi scikit-learn lokal harus sama dengan di Colab. Cek di Colab:
```python
import sklearn; print(sklearn.__version__)
```
lalu pasang di laptop: `pip install scikit-learn==<versi tadi>`.

## 3. Jalankan website
```
uvicorn backend.main:app --reload --port 8000
```
Buka http://localhost:8000. Tanpa n8n pun, formulir dan tombol "Hitung" sudah bekerja (harga pasaran diisi manual).

## 4. Hubungkan n8n lokal
1. Jalankan n8n: `npx n8n` (butuh Node.js) atau `docker run -it --rm -p 5678:5678 n8nio/n8n`. Buka http://localhost:5678.
2. Import `n8n/workflow_stub.json` (menu ⋯ → Import from file), lalu aktifkan workflow (toggle Active).
3. Set alamat webhook sebelum menjalankan uvicorn:
   - Windows (PowerShell): `$env:N8N_WEBHOOK_URL="http://localhost:5678/webhook/harga-pasaran"`
   - macOS / Linux: `export N8N_WEBHOOK_URL=http://localhost:5678/webhook/harga-pasaran
   uvicorn backend.main:app --reload --port 8000`
4. Restart uvicorn, pilih model, tekan "Ambil dari medsos".

Alamat `/webhook/...` hanya hidup kalau workflow aktif. Alamat `/webhook-test/...` hanya hidup saat kamu menekan "Listen for test event" di n8n.

## Kontrak data n8n
Backend mengirim `POST` JSON:
```json
{"model": "Vivo V29", "ram_gb": 8, "storage_gb": 256}
```
Isi node Webhook ada di `$input.first().json.body`. Workflow harus membalas:
```json
{"harga_pasaran": 4500000, "jumlah_iklan": 12}
```
`harga_pasaran` wajib. Saran: ambil median dari beberapa iklan, bukan rata-rata, supaya tidak terpengaruh iklan yang terlalu murah atau mahal.
Ganti node "Hitung harga pasaran" dengan alur scraping aslimu setelah platform-nya ditentukan.

## Masalah umum
- "N8N_WEBHOOK_URL belum diatur": variabel belum di-set di terminal yang sama dengan uvicorn.
- n8n 404 : workflow belum aktif, atau memakai alamat `webhook-test`.
- "Model ... belum ada di data training": hanya model di `daftar_model.json` yang bisa ditaksir. Tambah datanya lalu latih ulang di Colab.
