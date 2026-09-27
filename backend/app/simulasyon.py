"""Monte Carlo risk simülasyonu (Beta-PERT + Bernoulli + Gauss kopula)."""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .modeller import Proje, SimulasyonAyarlari, UcNoktaliTahmin

LAMBDA = 4.0  # PERT şekil parametresi


def pert_ornekle(
    t: UcNoktaliTahmin, n: int, rng: np.random.Generator, u: np.ndarray | None = None
) -> np.ndarray:
    """Beta-PERT dağılımından n örnek. u verilirse ters DF ile kopula desteklenir."""
    a, m, b = float(t.iyimser), float(t.en_olasi), float(t.kotumser)
    if b <= a:
        return np.full(n, a, dtype=float)
    alfa = 1 + LAMBDA * (m - a) / (b - a)
    beta = 1 + LAMBDA * (b - m) / (b - a)
    ornek = rng.beta(alfa, beta, n) if u is None else _beta_ppf(u, alfa, beta)
    return a + ornek * (b - a)


def _beta_ppf(u: np.ndarray, alfa: float, beta: float) -> np.ndarray:
    """SciPy'siz Beta ters dağılım fonksiyonu (ikili arama, vektörel)."""
    alt = np.zeros_like(u)
    ust = np.ones_like(u)
    for _ in range(40):
        orta = (alt + ust) / 2
        cdf = _beta_cdf(orta, alfa, beta)
        buyuk = cdf > u
        ust = np.where(buyuk, orta, ust)
        alt = np.where(buyuk, alt, orta)
    return (alt + ust) / 2


def _beta_cdf(x: np.ndarray, alfa: float, beta: float) -> np.ndarray:
    """Düzenli tamamlanmamış beta fonksiyonu (sürekli kesir açılımı)."""
    from math import lgamma

    x = np.clip(x, 1e-12, 1 - 1e-12)
    lnbeta = lgamma(alfa) + lgamma(beta) - lgamma(alfa + beta)
    ln_on = alfa * np.log(x) + beta * np.log(1 - x) - lnbeta

    def kesir(xx, a, b):
        eps = 1e-30
        c = np.ones_like(xx)
        d = 1 - (a + b) * xx / (a + 1)
        d = np.where(np.abs(d) < eps, eps, d)
        d = 1 / d
        h = d.copy()
        for m in range(1, 200):
            m2 = 2 * m
            aa = m * (b - m) * xx / ((a + m2 - 1) * (a + m2))
            d = 1 + aa * d
            d = np.where(np.abs(d) < eps, eps, d)
            c = 1 + aa / c
            c = np.where(np.abs(c) < eps, eps, c)
            d = 1 / d
            h *= d * c
            aa = -(a + m) * (a + b + m) * xx / ((a + m2) * (a + m2 + 1))
            d = 1 + aa * d
            d = np.where(np.abs(d) < eps, eps, d)
            c = 1 + aa / c
            c = np.where(np.abs(c) < eps, eps, c)
            d = 1 / d
            delta = d * c
            h *= delta
            if np.all(np.abs(delta - 1) < 1e-10):
                break
        return h

    esik = (alfa + 1) / (alfa + beta + 2)
    sonuc = np.empty_like(x)
    sol = x < esik
    if np.any(sol):
        sonuc[sol] = np.exp(ln_on[sol]) * kesir(x[sol], alfa, beta) / alfa
    sag = ~sol
    if np.any(sag):
        lnb = beta * np.log(1 - x[sag]) + alfa * np.log(x[sag]) - lnbeta
        sonuc[sag] = 1 - np.exp(lnb) * kesir(1 - x[sag], beta, alfa) / beta
    return np.clip(sonuc, 0, 1)


def _pert_kopula(t: UcNoktaliTahmin, u: np.ndarray) -> np.ndarray:
    a, m, b = float(t.iyimser), float(t.en_olasi), float(t.kotumser)
    if b <= a:
        return np.full(u.shape, a, dtype=float)
    alfa = 1 + LAMBDA * (m - a) / (b - a)
    beta = 1 + LAMBDA * (b - m) / (b - a)
    return a + _beta_ppf(u, alfa, beta) * (b - a)


def _norm_cdf(z: np.ndarray) -> np.ndarray:
    from math import sqrt

    from numpy import vectorize  # noqa: F401
    import math

    return 0.5 * (1 + np.vectorize(math.erf)(z / math.sqrt(2)))


def _yuzdelik(x: np.ndarray, p: float) -> float:
    return float(np.percentile(x, p))


def calistir(proje: Proje, ayarlar: SimulasyonAyarlari) -> Dict:
    n = ayarlar.deneme_sayisi
    rng = np.random.default_rng(ayarlar.tohum)
    ro = ayarlar.korelasyon

    # --- Baz (risksiz) maliyet ve süre ---
    baz_maliyet = pert_ornekle(proje.baz_maliyet, n, rng)
    baz_sure = pert_ornekle(proje.baz_sure, n, rng)

    riskler = proje.riskler
    k = len(riskler)
    maliyet_katkilari = np.zeros((k, n))
    sure_katkilari = np.zeros((k, n))
    gerceklesme = np.zeros((k, n), dtype=bool)

    # Gauss kopula ile ortak (korelasyonlu) etki büyüklükleri
    if k > 0:
        if ro > 0:
            ortak = rng.standard_normal(n)
            agirlik = np.sqrt(ro)
        for i, risk in enumerate(riskler):
            p = risk.etkin_olasilik(ayarlar.onlemler_uygulandi)
            carpan = risk.etki_carpani(ayarlar.onlemler_uygulandi)
            olur = rng.random(n) < p
            gerceklesme[i] = olur

            if ro > 0:
                z = agirlik * ortak + np.sqrt(1 - ro) * rng.standard_normal(n)
                u = _norm_cdf(z)
                m_ornek = _pert_kopula(risk.maliyet_etkisi, u)
                s_ornek = _pert_kopula(risk.sure_etkisi, u)
            else:
                m_ornek = pert_ornekle(risk.maliyet_etkisi, n, rng)
                s_ornek = pert_ornekle(risk.sure_etkisi, n, rng)

            isaret = -1.0 if risk.tur == "Fırsat" else 1.0
            maliyet_katkilari[i] = isaret * carpan * m_ornek * olur
            sure_katkilari[i] = isaret * carpan * s_ornek * olur

    onlem_gideri = (
        sum(r.onlem_maliyeti for r in riskler) if ayarlar.onlemler_uygulandi else 0.0
    )

    toplam_maliyet = baz_maliyet + maliyet_katkilari.sum(axis=0) + onlem_gideri
    toplam_sure = baz_sure + sure_katkilari.sum(axis=0)

    sonuc = {
        "deneme_sayisi": n,
        "para_birimi": proje.para_birimi,
        "onlemler_uygulandi": ayarlar.onlemler_uygulandi,
        "onlem_gideri": onlem_gideri,
        "maliyet": _dagilim_ozeti(
            toplam_maliyet, proje.butce_hedefi, ayarlar.guven_duzeyi
        ),
        "sure": _dagilim_ozeti(toplam_sure, proje.sure_hedefi, ayarlar.guven_duzeyi),
        "histogram": _histogram(toplam_maliyet, 40),
        "sure_histogram": _histogram(toplam_sure, 40),
        "s_egrisi": _s_egrisi(toplam_maliyet),
        "sure_s_egrisi": _s_egrisi(toplam_sure),
        "tornado": _tornado(riskler, maliyet_katkilari, toplam_maliyet),
        "kritiklik": _kritiklik(riskler, gerceklesme, maliyet_katkilari),
    }

    baz_bpd = float(np.mean(baz_maliyet))
    p80 = sonuc["maliyet"]["p80"]
    sonuc["beklenmeyen_rezerv"] = {
        "baz_maliyet_ortalama": baz_bpd,
        "p50_rezerv": max(sonuc["maliyet"]["p50"] - baz_bpd, 0.0),
        "p80_rezerv": max(p80 - baz_bpd, 0.0),
        "p90_rezerv": max(sonuc["maliyet"]["p90"] - baz_bpd, 0.0),
        "onerilen_rezerv": max(p80 - baz_bpd, 0.0),
    }
    return sonuc


def _dagilim_ozeti(x: np.ndarray, hedef: float, guven: float) -> Dict:
    ortalama = float(np.mean(x))
    var_seviye = _yuzdelik(x, guven * 100)
    kuyruk = x[x >= var_seviye]
    cvar = float(np.mean(kuyruk)) if kuyruk.size else var_seviye
    return {
        "ortalama": ortalama,
        "standart_sapma": float(np.std(x, ddof=1)) if x.size > 1 else 0.0,
        "en_dusuk": float(np.min(x)),
        "en_yuksek": float(np.max(x)),
        "p10": _yuzdelik(x, 10),
        "p50": _yuzdelik(x, 50),
        "p80": _yuzdelik(x, 80),
        "p90": _yuzdelik(x, 90),
        "p95": _yuzdelik(x, 95),
        "guven_duzeyi": guven,
        "riske_maruz_deger": var_seviye,
        "kosullu_rmd": cvar,
        "hedef": hedef,
        "hedefi_tutturma_olasiligi": (
            float(np.mean(x <= hedef)) if hedef and hedef > 0 else None
        ),
    }


def _histogram(x: np.ndarray, kutu: int) -> Dict:
    frekans, kenar = np.histogram(x, bins=kutu)
    merkez = (kenar[:-1] + kenar[1:]) / 2
    return {
        "merkezler": [float(v) for v in merkez],
        "frekanslar": [int(v) for v in frekans],
        "genislik": float(kenar[1] - kenar[0]) if len(kenar) > 1 else 0.0,
    }


def _s_egrisi(x: np.ndarray, nokta: int = 50) -> Dict:
    yuzdeler = np.linspace(0, 100, nokta)
    degerler = np.percentile(x, yuzdeler)
    return {
        "degerler": [float(v) for v in degerler],
        "olasiliklar": [float(p) / 100 for p in yuzdeler],
    }


def _tornado(riskler: List, katkilar: np.ndarray, toplam: np.ndarray) -> List[Dict]:
    """Her riskin toplam maliyet üzerindeki etkisi: korelasyon + ortalama katkı."""
    cikti = []
    for i, risk in enumerate(riskler):
        seri = katkilar[i]
        if np.std(seri) < 1e-12 or np.std(toplam) < 1e-12:
            korelasyon = 0.0
        else:
            korelasyon = float(np.corrcoef(seri, toplam)[0, 1])
        cikti.append(
            {
                "kod": risk.kod,
                "ad": risk.ad,
                "korelasyon": korelasyon,
                "katki_payi": float(np.mean(seri)),
                "en_kotu_katki": float(np.percentile(seri, 95)),
            }
        )
    cikti.sort(key=lambda d: -abs(d["katki_payi"]))
    return cikti


def _kritiklik(riskler: List, gerceklesme: np.ndarray, katkilar: np.ndarray) -> List[Dict]:
    cikti = []
    for i, risk in enumerate(riskler):
        olur = gerceklesme[i]
        adet = int(olur.sum())
        cikti.append(
            {
                "kod": risk.kod,
                "ad": risk.ad,
                "gerceklesme_orani": float(olur.mean()),
                "gerceklestiginde_ortalama_etki": (
                    float(katkilar[i][olur].mean()) if adet else 0.0
                ),
            }
        )
    cikti.sort(key=lambda d: -abs(d["gerceklestiginde_ortalama_etki"]))
    return cikti
