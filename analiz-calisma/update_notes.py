with open('opencode-notlari.md', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '## Faydalı bilgiler'
idx = content.index(marker)

new_section = '''

## GÜNCELLEME (28 Ekim öğleden sonrası) — ALTYAPI TAMAMLANDI ✅

- **Finansal Derinlik Modülü** (finansal_derinlik.py) ✅ Stdlib-only, 14 dönem, 147 kalem:
  - Marjlar (brüt/faaliyet/net/FAVOK proxy), Nakit akışı proxy (NOPAT), Normalize kâr, Net borç/FAVOK, Cari/Asit-test, Vergi oranı, NOPAT, Normalize kâr marjı
  - ASELS 2026/6: Faaliyet marj %27, Net marj %16.3, NOPAT 20.4B, Net borç/FAVOK 1.4x ✅
- **KAP PDF Parser** (kap_pdf_parser.py) ✅ pdfplumber + PyMuPDF fallback, teminat/dava/ilgili taraf/kambiyo/taahhüt/müşteri yoğunluğu regex çıkarma
- **KURALLAR.md** ✅ 7 kategori, 40+ eşik parametresi (fiyat, temel, kâr kalitesi, değerleme, haber, KAP dip not, bildirim)
- **Değerleme Modülü** (degerleme.py) ✅ DCF (3 senaryo), Çarpanlar (P/E, EV/FAVOK, EV/Sales), Ters DCF, Güvenlik marjı, NOPAT
- **ASELS Test Sonuçları (2026/6):** FAVOK marj %27.07, Net marj %16.33, NOPAT 20.4B, Net borç/FAVOK 1.41x, P/E hesaplandı, Fair value P/E bazlı hesaplandı

## SIRADAKİ ADIMLAR (29 Ekim — Otomasyon ve Entegrasyon)

1. **KAP PDF Parser Entegrasyonu** → kap_pdf_parser.py ajanlara entegre → KAP bildirimi PDF'ini indir → dip notları çıkar → bilanco-ajani/haber-ajani/ayi-ajani'ye besle
2. **Otomatik Veri Hattı (GitHub Actions)** → Günlük: fiyat + haber + KAP bildirimi toplama → Haftalık: bilanço/gelir tablosu güncelleme → Aylık: derin analiz tetikleme
3. **Sektör Şablonları** → Banka (NIM, CoR, CAR), Holding (NAV indirimi), Perakende (SSSG), Teknoloji (ARR/NRR), Enerji (rezerv/LCOE) → sektor_sablonlari/ klasörü
4. **Koordinatör Sentez Motoru** → 6 raporu birleştir → karar kutusu (🟢🟡🔴) + delta + "senin kaçırdığın" → analiz-arşivi/HISSE-YYYY-AA-GG.md
5. **Analiz Arşivi + Delta** → analiz-arşivi/ klasörü, SQLite/JSON indeks, arama, delta karşılaştırma
5. **Kural Motoru Entegrasyonu** → KURALLAR.md eşikleri → analiz sonrası kontrol → Telegram bildirimi
6. **Sektör Şablonları** → Banka (NIM, CoR, CAR), Holding (NAV indirimi), Perakende (SSSG), Teknoloji (ARR/NRR), Enerji (rezerv/LCOE)

'''

with open('opencode-notlari.md', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '## Faydalı bilgiler'
idx = content.index(marker)

new_content = content[:idx] + new_section + content[idx:]

with open('opencode-notlari.md', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Notlar güncellendi!')