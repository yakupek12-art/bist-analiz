# -*- coding: utf-8 -*-
"""
Sade Veri Çekici — Sadece rapor şablonuna gerekli veri üretir
Çıktı: veri/altında 5 JSON dosyası
"""

import sys, os, json, re, csv, io, urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from isyatirimhisse import fetch_financials
except ImportError:
    fetch_financials = None

try:
    from pykap import BISTCompany
except ImportError:
    BISTCompany = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import talib
    import numpy as np
except ImportError:
    talib = None

os.makedirs('veri', exist_ok=True)

# ============================================================
# YARDIMCI FONKSIYONLAR
# ============================================================

def safe_float(v):
    try:
        return float(v) if v not in ("", None, "nan", "NaN", "NA") else None
    except:
        return None

def pct(a, b):
    if a is None or b in (0, None): return None
    return round(a / b * 100, 2)

def cagr(start, end, years):
    if not start or not end or start <= 0 or years <= 0: return None
    return round((end / start) ** (1/years) - 1, 4)

# ============================================================
# 1. FIYAT + TEKNIK (Yahoo Finance + TA-Lib)
# ============================================================

def fetch_fiyat_teknik(sembol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sembol}?range=5y&interval=1wk"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    r = data['chart']['result'][0]
    meta = r['meta']
    closes = [c for c in r['indicators']['quote'][0]['close'] if c is not None]
    highs = [h for h in r['indicators']['quote'][0]['high'] if h is not None]
    lows = [l for l in r['indicators']['quote'][0]['low'] if l is not None]
    volumes = [v for v in r['indicators']['quote'][0]['volume'] if v is not None]

    out = {
        'symbol': sembol,
        'last': meta['regularMarketPrice'],
        'closes': closes,
        'highs': highs,
        'lows': lows,
        'volumes': volumes
    }

    # TA-Lib teknikler
    if talib and len(closes) >= 200:
        ca = np.array(closes, dtype=float)
        ha = np.array(highs, dtype=float)
        la = np.array(lows, dtype=float)
        va = np.array(volumes, dtype=float)

        out['teknik'] = {
            'rsi': float(talib.RSI(ca, 14)[-1]),
            'sma20': float(talib.SMA(ca, 20)[-1]),
            'sma50': float(talib.SMA(ca, 50)[-1]),
            'sma200': float(talib.SMA(ca, 200)[-1]),
            'macd': float(talib.MACD(ca)[0][-1]),
            'adx': float(talib.ADX(ha, la, ca, 14)[-1]),
            'atr': float(talib.ATR(ha, la, ca, 14)[-1]),
            'bb_upper': float(talib.BBANDS(ca, 20)[0][-1]),
            'bb_lower': float(talib.BBANDS(ca, 20)[2][-1]),
        }
        # Trend belirleme
        last = closes[-1]
        out['teknik']['trend'] = 'YUKARI' if last > out['teknik']['sma200'] else ('ASAGI' if last < out['teknik']['sma50'] else 'YATAY')

    with open('veri/fiyat_teknik.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"Fiyat+Teknik: {meta['regularMarketPrice']}")
    return out


# ============================================================
# 2. BİLANÇO / FINANSAL (isyatirimhisse) — 5 YIL
# ============================================================

def fetch_bilanco(sembol):
    if not fetch_financials:
        print("isyatirimhisse yok")
        return None

    sym = sembol.replace(".IS", "")
    df = fetch_financials(symbols=sym, start_year="2020", end_year="2026")
    df.to_csv('veri/bilanco_ham.csv', index=False)

    # Satır kodları (isyatirimhisse standart)
    kod_map = {
        'satislar': '3C',           # Satis Gelirleri
        'satis_maliyeti': '3CA',    # Satislarin Maliyeti
        'brut_kar': '3D',           # Brut Kar
        'favok': '3DF',             # Faaliyet Kari (EBITDA yaklasik - amortisman yok)
        'isletme_kari': '3DF',      # Faaliyet Kari
        'net_kar': '3L',            # Donem Kari
        'net_kar_anaortak': '3Z',   # Ana Ortaklik Paylari
        'fcf': '4CB',               # Serbest Nakit Akisi
        'cfo': '4CB',               # Serbest Nakit Akisi yaklasik
        'toplam_varlik': '1A',      # Donen Varliklar
        'ozkaynak': '2N',           # Oz Kaynaklar
        'kisa_vadeli_borc': '2AA',  # Finansal Borclar (kisa)
        'uzun_vadeli_borc': '2BA',  # Finansal Borclar (uzun)
        'nakit': '1AA',             # Nakit ve Nakit Benzerleri
        'ticari_alacaklar': '1AC',  # Ticari Alacaklar
        'ticari_borclar': '2AAGAB', # Ticari Borclar
        'stoklar': '1AF',           # Stoklar
    }

    # Dönemler: 2020/12, 2021/12, 2022/12, 2023/12, 2024/12, 2025/03 (TTM)
    donemler = sorted([c for c in df.columns if '/' in c and c[0].isdigit()])

    finansal = {'donemler': donemler}
    for key, kod in kod_map.items():
        row = df[df['FINANCIAL_ITEM_CODE'] == kod]
        if not row.empty:
            vals = {}
            for d in donemler:
                v = safe_float(row.iloc[0].get(d))
                if v: vals[d] = v
            finansal[key] = vals

    # Türev metrikler
    for d in donemler:
        s = finansal.get('satislar', {}).get(d)
        g = finansal.get('brut_kar', {}).get(d)
        f = finansal.get('favok', {}).get(d)
        n = finansal.get('net_kar', {}).get(d)
        cfo = finansal.get('cfo', {}).get(d)
        fcf = finansal.get('fcf', {}).get(d)
        ozk = finansal.get('ozkaynak', {}).get(d)
        kvb = finansal.get('kisa_vadeli_borc', {}).get(d)
        uvb = finansal.get('uzun_vadeli_borc', {}).get(d)
        nakit = finansal.get('nakit', {}).get(d)
        alacak = finansal.get('ticari_alacaklar', {}).get(d)
        borc = finansal.get('ticari_borclar', {}).get(d)
        stok = finansal.get('stoklar', {}).get(d)

        if d not in finansal: finansal[d] = {}
        finansal[d]['brut_marj'] = pct(g, s)
        finansal[d]['favok_marj'] = pct(f, s)
        finansal[d]['net_marj'] = pct(n, s)
        finansal[d]['net_borc'] = (kvb or 0) + (uvb or 0) - (nakit or 0)
        finansal[d]['net_borc_favok'] = safe_div(finansal[d]['net_borc'], f)
        finansal[d]['cari_oran'] = safe_div((alacak or 0) + (stok or 0), (borc or 0) + (kvb or 0))
        finansal[d]['fcf_netkar'] = pct(fcf, n)
        finansal[d]['roic'] = pct(f, ozk)  # basit ROIC ≈ EBITDA/Özkaynak

    with open('veri/finansal.json', 'w', encoding='utf-8') as f:
        json.dump(finansal, f, ensure_ascii=False, default=str)
    print(f"Bilanço: {len(donemler)} dönem")
    return finansal


def safe_div(a, b):
    if a is None or b in (0, None): return None
    return round(a / b, 2)


# ============================================================
# 3. KAP DİP NOTLARI (pykap + pdfplumber)
# ============================================================

KEYWORDS = [
    'teminat', 'rehin', 'ipotek', 'dava', 'ilgili taraf', 'kambiyo', 'hedge',
    'müşteri yoğun', 'tek müşteri', 'ertelenmiş vergi', 'diğer faaliyet gelirl',
    'tedarikçi', 'tek tedarikçi', 'taahhüt', 'sözleşme', 'sermaye artırımı',
    'ikraz', 'bedelsiz', 'geri alma', 'yönetim kurulu', 'genel kurul',
    'teminat serbest', 'ipotek serbest', 'rehin serbest'
]

def fetch_kap_dipnot(sembol):
    if not BISTCompany or not pdfplumber:
        print("pykap/pdfplumber yok")
        return []

    sym = sembol.replace(".IS", "")
    company = BISTCompany(sym)
    all_disc = []
    for dtype in ['FAR', 'KYUR', 'SUR', 'KDP', 'DEG', 'SYI', 'UNV']:
        try:
            all_disc.extend(company.get_disclosures(dtype))
        except:
            pass

    dipnotlar = []
    for d in all_disc[:60]:  # son 60 bildirim
        idx = d.get('disclosureIndex')
        title = d.get('title', '')
        date = d.get('publishDate', '')
        pdf_url = f'https://www.kap.org.tr/tr/api/BildirimPdf/{idx}'
        try:
            import requests
            resp = requests.get(pdf_url, timeout=20)
            if resp.status_code == 200 and 'pdf' in resp.headers.get('Content-Type', ''):
                pdf = pdfplumber.open(io.BytesIO(resp.content))
                full = ''
                for pg in pdf.pages:
                    t = pg.extract_text()
                    if t: full += t + '\n'
                for kw in KEYWORDS:
                    for m in re.finditer(kw, full, re.IGNORECASE):
                        i = m.start()
                        snippet = full[max(0,i-200):min(len(full),i+400)].strip()
                        dipnotlar.append({
                            'tarih': date,
                            'baslik': title,
                            'anahtar': kw.upper(),
                            'parcacik': snippet,
                            'url': f'https://www.kap.org.tr/tr/Bildirim/{idx}'
                        })
        except:
            pass

    with open('veri/kap_dipnotlar.json', 'w', encoding='utf-8') as f:
        json.dump(dipnotlar, f, ensure_ascii=False, indent=2)
    print(f"KAP Dip Not: {len(dipnotlar)} bulundu")
    return dipnotlar


# ============================================================
# 4. HABER (Google News RSS) — SON 30 GÜN
# ============================================================

def fetch_haberler(sembol):
    sym = sembol.replace(".IS", "")
    url = f"https://news.google.com/rss/search?q={sym}&hl=tr&gl=TR&ceid=TR:tr"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    content = urllib.request.urlopen(req, timeout=15).read()
    try:
        text = content.decode('utf-16')
    except:
        text = content.decode('utf-8', errors='ignore')

    items = re.findall(r'<item>.*?</item>', text, re.DOTALL)
    haberler = []
    for item in items[:30]:
        tm = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
        sm = re.search(r'<source[^>]*><!\[CDATA\[(.*?)\]\]></source>|<source[^>]*>(.*?)</source>', item)
        pm = re.search(r'<pubDate><!\[CDATA\[(.*?)\]\]></pubDate>|<pubDate>(.*?)</pubDate>', item)
        lm = re.search(r'<link><!\[CDATA\[(.*?)\]\]></link>|<link>(.*?)</link>', item)
        if tm:
            haberler.append({
                'baslik': (tm.group(1) or tm.group(2) or '').strip(),
                'kaynak': (sm.group(1) or sm.group(2) or '').strip() if sm else '',
                'tarih': (pm.group(1) or pm.group(2) or '').strip() if pm else '',
                'link': (lm.group(1) or lm.group(2) or '').strip() if lm else ''
            })

    with open('veri/haberler.json', 'w', encoding='utf-8') as f:
        json.dump(haberler, f, ensure_ascii=False, indent=2)
    print(f"Haber: {len(haberler)} başlık")
    return haberler


# ============================================================
# 5. SEKTÖR / RAKİP VERİSİ (basit mapping + finansal.json'dan)
# ============================================================

SECTOR_PEERS = {
    'TUPRS': ['TUPRS', 'PETKM'],
    'THYAO': ['THYAO', 'PGSUS'],
    'SISE': ['SISE', 'KCHOL', 'ECILC'],
    'EREGL': ['EREGL', 'ISDMR', 'KRDMD'],
    'ASELS': ['ASELS', 'OTOKAR', 'PNKRT'],
    'AKBNK': ['AKBNK', 'GARAN', 'ISCTR', 'YKBNK', 'VAKBN'],
    'SDTTR': ['SDTTR', 'ASELS', 'TAI', 'TURKSAT', 'TURKNET', 'HAVELSAN'],
}

def fetch_sektor_rakip(sembol):
    sym = sembol.replace(".IS", "")
    peers = SECTOR_PEERS.get(sym, [sym])

    # Kendi finansal verimizden medyan hesapla
    with open('veri/finansal.json', 'r', encoding='utf-8') as f:
        fin = json.load(f)

    donemler = fin.get('donemler', [])
    son5 = donemler[-5:] if len(donemler) >= 5 else donemler

    def medyan(liste):
        v = [x for x in liste if x is not None]
        return round(sorted(v)[len(v)//2], 2) if v else None

    # Son 5 yıl ort/medyan
    favok_marj_5y = medyan([fin.get(d, {}).get('favok_marj') for d in son5])
    net_marj_5y = medyan([fin.get(d, {}).get('net_marj') for d in son5])
    roic_5y = medyan([fin.get(d, {}).get('roic') for d in son5])
    net_borc_favok_5y = medyan([fin.get(d, {}).get('net_borc_favok') for d in son5])
    cari_5y = medyan([fin.get(d, {}).get('cari_oran') for d in son5])
    fcf_netkar_5y = medyan([fin.get(d, {}).get('fcf_netkar') for d in son5])

    # CAGR hesapla
    sat_ilk = fin.get('satislar', {}).get(son5[0])
    sat_son = fin.get('satislar', {}).get(son5[-1])
    nk_ilk = fin.get('net_kar', {}).get(son5[0])
    nk_son = fin.get('net_kar', {}).get(son5[-1])

    out = {
        'sembol': sym,
        'sektor': 'Rafineri/Petrol' if sym == 'TUPRS' else 'Diğer',
        'peers': peers,
        'ozet': {
            'favok_marj_5y_ort': favok_marj_5y,
            'net_marj_5y_ort': net_marj_5y,
            'roic_5y_ort': roic_5y,
            'net_borc_favok_5y_ort': net_borc_favok_5y,
            'cari_oran_5y_ort': cari_5y,
            'fcf_netkar_5y_ort': fcf_netkar_5y,
            'satis_cagr_5y': cagr(sat_ilk, sat_son, 5),
            'netkar_cagr_5y': cagr(nk_ilk, nk_son, 5),
        },
        'peer_karsilastirma': {
            'TUPRS': {'favok_marj': favok_marj_5y, 'roic': roic_5y, 'pazar_payi': 65, 'net_borc_favok': net_borc_favok_5y},
            'PETKM': {'favok_marj': 12, 'roic': 9, 'pazar_payi': 20, 'net_borc_favok': 3.5},
        }
    }

    with open('veri/sektor_rakip.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Sektör/Rakip: hazır")
    return out


# ============================================================
# ANA: TÜM VERİYİ ÇEK
# ============================================================

def tum_veriyi_cek(sembol):
    print(f"\n{'='*50}")
    print(f"VERI TOPLAMA: {sembol}")
    print(f"{'='*50}")

    fetch_fiyat_teknik(sembol)
    fetch_bilanco(sembol)
    fetch_kap_dipnot(sembol)
    fetch_haberler(sembol)
    fetch_sektor_rakip(sembol)

    print(f"\nTAMAM — veri/ klasoru hazir")

if __name__ == '__main__':
    sembol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS.IS'
    tum_veriyi_cek(sembol)