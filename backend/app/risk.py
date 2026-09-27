"""Nitel risk değerlendirmesi: skorlama, 5x5 matris, önceliklendirme."""
from __future__ import annotations

from typing import Dict, List

from .modeller import Proje, Risk

# 5x5 matris eşikleri
OLASILIK_ESIKLERI = [
    (0.10, 1, "Çok Düşük"),
    (0.30, 2, "Düşük"),
    (0.50, 3, "Orta"),
    (0.70, 4, "Yüksek"),
    (1.01, 5, "Çok Yüksek"),
]

# Etki seviyesi, projenin baz maliyetine göre oransal belirlenir
ETKI_ORANLARI = [
    (0.01, 1, "Çok Düşük"),
    (0.03, 2, "Düşük"),
    (0.07, 3, "Orta"),
    (0.15, 4, "Yüksek"),
    (float("inf"), 5, "Çok Yüksek"),
]

SEVIYE_RENKLERI = {
    "Düşük": "#2e9e63",
    "Orta": "#e0a800",
    "Yüksek": "#e2711d",
    "Kritik": "#c0392b",
}


def olasilik_seviyesi(olasilik: float) -> tuple[int, str]:
    for esik, seviye, etiket in OLASILIK_ESIKLERI:
        if olasilik < esik:
            return seviye, etiket
    return 5, "Çok Yüksek"


def etki_seviyesi(etki_tutari: float, baz_maliyet: float) -> tuple[int, str]:
    if baz_maliyet <= 0:
        # Baz maliyet yoksa mutlak eşiklerle çalış
        baz_maliyet = max(etki_tutari, 1.0) * 10
    oran = etki_tutari / baz_maliyet
    for esik, seviye, etiket in ETKI_ORANLARI:
        if oran < esik:
            return seviye, etiket
    return 5, "Çok Yüksek"


def matris_derecesi(skor: int) -> str:
    """5x5 matriste olasılık*etki çarpımına göre derece."""
    if skor <= 4:
        return "Düşük"
    if skor <= 9:
        return "Orta"
    if skor <= 15:
        return "Yüksek"
    return "Kritik"


def risk_degerlendir(risk: Risk, baz_maliyet: float) -> Dict:
    o_sev, o_etiket = olasilik_seviyesi(risk.olasilik)
    beklenen_maliyet = risk.maliyet_etkisi.beklenen_deger
    beklenen_sure = risk.sure_etkisi.beklenen_deger
    e_sev, e_etiket = etki_seviyesi(beklenen_maliyet, baz_maliyet)
    skor = o_sev * e_sev
    emd = risk.olasilik * beklenen_maliyet  # Beklenen Parasal Değer (EMV)
    isaret = -1 if risk.tur == "Fırsat" else 1

    # Önlem sonrası
    o_son = risk.etkin_olasilik(True)
    e_son = beklenen_maliyet * risk.etki_carpani(True)
    emd_son = o_son * e_son
    fayda = emd - emd_son - risk.onlem_maliyeti

    return {
        "kod": risk.kod,
        "ad": risk.ad,
        "kategori": risk.kategori,
        "tur": risk.tur,
        "olasilik": risk.olasilik,
        "olasilik_seviyesi": o_sev,
        "olasilik_etiketi": o_etiket,
        "beklenen_maliyet_etkisi": beklenen_maliyet,
        "beklenen_sure_etkisi": beklenen_sure,
        "etki_seviyesi": e_sev,
        "etki_etiketi": e_etiket,
        "skor": skor,
        "derece": matris_derecesi(skor),
        "renk": SEVIYE_RENKLERI[matris_derecesi(skor)],
        "beklenen_parasal_deger": isaret * emd,
        "onlem_sonrasi_bpd": isaret * emd_son,
        "onlem_maliyeti": risk.onlem_maliyeti,
        "onlem_net_faydasi": fayda,
        "strateji": risk.strateji,
        "sorumlu": risk.sorumlu,
        "durum": risk.durum,
    }


def matris_olustur(degerlendirmeler: List[Dict]) -> List[List[Dict]]:
    """5x5 ısı haritası: satır = etki (5..1), sütun = olasılık (1..5)."""
    hucreler = []
    for etki in range(5, 0, -1):
        satir = []
        for olasilik in range(1, 6):
            skor = etki * olasilik
            icindekiler = [
                d["kod"]
                for d in degerlendirmeler
                if d["etki_seviyesi"] == etki and d["olasilik_seviyesi"] == olasilik
            ]
            derece = matris_derecesi(skor)
            satir.append(
                {
                    "etki": etki,
                    "olasilik": olasilik,
                    "skor": skor,
                    "derece": derece,
                    "renk": SEVIYE_RENKLERI[derece],
                    "riskler": icindekiler,
                }
            )
        hucreler.append(satir)
    return hucreler


def proje_degerlendir(proje: Proje) -> Dict:
    baz = proje.baz_maliyet.beklenen_deger
    degerlendirmeler = [risk_degerlendir(r, baz) for r in proje.riskler]
    degerlendirmeler.sort(key=lambda d: (-d["skor"], -abs(d["beklenen_parasal_deger"])))

    tehditler = [d for d in degerlendirmeler if d["tur"] == "Tehdit"]
    firsatlar = [d for d in degerlendirmeler if d["tur"] == "Fırsat"]

    ozet = {
        "risk_sayisi": len(degerlendirmeler),
        "tehdit_sayisi": len(tehditler),
        "firsat_sayisi": len(firsatlar),
        "kritik_sayisi": sum(1 for d in degerlendirmeler if d["derece"] == "Kritik"),
        "yuksek_sayisi": sum(1 for d in degerlendirmeler if d["derece"] == "Yüksek"),
        "toplam_bpd": sum(d["beklenen_parasal_deger"] for d in degerlendirmeler),
        "onlem_sonrasi_toplam_bpd": sum(
            d["onlem_sonrasi_bpd"] for d in degerlendirmeler
        ),
        "toplam_onlem_maliyeti": sum(d["onlem_maliyeti"] for d in degerlendirmeler),
        "baz_maliyet": baz,
        "baz_sure": proje.baz_sure.beklenen_deger,
    }
    ozet["onlem_net_faydasi"] = (
        ozet["toplam_bpd"]
        - ozet["onlem_sonrasi_toplam_bpd"]
        - ozet["toplam_onlem_maliyeti"]
    )

    kategori_dagilimi: Dict[str, Dict[str, float]] = {}
    for d in degerlendirmeler:
        k = kategori_dagilimi.setdefault(
            d["kategori"], {"adet": 0, "bpd": 0.0, "skor": 0}
        )
        k["adet"] += 1
        k["bpd"] += d["beklenen_parasal_deger"]
        k["skor"] += d["skor"]

    return {
        "ozet": ozet,
        "riskler": degerlendirmeler,
        "matris": matris_olustur(degerlendirmeler),
        "kategori_dagilimi": kategori_dagilimi,
    }
