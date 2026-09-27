"""Veri modelleri (tamamı Türkçe alan adlarıyla)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

KATEGORILER = [
    "Teknik",
    "Dış Çevre",
    "Organizasyonel",
    "Proje Yönetimi",
    "Finansal",
    "Yasal/Mevzuat",
    "Tedarik",
    "İnsan Kaynağı",
]

DURUMLAR = ["Açık", "İzleniyor", "Gerçekleşti", "Kapandı"]

STRATEJILER = ["Kaçınma", "Azaltma", "Devretme", "Kabul", "Fırsat - Yararlanma"]


class UcNoktaliTahmin(BaseModel):
    """Beta-PERT için iyimser / en olası / kötümser üçlüsü."""

    iyimser: float = Field(0.0, ge=0)
    en_olasi: float = Field(0.0, ge=0)
    kotumser: float = Field(0.0, ge=0)

    @field_validator("en_olasi")
    @classmethod
    def _en_olasi_araliginda(cls, v, info):
        iyimser = info.data.get("iyimser", 0.0)
        if v < iyimser:
            raise ValueError("En olası değer, iyimser değerden küçük olamaz.")
        return v

    @field_validator("kotumser")
    @classmethod
    def _kotumser_araliginda(cls, v, info):
        en_olasi = info.data.get("en_olasi", 0.0)
        if v < en_olasi:
            raise ValueError("Kötümser değer, en olası değerden küçük olamaz.")
        return v

    @property
    def beklenen_deger(self) -> float:
        """PERT ortalaması: (a + 4m + b) / 6"""
        return (self.iyimser + 4 * self.en_olasi + self.kotumser) / 6


class Risk(BaseModel):
    kod: str = Field(..., description="Benzersiz risk kodu, örn. R-01")
    ad: str
    aciklama: str = ""
    kategori: str = "Teknik"
    tur: Literal["Tehdit", "Fırsat"] = "Tehdit"
    olasilik: float = Field(..., ge=0, le=1, description="Gerçekleşme olasılığı 0-1")
    maliyet_etkisi: UcNoktaliTahmin = UcNoktaliTahmin()
    sure_etkisi: UcNoktaliTahmin = UcNoktaliTahmin()
    strateji: str = "Azaltma"
    azaltma_sonrasi_olasilik: Optional[float] = Field(None, ge=0, le=1)
    azaltma_etkinligi: float = Field(
        0.0, ge=0, le=1, description="Önlem sonrası etkideki azalma oranı (0-1)"
    )
    onlem_maliyeti: float = Field(0.0, ge=0)
    sorumlu: str = ""
    durum: str = "Açık"

    def etkin_olasilik(self, onlemler_uygulandi: bool) -> float:
        if not onlemler_uygulandi:
            return self.olasilik
        if self.azaltma_sonrasi_olasilik is not None:
            return self.azaltma_sonrasi_olasilik
        return self.olasilik

    def etki_carpani(self, onlemler_uygulandi: bool) -> float:
        return (1 - self.azaltma_etkinligi) if onlemler_uygulandi else 1.0


class Proje(BaseModel):
    ad: str = "Yeni Proje"
    para_birimi: str = "TL"
    baz_maliyet: UcNoktaliTahmin = UcNoktaliTahmin()
    baz_sure: UcNoktaliTahmin = UcNoktaliTahmin()
    butce_hedefi: float = 0.0
    sure_hedefi: float = 0.0
    riskler: List[Risk] = []


class SimulasyonAyarlari(BaseModel):
    deneme_sayisi: int = Field(10_000, ge=100, le=500_000)
    tohum: Optional[int] = 42
    korelasyon: float = Field(
        0.0, ge=0, le=0.95, description="Riskler arası ortak etki korelasyonu"
    )
    onlemler_uygulandi: bool = False
    guven_duzeyi: float = Field(0.95, gt=0.5, lt=1)


class SimulasyonIstegi(BaseModel):
    proje: Proje
    ayarlar: SimulasyonAyarlari = SimulasyonAyarlari()
