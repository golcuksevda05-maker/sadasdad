"""Basit JSON dosya deposu (veritabanı gerektirmez)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .modeller import Proje

KOK = Path(__file__).resolve().parents[2]
VERI_DIZINI = KOK / "veriler"
VERI_DIZINI.mkdir(exist_ok=True)


def _yol(ad: str) -> Path:
    guvenli = "".join(c for c in ad if c.isalnum() or c in " -_çğıöşüÇĞİÖŞÜ").strip()
    if not guvenli:
        raise ValueError("Geçersiz proje adı.")
    return VERI_DIZINI / f"{guvenli}.json"


def listele() -> List[Dict]:
    kayitlar = []
    for p in sorted(VERI_DIZINI.glob("*.json")):
        try:
            veri = json.loads(p.read_text(encoding="utf-8"))
            kayitlar.append(
                {
                    "ad": veri.get("ad", p.stem),
                    "dosya": p.name,
                    "risk_sayisi": len(veri.get("riskler", [])),
                }
            )
        except json.JSONDecodeError:
            continue
    return kayitlar


def kaydet(proje: Proje) -> Path:
    yol = _yol(proje.ad)
    yol.write_text(
        json.dumps(proje.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return yol


def yukle(ad: str) -> Proje:
    yol = _yol(ad)
    if not yol.exists():
        raise FileNotFoundError(f"'{ad}' adlı proje bulunamadı.")
    return Proje.model_validate_json(yol.read_text(encoding="utf-8"))


def sil(ad: str) -> bool:
    yol = _yol(ad)
    if yol.exists():
        yol.unlink()
        return True
    return False
