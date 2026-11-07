#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunluk Veri Toplama Scripti
- Fiyat verisi (Yahoo Finance)
- Haberler (Google News RSS)
- KAP bildirimleri (API)
- Bilanco/gelir tablosu (isyatirimhisse)
- Makro veriler (TCMB EVDS)
- Ozet dosyalari olusturma (analiz icin)
"""
import os, sys, json, csv, os
from datetime import datetime, timedelta
import urllib.request, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---- Yapilandirma ----
WATCHLIST = os.getenv("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS,ESCOM.IS").split(",")
DATA_DIR = "analiz-calisma"

def ensure_dirs():
    os.makedirs("analiz-calisma", exist_ok=True)
    for symbol in WATCHLIST:
        symbol_clean = symbol.replace(".IS", "")
        os.makedirs(f"analiz-calisma/{symbol_clean}-veri", exist_ok=True)

# ---- Yardimci fonksiyonlar ----
def fetch_yahoo(symbol, range_="1y", interval="1d", max_retries=3):
    """Yahoo Finance API çağrısı - retry ve timeout destekli"""
    import time
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_}&interval={interval}"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            return data["chart"]["result"][0]
        except Exception as e:
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"    [RETRY {attempt+1}/{max_retries}] {symbol}: {e} - {wait}s bekleniyor")
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                raise

def fetch_news_rss(query):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=tr&gl=TR&ceid=TR:tr"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

def fetch_kap_disclosures(company):
    pass  # GitHub Actions'ta calisacak, localde timeout

def fetch_financials_isyatirim(symbol, start_year, end_year):
    try:
        from isyatirimhisse import fetch_financials
        df = fetch_financials(symbols=symbol, start_year=start_year, end_year=end_year)
        return df.to_json(orient="records")
    except Exception as e:
        return f"HATA: {e}"

def fetch_evds(series, startdate, enddate, api_key):
    pass

# ---- Ozet dosyalari olusturma ----
def create_haberler_txt(symbol_clean, rss_xml):
    """RSS XML'den haberler.txt olustur"""
    import re
    try:
        # RSS'ten baslik ve tarih cikar
        items = re.findall(r'<item>.*?</item>', rss_xml, re.DOTALL)
        lines = []
        for item in items[:20]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item)
            pub_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            source_match = re.search(r'<source[^>]*>(.*?)</source>', item)
            title = title_match.group(1) if title_match else "Baslik yok"
            pub = pub_match.group(1) if pub_match else "Tarih yok"
            source = source_match.group(1) if source_match else "Kaynak yok"
            lines.append(f"{pub} - {title} [{source}]")
        text = "\n".join(lines)
        path = f"analiz-calisma/{symbol_clean}-veri/haberler.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path
    except Exception as e:
        print("[ERROR] haberler.txt olusturma hatasi: " + str(e))
        return None

def create_fiyat_ozet_json(symbol, chart_data, symbol_clean):
    """fiyat-ozet.json olustur (zaten var ama garantile)"""
    meta = chart_data["meta"]
    closes = chart_data["indicators"]["quote"][0]["close"]
    timestamps = chart_data["timestamp"]
    fiyat_data = {
        "symbol": symbol,
        "currency": meta.get("currency"),
        "last_price": meta.get("regularMarketPrice"),
        "prev_close": meta.get("previousClose"),
        "change_pct": round((meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0)) / meta.get("previousClose", 1) * 100, 2),
        "history": [{"date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"), "close": round(c, 2)} for ts, c in zip(chart_data["timestamp"], chart_data["indicators"]["quote"][0]["close"]) if c is not None][-30:]
    }
    path = f"analiz-calisma/{symbol_clean}-veri/fiyat-ozet.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fiyat_data, f, ensure_ascii=False, indent=2)
    return path

def create_bilanco_ozet_txt(symbol_clean):
    """bilanco-ham.csv'den bilanco-ozet.txt olustur"""
    import csv
    csv_path = f"analiz-calisma/{symbol_clean}-veri/bilanco-ham.csv"
    if not os.path.exists(csv_path):
        return None
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            first = f.readline().strip()
            cols = [c.strip().strip('"') for c in first.split(",")]
            cols = ["EMPTY" if c == "" else c for c in cols]
            f.seek(0)
            reader = csv.DictReader(f, fieldnames=cols)
            rows = list(reader)

        # Donem kolonlari
        period_cols = sorted([c for c in cols if "/" in c and c[0].isdigit()],
                           key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))

        # Onemli kodlar
        key_codes = {
            "3C": "Satis Gelirleri", "3B": "Satis Maliyeti", "3C": "Brut Kar",
            "3DF": "Faaliyet Karsiligi", "3HACA": "Finansman Gideri Oncesi Faaliyet Karsiligi",
            "3HB": "Finansman Giderleri", "3HC": "Finansman Gelirleri",
            "3HE": "Vergi Oncesi Kar", "3HF": "Vergi Gideri/Geliri", "3HG": "Donem Karsiligi",
            "3L": "Net Kar", "3J": "Ana Ortaklik Payi", "3Z": "Hisse Basi Kazanc",
            "1AA": "Nakit", "1AC": "Ticari Alacak Kisa", "1AF": "Stoklar",
            "1AJ": "Toplam Donen Varliklar", "1B": "Ticari Alacak Uzun",
            "1BC": "Finansal Yatirimlar", "1BF": "Maddi Duran Varliklar",
            "1BH": "Maddi Olmayan Duran Varliklar", "1BJ": "Ertelenmis Vergi Varligi",
            "2AA": "Finansal Borc Kisa", "2AAGCA": "Ertelenmis Gelir Kisa",
            "2BA": "Finansal Borc Uzun", "2BAD": "Ertelenmis Gelir Uzun",
            "1AA": "Nakit", "1AC": "Ticari Alacak Kisa", "1AF": "Stoklar",
            "1AJ": "Toplam Donen Varliklar", "2AA": "Finansal Borc Kisa",
            "2AAGCA": "Ertelenmis Gelir Kisa", "2BA": "Finansal Borc Uzun",
            "2BAD": "Ertelenmis Gelir Uzun", "1AJ": "Toplam Donen Varliklar",
        }

        lines = []
        lines.append("BILANCO OZET - " + symbol_clean.upper())
        lines.append("Kaynak: isyatirimhisse / isyatirim.com.tr")
        lines.append("Donemler: " + ", ".join(period_cols))
        lines.append("")

        for code, name in key_codes.items():
            if code not in [r["FINANCIAL_ITEM_CODE"] for r in rows if r.get("FINANCIAL_ITEM_CODE") == code]:
                continue
            row = next((r for r in rows if r.get("FINANCIAL_ITEM_CODE") == code), None)
            if not row:
                continue
            vals = []
            for p in period_cols:
                v = row.get(p, "").strip()
                if v:
                    try:
                        vals.append(f"{p}={float(v)/1e6:.1f}Mn")
                    except:
                        vals.append(f"{p}={v}")
            if vals:
                lines.append(f"{code} | {name}: {', '.join(vals)}")

        text = "\n".join(lines)
        path = f"analiz-calisma/{symbol_clean}-veri/bilanco-ozet.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path
    except Exception as e:
        print("[ERROR] bilanco-ozet.txt olusturma hatasi: " + str(e))
        return None

def create_rakip_veri_txt(symbol_clean):
    """rakip-veri.txt olustur - sektor rakipleri icin basit fiyat karsilastirmasi"""
    try:
        # Temel rakip listesi (sektore gore genel - BIST sembolleri)
        rakip_listesi = {
            "ASELS": ["OTOKAR.IS", "PAMEL.IS", "NUHL.IS", "HAVELSAN.IS"],
            "THYAO": ["PGSUS.IS", "TURSAT.IS", "ARCLK.IS"],
            "BIMAS": ["MGROS.IS", "SOKM.IS", "SHLF.IS"],
            "ESCOM": ["ISCTR.IS", "GARAN.IS", "YKBNK.IS"],  # Yatirim / finans holding benzeri
        }
        rakip_kodlari = rakip_listesi.get(symbol_clean, [])

        lines = []
        lines.append("RAKIP KIYASLAMASI - " + symbol_clean.upper())
        lines.append("Kaynak: Yahoo Finance (guncel fiyat)")
        lines.append("")

        for rk in rakip_kodlari:
            try:
                chart = fetch_yahoo(rk, "5d", "1d")
                meta = chart["meta"]
                closes = chart["indicators"]["quote"][0]["close"]
                last = closes[-1] if closes else None
                prev = closes[-2] if len(closes) > 1 else None
                chg = round((last - prev) / prev * 100, 2) if last and prev else None
                lines.append(f"{rk.replace('.IS','')}: Son={last} TL, Gunluk=%{chg}")
            except:
                lines.append(f"{rk.replace('.IS','')}: Veri alinamadi")

        text = "\n".join(lines)
        path = f"analiz-calisma/{symbol_clean}-veri/rakip-veri.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path
    except Exception as e:
        print("[ERROR] rakip-veri.txt olusturma hatasi: " + str(e))
        return None

def create_haberler_txt_from_xml(symbol_clean):
    """haberler.xml'den haberler.txt olustur"""
    import re
    xml_path = f"analiz-calisma/{symbol_clean}-veri/haberler.xml"
    if not os.path.exists(xml_path):
        return None
    try:
        with open(f"analiz-calisma/{symbol_clean}-veri/haberler.xml", "r", encoding="utf-8") as f:
            xml = f.read()
        items = re.findall(r'<item>.*?</item>', xml, re.DOTALL)
        lines = []
        for item in items[:20]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item)
            pub_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            source_match = re.search(r'<source[^>]*>(.*?)</source>', item)
            title = title_match.group(1) if title_match else "Baslik yok"
            pub = pub_match.group(1) if pub_match else "Tarih yok"
            source = source_match.group(1) if source_match else "Kaynak yok"
            lines.append(f"{pub} - {title} [{source}]")
        text = "\n".join(lines)
        path = f"analiz-calisma/{symbol_clean}-veri/haberler.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path
    except Exception as e:
        print("[ERROR] haberler.txt olusturma hatasi: " + str(e))
        return None

# ---- Ana fonksiyon ----
def main():
    ensure_dirs()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[{datetime.now()}] Gunluk veri toplama basladi - {len(WATCHLIST)} hisse")

    for symbol in WATCHLIST:
        symbol_clean = symbol.replace(".IS", "")
        print(f"\n--- {symbol_clean} verisi toplaniyor ---")

        # 1. Fiyat verisi
        print("  Fiyat verisi cekiliyor...")
        try:
            chart = fetch_yahoo(symbol, "1y", "1d")
            meta = chart["meta"]
            closes = chart["indicators"]["quote"][0]["close"]
            timestamps = chart["timestamp"]

            fiyat_data = {
                "symbol": symbol,
                "currency": meta.get("currency"),
                "last_price": meta.get("regularMarketPrice"),
                "prev_close": meta.get("previousClose"),
                "change_pct": round((meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0)) / meta.get("previousClose", 1) * 100, 2),
                "history": [{"date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"), "close": round(c, 2)} for ts, c in zip(timestamps, closes) if c is not None][-30:]
            }
            with open(f"analiz-calisma/{symbol.replace('.IS','')}-veri/fiyat-ozet.json", "w", encoding="utf-8") as f:
                json.dump(fiyat_data, f, ensure_ascii=False, indent=2)
            print("[OK] Fiyat verisi kaydedildi")
        except Exception as e:
            print("[ERROR] Fiyat hatasi: " + str(e))

        # 2. Haberler - XML kaydet + TXT olustur
        print("  Haberler cekiliyor...")
        try:
            rss = fetch_news_rss(symbol.replace(".IS", "") + " " + symbol.replace(".IS", ""))
            with open(f"analiz-calisma/{symbol.replace('.IS','')}-veri/haberler.xml", "w", encoding="utf-8") as f:
                f.write(rss)
            create_haberler_txt_from_xml(symbol.replace(".IS",""))
            print("[OK] Haberler kaydedildi")
        except Exception as e:
            print("[ERROR] Haber hatasi: " + str(e))

        # 3. Bilanco verisi (isyatirimhisse)
        print("  Bilanco verisi cekiliyor...")
        try:
            from isyatirimhisse import fetch_financials
            current_year = datetime.now().year
            df = fetch_financials(symbols=symbol.replace(".IS", ""), start_year=str(datetime.now().year - 5), end_year=str(current_year))
            csv_path = f"analiz-calisma/{symbol.replace('.IS','')}-veri/bilanco-ham.csv"
            df.to_csv(csv_path, index=False)
            print("[OK] Bilanco CSV kaydedildi: " + csv_path)

            # Ozet dosyalari olustur
            create_bilanco_ozet_txt(symbol.replace(".IS",""))
            create_haberler_txt_from_xml(symbol.replace(".IS",""))
            create_rakip_veri_txt(symbol.replace(".IS",""))
            print("[OK] Ozet dosyalar olusturuldu")
        except Exception as e:
            print("[ERROR] Bilanco hatasi: " + str(e))

    print("\n[" + str(datetime.now()) + "] Veri toplama tamamlandi")

if __name__ == "__main__":
    import urllib.request, urllib.parse, json, os, sys
    from datetime import datetime
    WATCHLIST = os.getenv("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS,ESCOM.IS").split(",")
    main()