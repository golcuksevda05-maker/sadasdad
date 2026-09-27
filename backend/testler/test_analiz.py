"""Temel doğrulama testleri."""
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import uygulama
from app.modeller import Proje, Risk, SimulasyonAyarlari, UcNoktaliTahmin
from app.risk import matris_derecesi, olasilik_seviyesi, proje_degerlendir
from app.simulasyon import _beta_cdf, _beta_ppf, calistir, pert_ornekle

istemci = TestClient(uygulama)


def ornek_proje() -> Proje:
    return Proje(
        ad="Test Projesi",
        baz_maliyet=UcNoktaliTahmin(iyimser=800, en_olasi=1000, kotumser=1400),
        baz_sure=UcNoktaliTahmin(iyimser=80, en_olasi=100, kotumser=140),
        butce_hedefi=1300,
        sure_hedefi=130,
        riskler=[
            Risk(
                kod="R-01",
                ad="Tedarik gecikmesi",
                kategori="Tedarik",
                olasilik=0.5,
                maliyet_etkisi=UcNoktaliTahmin(iyimser=50, en_olasi=100, kotumser=200),
                sure_etkisi=UcNoktaliTahmin(iyimser=5, en_olasi=10, kotumser=20),
                azaltma_sonrasi_olasilik=0.2,
                azaltma_etkinligi=0.5,
                onlem_maliyeti=10,
            ),
            Risk(
                kod="R-02",
                ad="Erken teslim primi",
                tur="Fırsat",
                olasilik=0.3,
                maliyet_etkisi=UcNoktaliTahmin(iyimser=20, en_olasi=40, kotumser=60),
            ),
        ],
    )


def test_pert_ortalamasi():
    t = UcNoktaliTahmin(iyimser=10, en_olasi=20, kotumser=60)
    assert t.beklenen_deger == pytest.approx((10 + 80 + 60) / 6)


def test_pert_ornekleme_sinirlari():
    rng = np.random.default_rng(1)
    x = pert_ornekle(UcNoktaliTahmin(iyimser=10, en_olasi=20, kotumser=60), 5000, rng)
    assert x.min() >= 10 and x.max() <= 60
    assert x.mean() == pytest.approx(25, rel=0.05)


def test_beta_ppf_cdf_tutarli():
    u = np.array([0.05, 0.25, 0.5, 0.75, 0.95])
    x = _beta_ppf(u, 2.5, 3.5)
    assert np.allclose(_beta_cdf(x, 2.5, 3.5), u, atol=1e-3)


def test_uc_noktali_dogrulama():
    with pytest.raises(ValueError):
        UcNoktaliTahmin(iyimser=100, en_olasi=50, kotumser=200)


def test_olasilik_ve_derece():
    assert olasilik_seviyesi(0.05)[0] == 1
    assert olasilik_seviyesi(0.95)[0] == 5
    assert matris_derecesi(3) == "Düşük"
    assert matris_derecesi(20) == "Kritik"


def test_degerlendirme_bpd():
    sonuc = proje_degerlendir(ornek_proje())
    r1 = next(r for r in sonuc["riskler"] if r["kod"] == "R-01")
    assert r1["beklenen_parasal_deger"] == pytest.approx(0.5 * (50 + 400 + 200) / 6)
    firsat = next(r for r in sonuc["riskler"] if r["kod"] == "R-02")
    assert firsat["beklenen_parasal_deger"] < 0  # fırsat maliyeti düşürür
    assert len(sonuc["matris"]) == 5 and len(sonuc["matris"][0]) == 5


def test_simulasyon_tutarliligi():
    p = ornek_proje()
    s1 = calistir(p, SimulasyonAyarlari(deneme_sayisi=4000, tohum=7))
    s2 = calistir(p, SimulasyonAyarlari(deneme_sayisi=4000, tohum=7))
    assert s1["maliyet"]["ortalama"] == s2["maliyet"]["ortalama"]  # tohum sabit
    m = s1["maliyet"]
    assert m["p10"] <= m["p50"] <= m["p80"] <= m["p90"]
    assert 0 <= m["hedefi_tutturma_olasiligi"] <= 1
    assert len(s1["tornado"]) == 2
    assert s1["beklenmeyen_rezerv"]["onerilen_rezerv"] >= 0


def test_onlemler_riski_azaltir():
    p = ornek_proje()
    ham = calistir(p, SimulasyonAyarlari(deneme_sayisi=6000, tohum=3))
    onlemli = calistir(
        p, SimulasyonAyarlari(deneme_sayisi=6000, tohum=3, onlemler_uygulandi=True)
    )
    assert onlemli["maliyet"]["p90"] < ham["maliyet"]["p90"]


def test_korelasyon_kuyrugu_kalinlastirir():
    p = ornek_proje()
    dusuk = calistir(p, SimulasyonAyarlari(deneme_sayisi=6000, tohum=5, korelasyon=0.0))
    yuksek = calistir(p, SimulasyonAyarlari(deneme_sayisi=6000, tohum=5, korelasyon=0.8))
    assert yuksek["maliyet"]["standart_sapma"] > 0
    assert dusuk["maliyet"]["ortalama"] == pytest.approx(
        yuksek["maliyet"]["ortalama"], rel=0.05
    )


def test_api_uctan_uca():
    p = ornek_proje().model_dump()
    y = istemci.post("/api/analiz", json={"proje": p, "ayarlar": {"deneme_sayisi": 2000}})
    assert y.status_code == 200
    veri = y.json()
    assert veri["degerlendirme"]["ozet"]["risk_sayisi"] == 2
    assert veri["simulasyon"]["deneme_sayisi"] == 2000

    csv = istemci.post("/api/disa-aktar/csv", json=p)
    assert csv.status_code == 200 and "R-01" in csv.text
    assert istemci.get("/api/sabitler").json()["kategoriler"]
