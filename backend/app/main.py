"""FastAPI uygulaması: Olasılık ve Risk Analizi Programı."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import depo, risk as risk_modulu, simulasyon
from .modeller import (
    DURUMLAR,
    KATEGORILER,
    STRATEJILER,
    Proje,
    SimulasyonIstegi,
)

KOK = Path(__file__).resolve().parents[2]
ONYUZ = KOK / "frontend"

uygulama = FastAPI(
    title="Olasılık ve Risk Analizi Programı",
    description="Proje riskleri için nitel matris ve Monte Carlo nicel analizi.",
    version="0.1.0",
)

uygulama.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@uygulama.get("/api/saglik")
def saglik():
    return {"durum": "çalışıyor"}


@uygulama.get("/api/sabitler")
def sabitler():
    return {
        "kategoriler": KATEGORILER,
        "durumlar": DURUMLAR,
        "stratejiler": STRATEJILER,
    }


@uygulama.post("/api/degerlendirme")
def degerlendirme(proje: Proje):
    """Nitel değerlendirme: skor, 5x5 matris, BPD (EMV)."""
    return risk_modulu.proje_degerlendir(proje)


@uygulama.post("/api/simulasyon")
def simulasyon_calistir(istek: SimulasyonIstegi):
    """Monte Carlo simülasyonu."""
    try:
        return simulasyon.calistir(istek.proje, istek.ayarlar)
    except Exception as hata:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(hata))


@uygulama.post("/api/analiz")
def tam_analiz(istek: SimulasyonIstegi):
    """Nitel + nicel analizi tek çağrıda döndürür."""
    return {
        "degerlendirme": risk_modulu.proje_degerlendir(istek.proje),
        "simulasyon": simulasyon.calistir(istek.proje, istek.ayarlar),
    }


@uygulama.get("/api/projeler")
def projeler():
    return depo.listele()


@uygulama.post("/api/projeler")
def proje_kaydet(proje: Proje):
    yol = depo.kaydet(proje)
    return {"mesaj": f"'{proje.ad}' kaydedildi.", "dosya": yol.name}


@uygulama.get("/api/projeler/{ad}")
def proje_getir(ad: str):
    try:
        return depo.yukle(ad)
    except FileNotFoundError as hata:
        raise HTTPException(status_code=404, detail=str(hata))


@uygulama.delete("/api/projeler/{ad}")
def proje_sil(ad: str):
    if not depo.sil(ad):
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    return {"mesaj": f"'{ad}' silindi."}


@uygulama.post("/api/disa-aktar/csv")
def csv_disa_aktar(proje: Proje):
    sonuc = risk_modulu.proje_degerlendir(proje)
    tampon = io.StringIO()
    yazici = csv.writer(tampon, delimiter=";")
    yazici.writerow(
        [
            "Kod",
            "Ad",
            "Kategori",
            "Tür",
            "Olasılık",
            "Olasılık Sev.",
            "Beklenen Maliyet Etkisi",
            "Etki Sev.",
            "Skor",
            "Derece",
            "Beklenen Parasal Değer",
            "Strateji",
            "Sorumlu",
            "Durum",
        ]
    )
    for r in sonuc["riskler"]:
        yazici.writerow(
            [
                r["kod"],
                r["ad"],
                r["kategori"],
                r["tur"],
                f"{r['olasilik']:.2f}",
                r["olasilik_seviyesi"],
                f"{r['beklenen_maliyet_etkisi']:.2f}",
                r["etki_seviyesi"],
                r["skor"],
                r["derece"],
                f"{r['beklenen_parasal_deger']:.2f}",
                r["strateji"],
                r["sorumlu"],
                r["durum"],
            ]
        )
    tampon.seek(0)
    return StreamingResponse(
        iter(["\ufeff" + tampon.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="risk_kaydi.csv"'},
    )


if ONYUZ.exists():
    uygulama.mount("/statik", StaticFiles(directory=ONYUZ), name="statik")

    @uygulama.get("/")
    def anasayfa():
        return FileResponse(ONYUZ / "index.html")
