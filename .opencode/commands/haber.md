---
name: haber
description: Hızlı haber & gündem taraması — sadece haber-ajani çalıştırır
---

# /haber — HIZLI HABER ÖZETİ

## KULLANIM
```
/haber ASELS.IS
/haber THYAO.IS
```

---

## ADIM 1: VERİ TOPLAMA (Sadece Haber + KAP)

```bash
SEMBOL="$1"
SEMBOL_CLEAN="${SEMBOL/.IS/}"

mkdir -p veri

# Haber (Google News RSS)
curl -sS -m 15 "https://news.google.com/rss/search?q=${SEMBOL_CLEAN}&hl=tr&gl=TR&ceid=TR:tr" > veri/haberler.xml
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

# KAP Bildirimleri (son 30 gün, dip not parse)
python3 -c "
try:
    from pykap import Kap
    import pdfplumber, requests, re, io
    k = Kap()
    company = k.get_company(SEMBOL_CLEAN)
    disclosures = company.get_disclosures(limit=30)
    keywords = ['teminat', 'rehin', 'ipotek', 'dava', 'ilgili taraf', 'kambiyo', 'hedge', 'müşteri yoğun', 'tek müşteri', 'ertelenmiş vergi', 'diğer faaliyet gelirl', 'tedarikçi', 'tek tedarikçi']
    with open('veri/kap_bildirim.txt', 'w', encoding='utf-8') as f:
        for d in disclosures:
            f.write(f'{d.title} | {d.date} | {d.url}\n')
            if d.pdf_url:
                try:
                    resp = requests.get(d.pdf_url, timeout=20)
                    pdf = pdfplumber.open(io.BytesIO(resp.content))
                    full_text = ''
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t: full_text += t + '\n'
                    for kw in keywords:
                        if re.search(kw, full_text, re.I):
                            idx = full_text.lower().index(kw.lower())
                            start = max(0, idx - 300)
                            end = min(len(full_text), idx + 500)
                            snippet = full_text[start:end].strip()
                            f.write(f'  >> DİP NOT [{kw.upper()}]: {snippet}\n')
                except:
                    pass
except Exception as e:
    with open('veri/kap_bildirim.txt', 'w') as f:
        f.write(f'KAP veri çekilemedi: {e}\n')
"
```

---

## ADIM 2: HABER AJANI ÇAĞRILIR

```bash
opencode run --agent haber-ajani -f veri/haberler.txt -f veri/kap_bildirim.txt "Analiz et ve rapor yaz"
```

---

## ÇIKTI
Konsola doğrudan haber raporu basılır. Arşive yazmaz, delta yapmaz, diğer ajanları çalıştırmaz.

**Kullanım senaryosu:** Gün içinde hızlıca "şu an ne var?" diye bakmak için.