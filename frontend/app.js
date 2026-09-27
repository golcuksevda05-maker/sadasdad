/* Olasılık ve Risk Analizi Programı – arayüz mantığı */
let riskler = [];
let sabitler = { kategoriler: [], durumlar: [], stratejiler: [] };
let grafikler = {};
let sonSonuc = null;

const $ = (id) => document.getElementById(id);
const sayi = (v) => (isNaN(parseFloat(v)) ? 0 : parseFloat(v));
const bicim = (v, ondalik = 0) =>
  (v ?? 0).toLocaleString("tr-TR", { minimumFractionDigits: ondalik, maximumFractionDigits: ondalik });
const yuzde = (v) => (v == null ? "—" : (v * 100).toFixed(1).replace(".", ",") + "%");

function bildir(mesaj, hata = false) {
  const b = $("bildirim");
  b.textContent = mesaj;
  b.style.borderLeftColor = hata ? "#c0392b" : "#2e9e63";
  b.classList.add("gorunur");
  setTimeout(() => b.classList.remove("gorunur"), 3000);
}

/* ---------- Sekmeler ---------- */
document.querySelectorAll(".sekme").forEach((s) =>
  s.addEventListener("click", () => {
    document.querySelectorAll(".sekme").forEach((x) => x.classList.remove("etkin"));
    document.querySelectorAll(".panel").forEach((x) => x.classList.remove("etkin"));
    s.classList.add("etkin");
    $(s.dataset.hedef).classList.add("etkin");
  })
);

/* ---------- Risk tablosu ---------- */
function bosRisk(i) {
  return {
    kod: "R-" + String(i).padStart(2, "0"),
    ad: "Yeni risk",
    aciklama: "",
    kategori: sabitler.kategoriler[0] || "Teknik",
    tur: "Tehdit",
    olasilik: 0.3,
    maliyet_etkisi: { iyimser: 0, en_olasi: 0, kotumser: 0 },
    sure_etkisi: { iyimser: 0, en_olasi: 0, kotumser: 0 },
    strateji: "Azaltma",
    azaltma_sonrasi_olasilik: null,
    azaltma_etkinligi: 0,
    onlem_maliyeti: 0,
    sorumlu: "",
    durum: "Açık",
  };
}

function secenekler(liste, secili) {
  return liste.map((o) => `<option ${o === secili ? "selected" : ""}>${o}</option>`).join("");
}

function tabloCiz() {
  const gövde = document.querySelector("#riskTablosu tbody");
  gövde.innerHTML = riskler
    .map(
      (r, i) => `<tr data-i="${i}">
      <td><input data-a="kod" value="${r.kod}" style="min-width:64px"></td>
      <td><input data-a="ad" value="${r.ad}" style="min-width:180px"></td>
      <td><select data-a="kategori">${secenekler(sabitler.kategoriler, r.kategori)}</select></td>
      <td><select data-a="tur">${secenekler(["Tehdit", "Fırsat"], r.tur)}</select></td>
      <td><input data-a="olasilik" type="number" step="0.05" min="0" max="1" value="${r.olasilik}"></td>
      <td><input data-a="m.iyimser" type="number" min="0" value="${r.maliyet_etkisi.iyimser}"></td>
      <td><input data-a="m.en_olasi" type="number" min="0" value="${r.maliyet_etkisi.en_olasi}"></td>
      <td><input data-a="m.kotumser" type="number" min="0" value="${r.maliyet_etkisi.kotumser}"></td>
      <td><input data-a="s.iyimser" type="number" min="0" value="${r.sure_etkisi.iyimser}"></td>
      <td><input data-a="s.en_olasi" type="number" min="0" value="${r.sure_etkisi.en_olasi}"></td>
      <td><input data-a="s.kotumser" type="number" min="0" value="${r.sure_etkisi.kotumser}"></td>
      <td><select data-a="strateji">${secenekler(sabitler.stratejiler, r.strateji)}</select></td>
      <td><input data-a="azaltma_sonrasi_olasilik" type="number" step="0.05" min="0" max="1" value="${r.azaltma_sonrasi_olasilik ?? ""}"></td>
      <td><input data-a="azaltma_etkinligi" type="number" step="0.05" min="0" max="1" value="${r.azaltma_etkinligi}"></td>
      <td><input data-a="onlem_maliyeti" type="number" min="0" value="${r.onlem_maliyeti}"></td>
      <td><input data-a="sorumlu" value="${r.sorumlu}" style="min-width:110px"></td>
      <td><select data-a="durum">${secenekler(sabitler.durumlar, r.durum)}</select></td>
      <td><button class="sil" title="Sil">✕</button></td>
    </tr>`
    )
    .join("");

  gövde.querySelectorAll("tr").forEach((tr) => {
    const i = +tr.dataset.i;
    tr.querySelectorAll("[data-a]").forEach((el) =>
      el.addEventListener("change", () => {
        const a = el.dataset.a;
        const r = riskler[i];
        if (a.startsWith("m.")) r.maliyet_etkisi[a.slice(2)] = sayi(el.value);
        else if (a.startsWith("s.")) r.sure_etkisi[a.slice(2)] = sayi(el.value);
        else if (["olasilik", "azaltma_etkinligi", "onlem_maliyeti"].includes(a)) r[a] = sayi(el.value);
        else if (a === "azaltma_sonrasi_olasilik") r[a] = el.value === "" ? null : sayi(el.value);
        else r[a] = el.value;
      })
    );
    tr.querySelector(".sil").addEventListener("click", () => {
      riskler.splice(i, 1);
      tabloCiz();
    });
  });
}

$("btnRiskEkle").addEventListener("click", () => {
  riskler.push(bosRisk(riskler.length + 1));
  tabloCiz();
});

/* ---------- Proje nesnesi ---------- */
function projeTopla() {
  return {
    ad: $("projeAd").value || "Yeni Proje",
    para_birimi: $("paraBirimi").value || "TL",
    baz_maliyet: { iyimser: sayi($("bmIyimser").value), en_olasi: sayi($("bmOlasi").value), kotumser: sayi($("bmKotumser").value) },
    baz_sure: { iyimser: sayi($("bsIyimser").value), en_olasi: sayi($("bsOlasi").value), kotumser: sayi($("bsKotumser").value) },
    butce_hedefi: sayi($("butceHedefi").value),
    sure_hedefi: sayi($("sureHedefi").value),
    riskler: riskler,
  };
}

function projeYaz(p) {
  $("projeAd").value = p.ad;
  $("paraBirimi").value = p.para_birimi;
  $("butceHedefi").value = p.butce_hedefi;
  $("sureHedefi").value = p.sure_hedefi;
  $("bmIyimser").value = p.baz_maliyet.iyimser;
  $("bmOlasi").value = p.baz_maliyet.en_olasi;
  $("bmKotumser").value = p.baz_maliyet.kotumser;
  $("bsIyimser").value = p.baz_sure.iyimser;
  $("bsOlasi").value = p.baz_sure.en_olasi;
  $("bsKotumser").value = p.baz_sure.kotumser;
  riskler = p.riskler || [];
  tabloCiz();
}

function ayarlarTopla() {
  return {
    deneme_sayisi: Math.max(100, sayi($("denemeSayisi").value)),
    tohum: $("tohum").value === "" ? null : sayi($("tohum").value),
    korelasyon: sayi($("korelasyon").value),
    onlemler_uygulandi: $("onlemler").checked,
    guven_duzeyi: sayi($("guven").value) || 0.95,
  };
}

/* ---------- Analiz ---------- */
async function analizCalistir() {
  const p = projeTopla();
  if (!p.riskler.length) return bildir("Önce en az bir risk ekleyin.", true);
  try {
    const y = await fetch("/api/analiz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ proje: p, ayarlar: ayarlarTopla() }),
    });
    if (!y.ok) throw new Error((await y.json()).detail || "Hata");
    sonSonuc = await y.json();
    matrisCiz(sonSonuc.degerlendirme);
    simulasyonCiz(sonSonuc.simulasyon, p.para_birimi);
    raporCiz(sonSonuc, p);
    bildir("Analiz tamamlandı.");
  } catch (e) {
    bildir("Analiz hatası: " + e.message, true);
  }
}
$("btnAnaliz").addEventListener("click", analizCalistir);

/* ---------- Matris ---------- */
function matrisCiz(d) {
  const etiketler = ["Çok Düşük", "Düşük", "Orta", "Yüksek", "Çok Yüksek"];
  let html = "<table><tr><th></th>" + etiketler.map((e, i) => `<th>${i + 1}<br>${e}</th>`).join("") + "</tr>";
  d.matris.forEach((satir) => {
    html += `<tr><th>${satir[0].etki} · ${etiketler[satir[0].etki - 1]}</th>`;
    satir.forEach((h) => {
      html += `<td style="background:${h.renk}" title="Skor ${h.skor} – ${h.derece}">
        <div style="opacity:.75">${h.skor}</div>${h.riskler.join(", ")}</td>`;
    });
    html += "</tr>";
  });
  html += "</table><div class='ipucu'>Satır: Etki · Sütun: Olasılık</div>";
  $("matrisAlani").innerHTML = html;

  const g = document.querySelector("#siraliTablo tbody");
  g.innerHTML = d.riskler
    .map(
      (r) => `<tr>
      <td>${r.kod}</td><td>${r.ad}</td><td>${r.kategori}</td>
      <td>${yuzde(r.olasilik)}</td><td>${r.etki_seviyesi}</td><td>${r.skor}</td>
      <td><span class="rozet" style="background:${r.renk}">${r.derece}</span></td>
      <td>${bicim(r.beklenen_parasal_deger)}</td>
      <td style="color:${r.onlem_net_faydasi >= 0 ? "#2e9e63" : "#c0392b"}">${bicim(r.onlem_net_faydasi)}</td>
    </tr>`
    )
    .join("");
}

/* ---------- Grafikler ---------- */
function grafik(id, yapilandirma) {
  if (grafikler[id]) grafikler[id].destroy();
  Chart.defaults.color = "#9fb0c0";
  Chart.defaults.borderColor = "#2b3a4a";
  grafikler[id] = new Chart($(id), yapilandirma);
}

function simulasyonCiz(s, pb) {
  const m = s.maliyet;
  const r = s.beklenmeyen_rezerv;
  $("kartlar").innerHTML = [
    ["Ortalama Maliyet", bicim(m.ortalama) + " " + pb, "Simülasyon ortalaması"],
    ["P50 (Medyan)", bicim(m.p50) + " " + pb, "%50 olasılıkla altında"],
    ["P80", bicim(m.p80) + " " + pb, "Önerilen taahhüt seviyesi"],
    ["Önerilen Rezerv", bicim(r.onerilen_rezerv) + " " + pb, "P80 − baz maliyet"],
    [`RMD (%${(m.guven_duzeyi * 100).toFixed(0)})`, bicim(m.riske_maruz_deger) + " " + pb, "Koşullu RMD: " + bicim(m.kosullu_rmd)],
    ["Bütçeyi Tutturma", m.hedefi_tutturma_olasiligi == null ? "—" : yuzde(m.hedefi_tutturma_olasiligi), "Hedef: " + bicim(m.hedef)],
    ["Ortalama Süre", bicim(s.sure.ortalama, 1) + " gün", "P80: " + bicim(s.sure.p80, 1) + " gün"],
    ["Takvimi Tutturma", s.sure.hedefi_tutturma_olasiligi == null ? "—" : yuzde(s.sure.hedefi_tutturma_olasiligi), "Hedef: " + bicim(s.sure.hedef, 1) + " gün"],
  ]
    .map(([e, d, n]) => `<div class="ozet"><div class="etiket">${e}</div><div class="deger">${d}</div><div class="not">${n}</div></div>`)
    .join("");

  grafik("grafHistogram", {
    type: "bar",
    data: {
      labels: s.histogram.merkezler.map((v) => bicim(v)),
      datasets: [{ label: "Frekans", data: s.histogram.frekanslar, backgroundColor: "#3d8bfd99", borderColor: "#3d8bfd", borderWidth: 1 }],
    },
    options: { plugins: { legend: { display: false } }, scales: { x: { ticks: { maxTicksLimit: 10 } } } },
  });

  grafik("grafSEgrisi", {
    type: "line",
    data: {
      labels: s.s_egrisi.degerler.map((v) => bicim(v)),
      datasets: [{ label: "Birikimli olasılık", data: s.s_egrisi.olasiliklar.map((v) => v * 100), borderColor: "#2e9e63", backgroundColor: "#2e9e6333", fill: true, pointRadius: 0, tension: 0.2 }],
    },
    options: { scales: { y: { min: 0, max: 100, title: { display: true, text: "%" } }, x: { ticks: { maxTicksLimit: 10 } } } },
  });

  const t = s.tornado.slice(0, 12);
  grafik("grafTornado", {
    type: "bar",
    data: {
      labels: t.map((x) => x.kod + " " + x.ad.slice(0, 22)),
      datasets: [{ label: "Ortalama maliyet katkısı", data: t.map((x) => x.katki_payi), backgroundColor: t.map((x) => (x.katki_payi >= 0 ? "#c0392bcc" : "#2e9e63cc")) }],
    },
    options: { indexAxis: "y", plugins: { legend: { display: false } } },
  });

  grafik("grafSure", {
    type: "bar",
    data: {
      labels: s.sure_histogram.merkezler.map((v) => bicim(v, 1)),
      datasets: [{ label: "Frekans", data: s.sure_histogram.frekanslar, backgroundColor: "#e0a80099", borderColor: "#e0a800", borderWidth: 1 }],
    },
    options: { plugins: { legend: { display: false } }, scales: { x: { ticks: { maxTicksLimit: 10 } } } },
  });
}

/* ---------- Rapor ---------- */
function raporCiz(sonuc, proje) {
  const o = sonuc.degerlendirme.ozet;
  const m = sonuc.simulasyon.maliyet;
  const r = sonuc.simulasyon.beklenmeyen_rezerv;
  const pb = proje.para_birimi;
  const enler = sonuc.degerlendirme.riskler.slice(0, 5);
  const satir = (a, b) => `<div class="rapor-satir"><span>${a}</span><span>${b}</span></div>`;
  $("raporAlani").innerHTML = `
    <h3>${proje.ad}</h3>
    ${satir("Toplam risk sayısı", `${o.risk_sayisi} (${o.tehdit_sayisi} tehdit, ${o.firsat_sayisi} fırsat)`)}
    ${satir("Kritik / Yüksek risk", `${o.kritik_sayisi} / ${o.yuksek_sayisi}`)}
    ${satir("Toplam Beklenen Parasal Değer (BPD)", bicim(o.toplam_bpd) + " " + pb)}
    ${satir("Önlem sonrası BPD", bicim(o.onlem_sonrasi_toplam_bpd) + " " + pb)}
    ${satir("Toplam önlem maliyeti", bicim(o.toplam_onlem_maliyeti) + " " + pb)}
    ${satir("Önlemlerin net faydası", bicim(o.onlem_net_faydasi) + " " + pb)}
    ${satir("Baz maliyet (PERT ortalaması)", bicim(o.baz_maliyet) + " " + pb)}
    ${satir("Simülasyon ortalaması", bicim(m.ortalama) + " " + pb)}
    ${satir("P50 / P80 / P90", `${bicim(m.p50)} / ${bicim(m.p80)} / ${bicim(m.p90)} ${pb}`)}
    ${satir("Önerilen beklenmedik durum rezervi (P80)", bicim(r.onerilen_rezerv) + " " + pb)}
    ${satir("Bütçe hedefini tutturma olasılığı", yuzde(m.hedefi_tutturma_olasiligi))}
    <h3>En Kritik 5 Risk</h3>
    <ol>${enler.map((x) => `<li><b>${x.kod} – ${x.ad}</b> · skor ${x.skor} (${x.derece}) · BPD ${bicim(x.beklenen_parasal_deger)} ${pb} · Strateji: ${x.strateji}</li>`).join("")}</ol>
    <p class="ipucu">Yorum: P80 seviyesi (${bicim(m.p80)} ${pb}) taahhüt bütçesi olarak alınırsa, ${bicim(r.onerilen_rezerv)} ${pb} tutarında beklenmedik durum rezervi ayrılmalıdır.</p>`;
}

/* ---------- Kayıt / yükleme ---------- */
async function projeleriListele() {
  const l = await (await fetch("/api/projeler")).json();
  $("projeListesi").innerHTML =
    '<option value="">— Kayıtlı proje seç —</option>' +
    l.map((p) => `<option value="${p.ad}">${p.ad} (${p.risk_sayisi} risk)</option>`).join("");
}

$("btnKaydet").addEventListener("click", async () => {
  const y = await fetch("/api/projeler", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(projeTopla()),
  });
  bildir(y.ok ? "Proje kaydedildi." : "Kaydedilemedi.", !y.ok);
  projeleriListele();
});

$("btnYukle").addEventListener("click", async () => {
  const ad = $("projeListesi").value;
  if (!ad) return bildir("Bir proje seçin.", true);
  const y = await fetch("/api/projeler/" + encodeURIComponent(ad));
  if (!y.ok) return bildir("Proje yüklenemedi.", true);
  projeYaz(await y.json());
  bildir("Proje yüklendi.");
  analizCalistir();
});

$("btnCsv").addEventListener("click", async () => {
  const y = await fetch("/api/disa-aktar/csv", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(projeTopla()),
  });
  const blob = await y.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "risk_kaydi.csv";
  a.click();
});

$("btnOrnek").addEventListener("click", async () => {
  const y = await fetch("/statik/ornek_proje.json");
  projeYaz(await y.json());
  bildir("Örnek veri yüklendi.");
  analizCalistir();
});

/* ---------- Başlangıç ---------- */
(async function baslat() {
  sabitler = await (await fetch("/api/sabitler")).json();
  await projeleriListele();
  const y = await fetch("/statik/ornek_proje.json");
  if (y.ok) {
    projeYaz(await y.json());
    analizCalistir();
  } else {
    tabloCiz();
  }
})();
