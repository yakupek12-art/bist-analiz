try:
    from pykap import BISTCompany
    import pdfplumber, requests, re, io
    
    # THYAO için company oid bul
    from pykap import get_bist_companies
    companies = get_bist_companies()
    thy = companies[companies['symbol'] == 'THYAO']
    if len(thy) > 0:
        oid = thy.iloc[0]['mkkMemberOid']
        company = BISTCompany(oid)
        disclosures = company.get_disclosures(limit=50)
        
        keywords = ['teminat', 'rehin', 'ipotek', 'dava', 'ilgili taraf', 'kambiyo', 'hedge', 'musteri yogun', 'tek musteri', 'ertelenmis vergi', 'diger faaliyet gelirl', 'tedarikci', 'tek tedarikci', 'taahhut', 'sozlesme']
        
        with open('veri/kap_bildirim.txt', 'w', encoding='utf-8') as f:
            for d in disclosures:
                f.write('{} | {} | {}\n'.format(d.title, d.date, d.url))
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
                                idx = full_text.lower().index(kw.lower())
                                start = max(0, idx - 300)
                                end = min(len(full_text), idx + 500)
                                snippet = full_text[start:end].strip()
                                f.write('  >> DIP NOT [{}]: {}\n'.format(kw.upper(), snippet))
                    except Exception as e:
                        f.write('  >> PDF HATA: {}\n'.format(e))
        print('KAP:', len(disclosures), 'bildirim')
    else:
        print('THYAO bulunamadi')
except Exception as e:
    print('KAP HATA:', e)
    with open('veri/kap_bildirim.txt', 'w') as f:
        f.write('KAP veri cekilemedi: {}\n'.format(e))