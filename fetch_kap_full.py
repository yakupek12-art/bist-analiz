import requests, re, io, pdfplumber
from pykap import BISTCompany

company = BISTCompany('THYAO')

# Tüm disclosure tipleri
all_disclosures = []
for dtype in ['FAR', 'KYUR', 'SUR', 'KDP', 'DEG', 'SYI', 'UNV']:
    try:
        d = company.get_disclosures(dtype)
        all_disclosures.extend(d)
    except:
        pass

print('Toplam bildirim:', len(all_disclosures))

keywords = ['teminat', 'rehin', 'ipotek', 'dava', 'ilgili taraf', 'kambiyo', 'hedge', 
            'musteri yogun', 'tek musteri', 'ertelenmis vergi', 'diger faaliyet gelirl', 
            'tedarikci', 'tek tedarikci', 'taahhut', 'sozlesme']

with open('veri/kap_bildirim.txt', 'w', encoding='utf-8') as f:
    for d in all_disclosures[:50]:  # İlk 50
        idx = d.get('disclosureIndex')
        title = d.get('title', '')
        date = d.get('publishDate', '')
        url = f'https://www.kap.org.tr/tr/Bildirim/{idx}'
        
        f.write(f'{title} | {date} | {url}\n')
        
        # PDF indir ve parse et
        pdf_url = f'https://www.kap.org.tr/tr/api/BildirimPdf/{idx}'
        try:
            resp = requests.get(pdf_url, timeout=30)
            if resp.status_code == 200 and 'pdf' in resp.headers.get('Content-Type', ''):
                pdf = pdfplumber.open(io.BytesIO(resp.content))
                full_text = ''
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: full_text += t + '\n'
                
                for kw in keywords:
                    if re.search(kw, full_text, re.I):
                        idx_kw = full_text.lower().index(kw.lower())
                        start = max(0, idx_kw - 300)
                        end = min(len(full_text), idx_kw + 500)
                        snippet = full_text[start:end].strip()
                        f.write(f'  >> DIP NOT [{kw.upper()}]: {snippet}\n')
        except Exception as e:
            f.write(f'  >> PDF HATA: {e}\n')

print('KAP bildirim + dip not kaydedildi')