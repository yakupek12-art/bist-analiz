---
name: analiz
description: Tam çoklu-ajan finansal analiz pipeline'ı — veri toplama → 6 ajan paraleli → sentez → karar kutusu → arşiv + delta
---

# /analiz — TAM ANALİZ PIPELINE'I

## KULLANIM
```
/analiz ASELS.IS
/analiz THYAO.IS
```

---

## ⚙️ ADIM 1: VERİ TOPLAMA (KOORDİNATÖR — AI'SIZ, MAKİNE KODU)

> **BU ADIM TAMAMLANMAZSA AJANLAR ÇAĞRILMAZ**

```bash
# Sembol al
SEMBOL="$1"
SEMBOL_CLEAN="${SEMBOL/.IS/}"

# veri/ klasörünü hazırla
rm -rf veri && mkdir -p veri raporlar analiz-arşivi

echo "📊 Veri toplanıyor: $SEMBOL"

# 1. Fiyat (Yahoo Finance, 1y daily)
python3 -c "
import urllib.request, json, sys
url = f'https://query1.finance.yahoo.com/v8/finance/chart/{SEMBOL}?range=1y&interval=1d'
data = json.loads(urllib.request.urlopen(url).read())
result = data['chart']['result'][0]
meta = result['meta']
closes = [c for c in result['indicators']['quote'][0]['close'] if c]
highs = [h for h in result['indicators']['quote'][0]['high'] if h]
lows = [l for l in result['indicators']['quote'][0]['low'] if l]
volumes = [v for v in result['indicators']['quote'][0]['volume'] if v]
with open('veri/fiyat.json', 'w') as f:
    json.dump({'symbol': SEMBOL, 'last': meta['regularMarketPrice'], 'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}, f)
print('✅ Fiyat:', meta['regularMarketPrice'])
"

# 2. Bilanço (isyatirimhisse, 2015-2026)
python3 -c "
from isyatirimhisse import fetch_financials
import pandas as pd
df = fetch_financials(symbols=SEMBOL_CLEAN, start_year='2015', end_year='2026')
df.to_csv('veri/bilanco.csv', index=False)
print('✅ Bilanço:', len(df), 'kalem')
"

# 3. Haber (Google News RSS, son 30 gün)
curl -sS -m 15 "https://news.google.com/rss/search?q=${SEMBOL_CLEAN}&hl=tr&gl=TR&ceid=TR:tr" > veri/haberler.xml
# XML -> txt basitleştirme
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('veri/haberler.xml')
root = tree.getroot()
with open('veri/haberler.txt', 'w') as f:
    for item in root.findall('.//item'):
        title = item.find('title').text if item.find('title') is not None else ''
        source = item.find('source').text if item.find('source') is not None else ''
        pub = item.find('pubDate').text if item.find('pubDate') is not None else ''
        link = item.find('link').text if item.find('link') is not None else ''
        f.write(f'{title} | {source} | {pub} | {link}\n')
"
echo "✅ Haber: $(wc -l < veri/haberler.txt) başlık"

# 4. KAP Bildirimleri + Dip Not Parse (pykap + pdfplumber)
python3 -c "
try:
    from pykap import Kap
    import pdfplumber, requests, re, io
    k = Kap()
    company = k.get_company(SEMBOL_CLEAN)
    disclosures = company.get_disclosures(limit=50)
    keywords = ['teminat', 'rehin', 'ipotek', 'dava', 'ilgili taraf', 'kambiyo', 'hedge', 'müşteri yoğun', 'tek müşteri', 'ertelenmiş vergi', 'diğer faaliyet gelirl', 'tedarikçi', 'tek tedarikçi', 'taahhüt', 'sözleşme']
    with open('veri/kap_bildirim.txt', 'w', encoding='utf-8') as f:
        for d in disclosures:
            f.write(f'{d.title} | {d.date} | {d.url}\n')
            if d.pdf_url:
                try:
                    resp = requests.get(d.pdf_url, timeout=30)
                    pdf = pdfplumber.open(io.BytesIO(resp.content))
                    full_text = ''
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t: full_text += t + '\n'
                    for kw in keywords:
                        if re.search(kw, full_text, re.I):
                            # Bağlam: 300 karakter
                            idx = full_text.lower().index(kw.lower())
                            start = max(0, idx - 300)
                            end = min(len(full_text), idx + 500)
                            snippet = full_text[start:end].strip()
                            f.write(f'  >> DİP NOT [{kw.upper()}]: {snippet}\n')
                except Exception as e:
                    f.write(f'  >> PDF HATA: {e}\n')
    print('✅ KAP + Dip Not:', len(disclosures), 'bildirim')
except Exception as e:
    print('⚠️ KAP HATA:', e)
    with open('veri/kap_bildirim.txt', 'w') as f:
        f.write(f'KAP veri çekilemedi: {e}\n')
"

# 5. Rakip Verisi (borsapy - sektör peerleri)
python3 -c "
try:
    import borsapy as bp
    hisse = bp.Ticker(SEMBOL)
    info = hisse.info
    sektor = info.get('sector', '')
    # Basit: sektör hisseleri çek (borsapy destekliyorsa)
    peers = []
    if hasattr(bp, 'get_sector_stocks'):
        peers = bp.get_sector_stocks(sektor)[:10]
    with open('veri/rakip_veri.txt', 'w') as f:
        f.write(f'Sektör: {sektor}\n')
        for p in peers:
            f.write(f'{p}\n')
    print('✅ Rakip: {len(peers)} peer')
except Exception as e:
    print('⚠️ Rakip HATA:', e)
    with open('veri/rakip_veri.txt', 'w') as f:
        f.write(f'Rakip veri çekilemedi: {e}\n')
"

# 6. Teknik İndikatörler (TA-Lib)
python3 -c "
try:
    import talib, numpy as np, json
    with open('veri/fiyat.json') as f: data = json.load(f)
    closes = np.array(data['closes'], dtype=float)
    highs = np.array(data['highs'], dtype=float)
    lows = np.array(data['lows'], dtype=float)
    volumes = np.array(data['volumes'], dtype=float)
    
    rsi = talib.RSI(closes, 14)[-1]
    macd, sig, hist = talib.MACD(closes)
    sma20 = talib.SMA(closes, 20)[-1]
    sma50 = talib.SMA(closes, 50)[-1]
    sma200 = talib.SMA(closes, 200)[-1]
    bb_up, bb_mid, bb_low = talib.BBANDS(closes, 20)
    atr = talib.ATR(highs, lows, closes, 14)[-1]
    adx = talib.ADX(highs, lows, closes, 14)[-1]
    obv = talib.OBV(closes, volumes)[-1]
    
    with open('veri/teknik.json', 'w') as f:
        json.dump({
            'rsi': float(rsi) if not np.isnan(rsi) else None,
            'macd': float(macd[-1]) if not np.isnan(macd[-1]) else None,
            'signal': float(sig[-1]) if not np.isnan(sig[-1]) else None,
            'hist': float(hist[-1]) if not np.isnan(hist[-1]) else None,
            'sma20': float(sma20) if not np.isnan(sma20) else None,
            'sma50': float(sma50) if not np.isnan(sma50) else None,
            'sma200': float(sma200) if not np.isnan(sma200) else None,
            'bb_upper': float(bb_up[-1]) if not np.isnan(bb_up[-1]) else None,
            'bb_middle': float(bb_mid[-1]) if not np.isnan(bb_mid[-1]) else None,
            'bb_lower': float(bb_low[-1]) if not np.isnan(bb_low[-1]) else None,
            'atr': float(atr) if not np.isnan(atr) else None,
            'adx': float(adx) if not np.isnan(adx) else None,
            'obv': float(obv) if not np.isnan(obv) else None,
        }, f)
    print('✅ Teknik: RSI={:.1f}'.format(rsi))
except Exception as e:
    print('⚠️ Teknik HATA:', e)
    with open('veri/teknik.json', 'w') as f:
        json.dump({'error': str(e)}, f)
"

# 7. Finansal Derinlik (marjlar, NOPAT, normalize kâr, net borç/FAVÖK)
python3 analiz-calisma/finansal_derinlik_final.py veri > veri/finansal_derinlik.json 2>&1
echo "✅ Finansal Derinlik tamamlandı"

# 8. Değerleme (DCF, çarpanlar, ters DCF, güvenlik marjı)
python3 -c "
import sys
sys.path.insert(0, 'analiz-calisma')
from degerleme import calculate_valuation
import json, os, csv

# Bilanço verisini oku
all_rows = {}
period_cols = set()
for fname in sorted(os.listdir('veri')):
    if fname == 'bilanco.csv':
        with open(os.path.join('veri', fname), 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
            cols = [c.strip().strip('\"') for c in first_line.split(',')]
            cols = ['EMPTY' if c == '' else c for c in cols]
            reader = csv.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get('FINANCIAL_ITEM_CODE', '').strip()
                if not code: continue
                if code not in all_rows: all_rows[code] = {}
                for k, v in row.items():
                    if '/' in k and k[0].isdigit():
                        period_cols.add(k)
                        all_rows[code][k] = v.strip() if v else ''

period_cols = sorted(period_cols, key=lambda x: (int(x.split('/')[0]), int(x.split('/')[1])))

# Fiyat al
import json
with open('veri/fiyat.json') as f:
    price_data = json.load(f)
price = price_data.get('last')
shares = 3500000  # Yaklaşık hisse adedi (şirkete göre güncellenmeli)

result = calculate_valuation(all_rows, period_cols, price_per_share=price, shares=shares)
with open('veri/degerleme.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print('✅ Değerleme tamamlandı')
"

echo "🎯 Veri toplama TAMAM — veri/ klasörü dolu"
```

---

## 🤖 ADIM 2: 6 UZMAN AJAN PARALEL ÇAĞRILIR

> **Her ajan TEK ATIŞLIK, dosya ekiyle (`-f`), SERİ çalışır (free model limiti için)**

```bash
# Ajan raporları raporlar/ klasörüne yazılır
opencode run --agent haber-ajani   -f veri/haberler.txt   -f veri/kap_bildirim.txt   "Analiz et ve rapor yaz" > raporlar/haber-raporu.md 2>&1
opencode run --agent bilanco-ajani -f veri/bilanco.csv     -f veri/kap_bildirim.txt   -f veri/finansal_derinlik.json "Analiz et ve rapor yaz" > raporlar/bilanco-raporu.md 2>&1
opencode run --agent hikaye-ajani  -f veri/haberler.txt   -f veri/bilanco.csv        -f veri/kap_bildirim.txt "Analiz et ve rapor yaz" > raporlar/hikaye-raporu.md 2>&1
opencode run --agent rakip-ajani   -f veri/rakip_veri.txt -f veri/bilanco.csv        "Analiz et ve rapor yaz" > raporlar/rakip-raporu.md 2>&1
opencode run --agent teknik-ajani  -f veri/teknik.json    -f veri/fiyat.json         "Analiz et ve rapor yaz" > raporlar/teknik-raporu.md 2>&1
opencode run --agent ayi-ajani     -f veri/bilanco.csv    -f veri/haberler.txt       -f veri/kap_bildirim.txt   "Analiz et ve rapor yaz" > raporlas/ayi-raporu.md 2>&1

echo "✅ 6 ajan raporu üretti: raporlar/*.md"
```

---

## 🎯 ADIM 3: SENTEZ (KOORDİNATÖR — 6 RAPOR GELDİKTEN SONRA)

```bash
# 1. 6 raporu oku
# 2. KARAR KUTUSU belirle:
#    🟢 Olumlu: Tüm katmanlar olumlu/izle, KURALLAR.md ihlali YOK
#    🟡 Nötr-İzle: Karmaşık — güçlü/zayıf dengeli, 1-2 kural uyarısı VAR
#    🔴 Riskli: ≥2 katman ciddi olumsuz VEYA kritik kural ihlali (FAVÖK<%20, cari<1, NetBorç/FAVÖK>3x)
#
# 3. "SENİN KAÇIRDIKLARIN" → Sadece bilanco-raporu.md'deki "KAP DİP NOTLARI" bölümünden çek
# 4. DELTA → analiz-arşivi/${SEMBOL_CLEAN}-*.md en son dosya varsa Python diff ile karşılaştır
# 5. KURAL MOTORU → KURALLAR.md oku, eşikleri test et, ihlalleri listele
# 6. DEĞERLEME → veri/degerleme.json oku, özetle
# 7. ÇIKTI YAZ → analiz-arşivi/${SEMBOL_CLEAN}-$(date +%Y-%m-%d).md (TEMPLATE formatında)

python3 -c "
import os, json, re, glob
from datetime import datetime

sembol = '${SEMBOL_CLEAN}'
today = datetime.now().strftime('%Y-%m-%d')

# Raporları oku
reports = {}
for name in ['haber', 'bilanco', 'hikaye', 'rakip', 'teknik', 'ayi']:
    path = f'raporlar/{name}-raporu.md'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            reports[name] = f.read()
    else:
        reports[name] = 'RAPOR YOK'

# KARAR KUTUSU mantığı
kural_ihlalleri = []
# KURALLAR.md'yi basit parse et (yaml benzeri)
# Basit: dosya var mı kontrolü
has_kurallar = os.path.exists('analiz-calisma/KURALLAR.md')

# Basit kural: bilanco raporunda 'KRİTİK' veya 'RİSKLİ' geçiyorsa
risk_signals = 0
positive_signals = 0
for name, content in reports.items():
    if 'KRİTİK' in content.upper() or 'RİSKLİ' in content.upper() or 'ZAYIF' in content.upper():
        risk_signals += 1
    if 'GÜÇLÜ' in content.upper() or 'OLUMLU' in content.upper() or 'LİDER' in content.upper():
        positive_signals += 1

if risk_signals >= 2 or (has_kurallar and 'ihlal' in str(reports).lower()):
    karar = '🔴 RİSKLİ'
elif risk_signals == 0 and positive_signals >= 3:
    karar = '🟢 OLUMLU'
else:
    karar = '🟡 NÖTR-İZLE'

# KAÇIRDIKLARIN (bilanco raporundan)
kacirdiklar = ''
if 'bilanco' in reports:
    lines = reports['bilanco'].split('\n')
    in_section = False
    for line in lines:
        if 'KAÇIRABİLECEĞİN' in line.upper() or 'DİP NOT' in line.upper():
            in_section = True
        if in_section and line.strip().startswith('##') and 'KAÇIR' not in line.upper():
            in_section = False
        if in_section:
            kacirdiklar += line + '\n'

# DELTA (önceki rapor)
archive_files = sorted(glob.glob(f'analiz-arşivi/{sembol}-*.md'))
delta = ''
if len(archive_files) >= 2:
    prev = archive_files[-2]
    with open(prev, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    # Basit diff: satır bazlı
    curr_lines = set(str(reports).split('\n'))
    prev_lines = set(prev_content.split('\n'))
    added = curr_lines - prev_lines
    removed = prev_lines - curr_lines
    if added or removed:
        delta = '### Değişenler:\n'
        for a in sorted(added)[:10]:
            delta += f'+ {a}\n'
        for r in sorted(removed)[:5]:
            delta += f'- {r}\n'
    else:
        delta = 'Önceki rapordan belirgin değişiklik yok.'

# DEĞERLEME özeti
deg = ''
if os.path.exists('veri/degerleme.json'):
    with open('veri/degerleme.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    v = d.get('valuation', {})
    deg = f'- P/E: {v.get(\"p_e\", \"-\")} | EV/FAVÖK: {v.get(\"ev_favok\", \"-\")} | P/S: {v.get(\"p_s\", \"-\")}\n'
    deg += f'- FAVÖK Marjı: {v.get(\"favok_margin\", \"-\")}% | Net Marj: {v.get(\"net_margin\", \"-\")}%\n'
    deg += f'- Net Borç/FAVÖK: {v.get(\"net_borc_favok\", \"-\")}x\n'
    if 'fair_price_pe' in v:
        deg += f'- Fair Price (P/E bazlı): {v[\"fair_price_pe\"]:.2f} TL | Güvenlik Marjı: {v.get(\"safety_margin_pe\", \"-\")}%\n'

# TEMPLATE ile birleştir
output = f'''# {sembol} ANALİZ RAPORU -- {today}

## KARAR KUTUSU: {karar}

---

## 1. HABER & GÜNDEM
{reports.get('haber', 'RAPOR YOK')}

---

## 2. HİKAYE & HENDEK
{reports.get('hikaye', 'RAPOR YOK')}

---

## 3. TEMEL ANALIZ & KAP DİP NOTLARI
{reports.get('bilanco', 'RAPOR YOK')}

---

## 4. TEKNIK ANALIZ
{reports.get('teknik', 'RAPOR YOK')}

---

## 5. RAKİP & SEKTÖR KIYASI
{reports.get('rakip', 'RAPOR YOK')}

---

## 6. AYI / RİSK ANALİZİ
{reports.get('ayi', 'RAPOR YOK')}

---

## 7. DEĞERLEME
{deg}

---

## 🔍 SENİN KAÇIRDIKLARIN (KAP Dip Notları)
{kacirdiklar if kacirdiklar else 'Bilanco raporunda dip not bölümü bulunamadı.'}

---

## 📊 DELTA (Önceki Rapora Göre)
{delta}

---

*Bu analiz bilgi amaclidir; yatirim tavsiyesi degildir.*
'''

# Arşivi yaz
archive_path = f'analiz-arşivi/{sembol}-{today}.md'
with open(archive_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f'✅ Sentez tamam: {archive_path}')
print(f'KARAR: {karar}')
"

echo "🎉 ANALİZ TAMAMLANDI — analiz-arşivi/${SEMBOL_CLEAN}-$(date +%Y-%m-%d).md"
```

---

## ⚠️ HATA YÖNETİMİ
- Her adım `set -e` ile durmaz; hata olsa bile sonraki adım denenenir
- Ajanlardan biri başarısız olursa raporu "HATA: ..." ile işaretle, sentez devam eder
- Veri toplama tamamen başarısız olursa (internet yoksa) → "VERİ YETERSİZ" raporu üret

---

## ÇIKTI
- `analiz-arşivi/{HISSE}-{YYYY-MM-DD}.md` — Tam rapor (karar kutusu + 7 katman + kaçırdıklar + delta)
- `raporlar/*.md` — Ham ajan raporları (debug için)
- `veri/*.json/txt` — Ham veriler (tekrar analiz için)