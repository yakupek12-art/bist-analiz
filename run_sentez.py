import os
import json
import re
import glob
from datetime import datetime

sembol = 'TUPRS'
today = '2026-10-30'

# Raporlari oku
reports = {}
for name in ['sektor-ajani', 'hikaye-ajani', 'hendek-ajani', 'rakip-ajani', 'yonetim-ajani', 
             'sektor-karsilastirma-ajani', 'risk-ajani', 'degerleme-ajani', 'bilanco-ajani', 'teknik-ajani']:
    path = f'raporlar/{name}-raporu.md'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            reports[name] = f.read()
    else:
        reports[name] = 'RAPOR YOK'

# KARAR KUTUSU MANTIGI (10 Katman agirlikli)
layer_weights = {
    'sektor-ajani': 5, 'hikaye-ajani': 10, 'hendek-ajani': 20,
    'rakip-ajani': 10, 'yonetim-ajani': 10,
    'sektor-karsilastirma-ajani': 10, 'risk-ajani': 15,
    'degerleme-ajani': 10, 'bilanco-ajani': 5, 'teknik-ajani': 5,
}

risk_signals = 0
positive_signals = 0
total_weight = 0
positive_weight = 0

for name, content in reports.items():
    weight = {'sektor-ajani':5,'hikaye-ajani':10,'hendek-ajani':20,'rakip-ajani':10,'yonetim-ajani':10,
              'sektor-karsilastirma-ajani':10,'risk-ajani':15,'degerleme-ajani':10,'bilanco-ajani':5,'teknik-ajani':5}.get(name,5)
    total_weight += weight
    c = content.upper()
    if any(w in c for w in ['KRITIK','RISKLI','ZAYIF','SORUN','UYARI','DUSUS','AZALMA','KIRILMA','TUZAK']):
        risk_signals += 1
    if any(w in c for w in ['GUCLU','OLUMLU','LIDER','ARTIS','IYILESME','YUKSEK','KARLI','GENISLEME','AVANTAJ','GUVENILIR']):
        positive_signals += 1
        positive_weight += weight

if risk_signals >= 4 or (total_weight > 0 and (total_weight - positive_weight) / total_weight > 0.4):
    karar = 'ZAYIF'
elif risk_signals <= 1 and positive_weight / total_weight > 0.7:
    karar = 'GUCLU'
else:
    karar = 'ORTA'

# KACIRDIKLARIN (bilanco raporundan)
kacirdiklar = ''
if 'bilanco-ajani' in reports:
    lines = reports['bilanco-ajani'].split('\n')
    in_section = False
    for line in lines:
        if 'KACIRABILECEGIN' in line.upper() or 'DIP NOT' in line.upper():
            in_section = True
        if in_section and line.strip().startswith('##') and 'KACIR' not in line.upper():
            in_section = False
        if in_section:
            kacirdiklar += line + '\n'

# DELTA
archive_files = sorted(glob.glob('analiz-arşivi/TUPRS-*.md'))
delta = ''
if len(archive_files) >= 2:
    prev = archive_files[-2]
    with open(prev, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    curr_lines = set(str(reports).split('\n'))
    prev_lines = set(prev_content.split('\n'))
    added = curr_lines - prev_lines
    removed = prev_lines - curr_lines
    if added or removed:
        delta = '### Degisenler:\n'
        for a in sorted(added)[:15]:
            delta += '+ {a}\n'
        for r in sorted(removed)[:8]:
            delta += '- {r}\n'
    else:
        delta = 'Onceki rapordan belirgin degisiklik yok.'
elif len(archive_files) == 1:
    delta = 'Ilk analiz -- delta yok.'

# DEGERLEME
deg = ''
if os.path.exists('veri/degerleme.json'):
    with open('veri/degerleme.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    v = d.get('valuation', {})
    deg = '- P/E: {v.get("p_e", "-")} | EV/FAVOK: {v.get("ev_favok", "-")} | P/S: {v.get("p_s", "-")}\n'
    deg += '- FAVOK Marji: {v.get("favok_margin", "-")}% | Net Marj: {v.get("net_margin", "-")}%\n'
    deg += '- Net Borc/FAVOK: {v.get("net_borc_favok", "-")}x\n'
    if 'fair_price_pe' in v:
        deg += '- Fair Price (P/E): {v["fair_price_pe"]:.2f} TL | Guvenlik Marji: {v.get("safety_margin_pe", "-")}%\n'

# MOATSIZ DEGERLEME
moatsiz = ''
if os.path.exists('veri/degerleme_moatsiz.json'):
    with open('veri/degerleme_moatsiz.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    moatsiz = '- Hendeksiz Kontrol: {d.get("hendeksiz_kontrol", {}).get("tum_kriterler_karsilandi", "N/A")}\n'
    if 'fair_value_aralik' in d:
        moatsiz += '- Fair Value Araligi: {d["fair_value_aralik"].get("min", "N/A")} - {d["fair_value_aralik"].get("max", "N/A")} TL\n'

# TEKNIK POZISYON
teknik_ozet = ''
if os.path.exists('veri/teknik_pozisyon.json'):
    with open('veri/teknik_pozisyon.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    teknik_ozet = '- Trend: {d.get("ana_trend", "N/A")} | RSI: {d.get("indikatorler", {}).get("rsi", "N/A")} | R/R: {d.get("risk_odul", "N/A")}\n'
    teknik_ozet += '- Stop: {d.get("stop_loss", "N/A")} | Giris: {d.get("entry", "N/A")} | Hedef: {d.get("target1", "N/A")}\n'

# HENDEK SKORU
hendek_ozet = ''
if os.path.exists('veri/hendek_skor.json'):
    with open('veri/hendek_skor.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    hendek_ozet = '- Hendek Skoru: {d.get("skor", "N/A")}/100 -> {"HENDEKLI" if d.get("skor", 0) >= 50 else "HENDEKSIZ"}\n'

# Ensure variables are defined even if files don't exist
moatsiz = moatsiz or ''
teknik_ozet = teknik_ozet or ''
hendek_ozet = hendek_ozet or ''

# KACIRDIKLARIN
kacirdiklar = ''
if 'bilanco-ajani' in reports:
    lines = reports['bilanco-ajani'].split('\n')
    in_section = False
    for line in lines:
        if 'KACIRABILECEGIN' in line.upper() or 'DIP NOT' in line.upper():
            in_section = True
        if in_section and line.strip().startswith('##') and 'KACIR' not in line.upper():
            in_section = False
        if in_section:
            kacirdiklar += line + '\n'

# DELTA
archive_files = sorted(glob.glob('analiz-arşivi/TUPRS-*.md'))
delta = ''
if len(archive_files) >= 2:
    prev = archive_files[-2]
    with open(prev, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    curr_lines = set(str(reports).split('\n'))
    prev_lines = set(prev_content.split('\n'))
    added = curr_lines - prev_lines
    removed = prev_lines - curr_lines
    if added or removed:
        delta = '### Degisenler:\n'
        for a in sorted(added)[:15]:
            delta += '+ {a}\n'
        for r in sorted(removed)[:8]:
            delta += '- {r}\n'
    else:
        delta = 'Onceki rapordan belirgin degisiklik yok.'
elif len(archive_files) == 1:
    delta = 'Ilk analiz -- delta yok.'

# DEGERLEME
deg = ''
if os.path.exists('veri/degerleme.json'):
    with open('veri/degerleme.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    v = d.get('valuation', {})
    deg = '- P/E: {v.get("p_e", "-")} | EV/FAVOK: {v.get("ev_favok", "-")} | P/S: {v.get("p_s", "-")}\n'
    deg += '- FAVOK Marji: {v.get("favok_margin", "-")}% | Net Marj: {v.get("net_margin", "-")}%\n'
    deg += '- Net Borc/FAVOK: {v.get("net_borc_favok", "-")}x\n'
    if 'fair_price_pe' in v:
        deg += '- Fair Price (P/E): {v["fair_price_pe"]:.2f} TL | Guvenlik Marji: {v.get("safety_margin_pe", "-")}%\n'

# MOATSIZ DEGERLEME
moatsiz = ''
if os.path.exists('veri/degerleme_moatsiz.json'):
    with open('veri/degerleme_moatsiz.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    moatsiz = '- Hendeksiz Kontrol: {d.get("hendeksiz_kontrol", {}).get("tum_kriterler_karsilandi", "N/A")}\n'
    if 'fair_value_aralik' in d:
        moatsiz += '- Fair Value Araligi: {d["fair_value_aralik"].get("min", "N/A")} - {d["fair_value_aralik"].get("max", "N/A")} TL\n'

# TEKNIK POZISYON
teknik_ozet = ''
if os.path.exists('veri/teknik_pozisyon.json'):
    with open('veri/teknik_pozisyon.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    teknik_ozet = '- Trend: {d.get("ana_trend", "N/A")} | RSI: {d.get("indikatorler", {}).get("rsi", "N/A")} | R/R: {d.get("risk_odul", "N/A")}\n'
    teknik_ozet += '- Stop: {d.get("stop_loss", "N/A")} | Giris: {d.get("entry", "N/A")} | Hedef: {d.get("target1", "N/A")}\n'

# HENDEK SKORU
hendek_ozet = ''
if os.path.exists('veri/hendek_skor.json'):
    with open('veri/hendek_skor.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    hendek_ozet = '- Hendek Skoru: {d.get("skor", "N/A")}/100 -> {"HENDEKLI" if d.get("skor", 0) >= 50 else "HENDEKSIZ"}\n'

# Ensure variables are defined even if files don't exist
moatsiz = moatsiz or ''
teknik_ozet = teknik_ozet or ''
hendek_ozet = hendek_ozet or ''

# KACIRDIKLARIN
kacirdiklar = ''
if 'bilanco-ajani' in reports:
    lines = reports['bilanco-ajani'].split('\n')
    in_section = False
    for line in lines:
        if 'KACIRABILECEGIN' in line.upper() or 'DIP NOT' in line.upper():
            in_section = True
        if in_section and line.strip().startswith('##') and 'KACIR' not in line.upper():
            in_section = False
        if in_section:
            kacirdiklar += line + '\n'

# DELTA
archive_files = sorted(glob.glob('analiz-arşivi/TUPRS-*.md'))
delta = ''
if len(archive_files) >= 2:
    prev = archive_files[-2]
    with open(prev, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    curr_lines = set(str(reports).split('\n'))
    prev_lines = set(prev_content.split('\n'))
    added = curr_lines - prev_lines
    removed = prev_lines - curr_lines
    if added or removed:
        delta = '### Degisenler:\n'
        for a in sorted(added)[:15]:
            delta += '+ {a}\n'
        for r in sorted(removed)[:8]:
            delta += '- {r}\n'
    else:
        delta = 'Onceki rapordan belirgin degisiklik yok.'
elif len(archive_files) == 1:
    delta = 'Ilk analiz -- delta yok.'

# DEGERLEME
deg = ''
if os.path.exists('veri/degerleme.json'):
    with open('veri/degerleme.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    v = d.get('valuation', {})
    deg = '- P/E: {v.get("p_e", "-")} | EV/FAVOK: {v.get("ev_favok", "-")} | P/S: {v.get("p_s", "-")}\n'
    deg += '- FAVOK Marji: {v.get("favok_margin", "-")}% | Net Marj: {v.get("net_margin", "-")}%\n'
    deg += '- Net Borc/FAVOK: {v.get("net_borc_favok", "-")}x\n'
    if 'fair_price_pe' in v:
        deg += '- Fair Price (P/E): {v["fair_price_pe"]:.2f} TL | Guvenlik Marji: {v.get("safety_margin_pe", "-")}%\n'

# MOATSIZ
moatsiz = ''
if os.path.exists('veri/degerleme_moatsiz.json'):
    with open('veri/degerleme_moatsiz.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    moatsiz = '- Hendeksiz Kontrol: {d.get("hendeksiz_kontrol", {}).get("tum_kriterler_karsilandi", "N/A")}\n'
    if 'fair_value_aralik' in d:
        moatsiz += '- Fair Value Araligi: {d["fair_value_aralik"].get("min", "N/A")} - {d["fair_value_aralik"].get("max", "N/A")} TL\n'

# TEKNIK
teknik_ozet = ''
if os.path.exists('veri/teknik_pozisyon.json'):
    with open('veri/teknik_pozisyon.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    teknik_ozet = '- Trend: {d.get("ana_trend", "N/A")} | RSI: {d.get("indikatorler", {}).get("rsi", "N/A")} | R/R: {d.get("risk_odul", "N/A")}\n'
    teknik_ozet += '- Stop: {d.get("stop_loss", "N/A")} | Giris: {d.get("entry", "N/A")} | Hedef: {d.get("target1", "N/A")}\n'

# HENDEK
hendek_ozet = ''
if os.path.exists('veri/hendek_skor.json'):
    with open('veri/hendek_skor.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    hendek_ozet = '- Hendek Skoru: {d.get("skor", "N/A")}/100 -> {"HENDEKLI" if d.get("skor", 0) >= 50 else "HENDEKSIZ"}\n'

moatsiz = moatsiz or ''
teknik_ozet = teknik_ozet or ''
hendek_ozet = hendek_ozet or ''

# KACIRDIKLARIN
kacirdiklar = ''
if 'bilanco-ajani' in reports:
    lines = reports['bilanco-ajani'].split('\n')
    in_section = False
    for line in lines:
        if 'KACIRABILECEGIN' in line.upper() or 'DIP NOT' in line.upper():
            in_section = True
        if in_section and line.strip().startswith('##') and 'KACIR' not in line.upper():
            in_section = False
        if in_section:
            kacirdiklar += line + '\n'

# DELTA
archive_files = sorted(glob.glob('analiz-arşivi/TUPRS-*.md'))
delta = ''
if len(archive_files) >= 2:
    prev = archive_files[-2]
    with open(prev, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    curr_lines = set(str(reports).split('\n'))
    prev_lines = set(prev_content.split('\n'))
    added = curr_lines - prev_lines
    removed = prev_lines - curr_lines
    if added or removed:
        delta = '### Degisenler:\n'
        for a in sorted(added)[:15]:
            delta += '+ {a}\n'
        for r in sorted(removed)[:8]:
            delta += '- {r}\n'
    else:
        delta = 'Onceki rapordan belirgin degisiklik yok.'
elif len(archive_files) == 1:
    delta = 'Ilk analiz -- delta yok.'

# DEGERLEME (again for output)
deg = ''
if os.path.exists('veri/degerleme.json'):
    with open('veri/degerleme.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    v = d.get('valuation', {})
    deg = '- P/E: {v.get("p_e", "-")} | EV/FAVOK: {v.get("ev_favok", "-")} | P/S: {v.get("p_s", "-")}\n'
    deg += '- FAVOK Marji: {v.get("favok_margin", "-")}% | Net Marj: {v.get("net_margin", "-")}%\n'
    deg += '- Net Borc/FAVOK: {v.get("net_borc_favok", "-")}x\n'
    if 'fair_price_pe' in v:
        deg += '- Fair Price (P/E): {v["fair_price_pe"]:.2f} TL | Guvenlik Marji: {v.get("safety_margin_pe", "-")}%\n'

# MOATSIZ
moatsiz = ''
if os.path.exists('veri/degerleme_moatsiz.json'):
    with open('veri/degerleme_moatsiz.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    moatsiz = '- Hendeksiz Kontrol: {d.get("hendeksiz_kontrol", {}).get("tum_kriterler_karsilandi", "N/A")}\n'
    if 'fair_value_aralik' in d:
        moatsiz += '- Fair Value Araligi: {d["fair_value_aralik"].get("min", "N/A")} - {d["fair_value_aralik"].get("max", "N/A")} TL\n'

# TEKNIK
teknik_ozet = ''
if os.path.exists('veri/teknik_pozisyon.json'):
    with open('veri/teknik_pozisyon.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    teknik_ozet = '- Trend: {d.get("ana_trend", "N/A")} | RSI: {d.get("indikatorler", {}).get("rsi", "N/A")} | R/R: {d.get("risk_odul", "N/A")}\n'
    teknik_ozet += '- Stop: {d.get("stop_loss", "N/A")} | Giris: {d.get("entry", "N/A")} | Hedef: {d.get("target1", "N/A")}\n'

# HENDEK
hendek_ozet = ''
if os.path.exists('veri/hendek_skor.json'):
    with open('veri/hendek_skor.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    hendek_ozet = '- Hendek Skoru: {d.get("skor", "N/A")}/100 -> {"HENDEKLI" if d.get("skor", 0) >= 50 else "HENDEKSIZ"}\n'

moatsiz = moatsiz or ''
teknik_ozet = teknik_ozet or ''
hendek_ozet = hendek_ozet or ''

# KACIRDIKLARIN
kacirdiklar = ''
if 'bilanco-ajani' in reports:
    lines = reports['bilanco-ajani'].split('\n')
    in_section = False
    for line in lines:
        if 'KACIRABILECEGIN' in line.upper() or 'DIP NOT' in line.upper():
            in_section = True
        if in_section and line.strip().startswith('##') and 'KACIR' not in line.upper():
            in_section = False
        if in_section:
            kacirdiklar += line + '\n'

# DELTA
archive_files = sorted(glob.glob('analiz-arşivi/TUPRS-*.md'))
delta = ''
if len(archive_files) >= 2:
    prev = archive_files[-2]
    with open(prev, 'r', encoding='utf-8') as f:
        prev_content = f.read()
    curr_lines = set(str(reports).split('\n'))
    prev_lines = set(prev_content.split('\n'))
    added = curr_lines - prev_lines
    removed = prev_lines - curr_lines
    if added or removed:
        delta = '### Degisenler:\n'
        for a in sorted(added)[:15]:
            delta += '+ {a}\n'
        for r in sorted(removed)[:8]:
            delta += '- {r}\n'
    else:
        delta = 'Onceki rapordan belirgin degisiklik yok.'
elif len(archive_files) == 1:
    delta = 'Ilk analiz -- delta yok.'

# CIKTI
output = f'''# TUPRS ANALIZ RAPORU -- 2026-10-30

## KARAR KUTUSU: ZAYIF

---

## 1. SEKTOR MAKRO (Katman 1)
{reports.get("sektor-ajani", "RAPOR YOK")}

---

## 2. HIKAYE VE STRATEJI (Katman 2)
{reports.get("hikaye-ajani", "RAPOR YOK")}

---

## 3. HENDEK (MOAT) -- 5/10 YIL (Katman 3)
{reports.get("hendek-ajani", "RAPOR YOK")}

---

## 4. RAKIP DERIN ANALIZI (Katman 4)
{reports.get("rakip-ajani", "RAPOR YOK")}

---

## 5. YONETIM / HAKIM ORTAK (Katman 5)
{reports.get("yonetim-ajani", "RAPOR YOK")}

---

## 6. SEKTOR vs SIRKET KARSILASTIRMASI (Katman 6)
{reports.get("sektor-karsilastirma-ajani", "RAPOR YOK")}

---

## 7. DUYARLILIK VE RISK (Katman 7)
{reports.get("risk-ajani", "RAPOR YOK")}

---

## 8. DEGERLEME (Katman 8)
{reports.get("degerleme-ajani", "RAPOR YOK")}

{moatsiz}
{teknik_ozet}
{hendek_ozet}

---

## 9. BILANCO DERIN OKUMA (Katman 9)
{reports.get("bilanco-ajani", "RAPOR YOK")}

---

## 10. TEKNIK ANALIZ VE POZISYON (Katman 10)
{reports.get("teknik-ajani", "RAPOR YOK")}

---

## SENIN KACIRDIKLARIN (KAP Dip Notlari)
{kacirdiklar if kacirdiklar else 'Bilanco raporunda dip not bolumu bulunamadi.'}

---

## DELTA (Onceki Rapora Gore)
{delta}

---

*Bu analiz bilgi amaclidir; yatirim tavsiyesi degildir.*
'''

archive_path = 'analiz-arşivi/TUPRS-2026-10-30.md'
with open(archive_path, 'w', encoding='utf-8') as f:
    f.write(output)

print('SENTEZ TAMAM:', archive_path)
print('KARAR: ZAYIF')