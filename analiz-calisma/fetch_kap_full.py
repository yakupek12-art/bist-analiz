#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAP Tam Veri Çekici — Bildirimler + PDF Dip Not Parse
"""

import sys, os, json, re, io, requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from pykap import BISTCompany
except ImportError:
    print("pykap kurulu değil: pip install pykap")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("pdfplumber kurulu değil: pip install pdfplumber")
    sys.exit(1)

# Dip not keyword'leri
KEYWORDS = [
    'teminat', 'rehin', 'ipotek', 'dava', 'ilgili taraf', 'kambiyo', 'hedge',
    'müşteri yoğun', 'tek müşteri', 'ertelenmiş vergi', 'diğer faaliyet gelirl',
    'tedarikçi', 'tek tedarikçi', 'taahhüt', 'sözleşme', 'sermaye artırımı',
    'ikraz', 'bedelsiz', 'geri alma', 'yönetim kurulu', 'genel kurul',
    'teminat serbest', 'ipotek serbest', 'rehin serbest'
]

def fetch_kap_full(symbol):
    """KAP'tan tam veri çek"""
    try:
        company = BISTCompany(symbol)
        all_disclosures = []
        
        # Tüm bildirim tipleri
        for dtype in ['FAR', 'KYUR', 'SUR', 'KDP', 'DEG', 'SYI', 'UNV']:
            try:
                disclosures = company.get_disclosures(dtype)
                all_disclosures.extend(disclosures)
            except Exception as e:
                pass
        
        print(f"Toplam bildirim: {len(all_disclosures)}")
        
        output_lines = []
        dip_not_count = 0
        
        for d in all_disclosures[:80]:  # İlk 80 bildirim
            idx = d.get('disclosureIndex')
            title = d.get('title', '')
            date = d.get('publishDate', '')
            url = f'https://www.kap.org.tr/tr/Bildirim/{idx}'
            
            output_lines.append(f'{title} | {date} | {url}')
            
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
                    
                    for kw in KEYWORDS:
                        matches = list(re.finditer(kw, full_text, re.IGNORECASE))
                        for match in matches[:3]:  # Her keyword için max 3 eşleşme
                            idx_kw = match.start()
                            start = max(0, idx_kw - 300)
                            end = min(len(full_text), idx_kw + 500)
                            snippet = full_text[start:end].strip()
                            output_lines.append(f'  >> DİP NOT [{kw.upper()}]: {snippet}')
                            dip_not_count += 1
            except Exception as e:
                output_lines.append(f'  >> PDF HATA: {e}')
        
        # Çıktı dosyalarını yaz
        with open('veri/kap_bildirim.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        # Yatırım planları ayrı dosya
        yatirim_lines = []
        for line in output_lines:
            if any(kw in line.lower() for kw in ['yatırım', 'yatırım', 'tesis', 'kapasite', 'yeni', 'genişleme', 'modernizasyon', 'ar-ge', 'ar ge', 'proje']):
                yatirim_lines.append(line)
        
        with open('veri/kap_yatirim_planlari.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(yatirim_lines) if yatirim_lines else 'Yatırım planı bulunamadı')
        
        # Dip notları ayrı dosya
        dip_lines = [l for l in output_lines if l.startswith('  >> DİP NOT')]
        with open('veri/kap_dip_notlari.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(dip_lines))
        
        # Hikaye verisi için özet
        hikaye_summary = {
            'sirket': symbol,
            'toplam_bildirim': len(all_disclosures),
            'dip_not_sayisi': dip_not_count,
            'son_bildirim_tarihi': all_disclosures[0].get('publishDate', '') if all_disclosures else '',
            'bildirim_turleri': list(set(d.get('disclosureType') for d in all_disclosures if d.get('disclosureType')))
        }
        
        with open('veri/hikaye_veri.json', 'w', encoding='utf-8') as f:
            json.dump(hikaye_summary, f, ensure_ascii=False, indent=2)
        
        print(f"KAP analizi tamamlandı: {len(all_disclosures)} bildirim, {dip_not_count} dip not")
        
    except Exception as e:
        print(f"KAP HATA: {e}")
        with open('veri/kap_bildirim.txt', 'w') as f:
            f.write(f'KAP veri cekilemedi: {e}')

if __name__ == '__main__':
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS'
    fetch_kap_full(symbol)