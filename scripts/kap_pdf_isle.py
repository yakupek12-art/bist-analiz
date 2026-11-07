#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAP PDF İşleme Scripti - GitHub Actions'ta çalışır
"""
import os, sys, json, urllib.request, re, io
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WATCHLIST = os.getenv("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS").split(",")

def fetch_disclosure_ids(company):
    url = 'https://www.kap.org.tr/tr/api/disclosures'
    data = {"companyQuery": {"text": company.replace(".IS", "").replace("AS", "")}, "submit": "Getir"}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except Exception as e:
        print(f"  KAP API hatası: {e}")
        return []

def download_pdf(disclosure_id):
    url = f"https://www.kap.org.tr/tr/api/BildirimPdf/{disclosure_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as e:
        print(f"  PDF indirme hatası ({disclosure_id}): {e}")
        return None

def extract_pdf_text(pdf_bytes):
    try:
        import pdfplumber, io
        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: text += t + "\n"
        return text
    except Exception as e:
        print(f"  PDF metin çıkarma hatası: {e}")
        return ""

def extract_findings(text):
    import re
    patterns = {
        "teminat": r"(teminat|rehin|ipotek|garanti\s+verilen)",
        "dava": r"(dava|icra|hukuki\s+içtihat|mahkeme)",
        "ilgili_taraf": r"(ilgili\s+taraf|bağlı\s+ortaklık|kontrol|ana\s+ortağ)",
        "kambiyo": r"(kambiyo|döviz\s+pozisyon|hedge|forward|swap|opsiyon|kur\s+risk)",
        "taahhut": r"(taahhüt|sözleşme|yatırım\s+taahhüdü|sipariş\s+taahhüdü)",
        "musteri_yogunlugu": r"(müşteri\s+yoğun|tek\s+müşteri|ana\s+müşteri|ihale|kamu\s+ihalesi)",
        "finansal_kirala": r"(finansal\s+kiralama|IFRS\s+16)",
        "ozkaynak_ozel": r"(öz\s+kaynak|kâr\s+zarar|geri\s+alım|bedelsiz|sermaye\s+artırımı)",
    }
    findings = {}
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            findings[name] = len(matches)
    return findings

def main():
    WATCHLIST = os.getenv("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS").split(",")
    print(f"[{datetime.now()}] KAP PDF işleme başladı")

    for symbol in WATCHLIST:
        company = symbol.replace(".IS", "").replace("AS", "")
        print(f"\n--- {symbol} KAP PDF işleniyor ---")

        disclosures = fetch_disclosure_ids(company)
        print(f"  {len(disclosures)} bildirim bulundu")

        results = []
        for disc in disclosures[:5]:
            disc_id = disc.get("disclosureId")
            title = disc.get("disclosureTitle", "")
            date = disc.get("disclosureDate", "")
            print(f"  İşleniyor: {disc_id} - {title[:50]}")

            pdf_bytes = download_pdf(disc_id)
            if not pdf_bytes:
                continue

            text = extract_pdf_text(pdf_bytes)
            findings = extract_findings(text)

            results.append({
                "disclosureId": disc_id,
                "title": title,
                "date": date,
                "findings": findings,
                "text_length": len(text)
            })

        symbol_clean = symbol.replace(".IS", "")
        os.makedirs(f"analiz-calisma/{symbol.replace('.IS','')}-veri/kap-dip-notlar", exist_ok=True)
        with open(f"analiz-calisma/{symbol.replace('.IS','')}-veri/kap-dip-notlar/kap-dip-notlar.json", "w", encoding="utf-8") as f:
            json.dump({
                "symbol": symbol,
                "processed_at": datetime.now().isoformat(),
                "processed_count": len(results),
                "disclosures": results
            }, f, ensure_ascii=False, indent=2)

        print(f"  ✓ {len(results)} bildirim işlendi, kaydedildi")

    print(f"\n[{datetime.now()}] KAP PDF işleme tamamlandı")

if __name__ == "__main__":
    import os, sys, json, urllib.request, datetime
    main()