import json, os
from pathlib import Path
from typing import Literal

import httpx, joblib, numpy as np, pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
bundle = joblib.load(BASE / "model" / "rf_harga_spk.joblib")
MODEL, COLUMNS = bundle["model"], bundle["columns"]
DAFTAR_MODEL = json.loads((BASE / "model" / "daftar_model.json").read_text(encoding="utf-8"))

app = FastAPI(title="Harga HP Bekas SPK")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class PredictIn(BaseModel):
    model: str
    ram_gb: int
    storage_gb: int
    asal_unit: Literal["Resmi SEIN / Indonesia", "Inter / Impor", "Resmi iBox / Digimap"]
    status_imei: Literal["Resmi Terdaftar", "Terdaftar Bea Cukai", "Simlok / Sinyal Blocked", "Bypass"]
    skala_kondisi_fisik: int = Field(ge=1, le=5)
    battery_health: int = Field(ge=50, le=100)
    riwayat_servis: str = "Original Normal"
    kelengkapan: Literal["Fullset Original", "Unit + Charger OEM", "Batangan"]
    garansi_aktif: int = Field(ge=0, le=1)
    harga_pasaran_medsos: int = Field(gt=0)


class ScrapeIn(BaseModel):
    model: str
    ram_gb: int | None = None
    storage_gb: int | None = None


def build_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["svc_lcd"] = d["riwayat_servis"].str.contains("LCD").astype(int)
    d["svc_bat"] = d["riwayat_servis"].str.contains("Baterai").astype(int)
    d["svc_hous"] = d["riwayat_servis"].str.contains("Housing").astype(int)
    d["svc_mesin"] = d["riwayat_servis"].str.contains("Mesin").astype(int)
    d["n_svc"] = d[["svc_lcd", "svc_bat", "svc_hous", "svc_mesin"]].sum(axis=1)
    num = ["ram_gb", "storage_gb", "skala_kondisi_fisik", "battery_health", "garansi_aktif",
           "harga_pasaran_medsos", "svc_lcd", "svc_bat", "svc_hous", "svc_mesin", "n_svc"]
    cat = ["model", "asal_unit", "status_imei", "kelengkapan"]
    return pd.get_dummies(d[num + cat], columns=cat)


@app.get("/api/meta")
def meta():
    return {"models": DAFTAR_MODEL}


@app.post("/api/predict")
def predict(body: PredictIn):
    if body.model not in DAFTAR_MODEL:
        raise HTTPException(422, f"Model '{body.model}' belum ada di data training.")
    X = build_features(pd.DataFrame([body.model_dump()])).reindex(columns=COLUMNS, fill_value=0)
    pasar = body.harga_pasaran_medsos
    rasio = float(MODEL.predict(X)[0])
    tree = np.array([t.predict(X.values)[0] for t in MODEL.estimators_]) * pasar
    r10 = lambda v: int(round(float(v), -4))
    return {
        "harga_rekomendasi": r10(rasio * pasar),
        "rentang_bawah": r10(np.percentile(tree, 10)),
        "rentang_atas": r10(np.percentile(tree, 90)),
        "rasio": round(rasio, 3),
        "selisih_persen": round((rasio - 1) * 100, 1),
    }


@app.post("/api/harga-pasaran")
def harga_pasaran(body: ScrapeIn):
    """Meneruskan permintaan ke webhook n8n lokal dan mengembalikan harga pasaran."""
    url = os.getenv("N8N_WEBHOOK_URL")
    if not url:
        raise HTTPException(503, "N8N_WEBHOOK_URL belum diatur. Lihat README langkah 4.")
    try:
        r = httpx.post(url, json=body.model_dump(), timeout=120)
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, ValueError) as e:
        raise HTTPException(502, f"n8n tidak merespons dengan benar: {e}")
    if isinstance(data, list):
        data = data[0] if data else {}
    harga = data.get("harga_pasaran")
    if not harga:
        raise HTTPException(502, "Respons n8n tidak berisi 'harga_pasaran'.")
    return {"harga_pasaran": int(harga), "jumlah_iklan": data.get("jumlah_iklan")}


app.mount("/", StaticFiles(directory=BASE / "static", html=True), name="static")
