# 📊 Olasılık ve Risk Analizi Programı

Proje riskleri için **nitel** (5×5 olasılık–etki matrisi) ve **nicel** (Monte Carlo simülasyonu)
analiz yapan, tamamen Türkçe bir uygulama.
Arka uç: **Python + FastAPI + NumPy** · Ön yüz: **tek sayfalık web paneli + Chart.js**

---

## Neler yapabiliyor?

**Nitel analiz**
- Risk kaydı (kod, ad, kategori, tehdit/fırsat, sorumlu, durum, strateji)
- Olasılık ve etki seviyelerinin otomatik hesabı (etki, baz maliyete oranla 1–5 ölçeğine yerleşir)
- 5×5 olasılık–etki matrisi ısı haritası ve Düşük/Orta/Yüksek/Kritik dereceleme
- Beklenen Parasal Değer (BPD / EMV) ve **önlem net faydası** (BPD azalması − önlem maliyeti)

**Nicel analiz (Monte Carlo)**
- Üç noktalı (iyimser / en olası / kötümser) tahminlerden **Beta-PERT** örnekleme
- Her risk için Bernoulli gerçekleşme denemesi; fırsatlar maliyeti düşürür, tehditler artırır
- Riskler arası **korelasyon** (tek faktörlü Gauss kopula, SciPy'siz Beta ters DF ile)
- Maliyet ve süre için: ortalama, standart sapma, P10/P50/P80/P90/P95
- **RMD (VaR)** ve **Koşullu RMD (CVaR)** seçilen güven düzeyinde
- Bütçe/takvim hedefini tutturma olasılığı
- **Beklenmedik durum rezervi** önerisi (P80 − baz maliyet)
- Histogram, birikimli olasılık (S eğrisi), **tornado** duyarlılık grafiği, risk kritiklik indeksi
- "Önlemler uygulandı" senaryosunu tek tıkla karşılaştırma

**Diğer**
- Proje kaydetme / yükleme (JSON dosya deposu, veritabanı gerekmez)
- Risk kaydını **CSV** olarak dışa aktarma (Excel uyumlu, `;` ayraçlı, UTF-8 BOM)
- Yönetici özeti raporu

---

## Kurulum ve çalıştırma

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

cd backend
uvicorn app.main:uygulama --host 0.0.0.0 --port 8000 --reload
```

Tarayıcıdan **http://localhost:8000** adresini açın. Açılışta örnek proje
(Fabrika Otomasyon Projesi, 8 risk) otomatik yüklenir.

### Testler

```bash
cd backend && pytest -q      # 10 test
```

---

## Proje yapısı

```
backend/
  app/
    modeller.py     # Pydantic modelleri (Proje, Risk, ÜçNoktalıTahmin, ayarlar)
    risk.py         # Nitel skorlama, 5×5 matris, BPD/EMV hesapları
    simulasyon.py   # Monte Carlo: Beta-PERT, kopula, yüzdelikler, tornado
    depo.py         # JSON dosya deposu
    main.py         # FastAPI uç noktaları + statik dosya sunumu
  testler/          # pytest testleri
frontend/
  index.html, stil.css, app.js, ornek_proje.json
veriler/            # Kaydedilen projeler (git'e dahil değil)
```

## API uç noktaları

| Yöntem | Yol | Açıklama |
|---|---|---|
| GET | `/api/saglik` | Servis kontrolü |
| GET | `/api/sabitler` | Kategori, durum, strateji listeleri |
| POST | `/api/degerlendirme` | Nitel analiz (matris + BPD) |
| POST | `/api/simulasyon` | Monte Carlo simülasyonu |
| POST | `/api/analiz` | Nitel + nicel analiz birlikte |
| GET/POST | `/api/projeler` | Kayıtlı projeleri listele / kaydet |
| GET/DELETE | `/api/projeler/{ad}` | Proje getir / sil |
| POST | `/api/disa-aktar/csv` | Risk kaydını CSV indir |

Etkileşimli API dokümanı: **http://localhost:8000/docs**

---

## Yöntem notları

- **Beta-PERT**: `α = 1 + 4(m−a)/(b−a)`, `β = 1 + 4(b−m)/(b−a)`; ortalama `(a+4m+b)/6`.
- **Matris dereceleri**: skor = olasılık seviyesi × etki seviyesi → 1–4 Düşük, 5–9 Orta,
  10–15 Yüksek, 16–25 Kritik.
- **Etki seviyesi eşikleri**: baz maliyetin %1 / %3 / %7 / %15'i.
- **Korelasyon**: tüm risk etkileri tek ortak faktöre `√ρ` ağırlığıyla bağlanır; ortalama
  değişmez, dağılımın kuyruğu kalınlaşır.

## Yol haritası (sonraki adımlar için fikirler)
- Zaman serisi/aktivite ağı (CPM) üzerinden takvim simülasyonu
- PDF/Excel rapor çıktısı
- Kullanıcı girişi ve çok kullanıcılı risk kaydı
- Risk izleme geçmişi ve trend grafikleri
