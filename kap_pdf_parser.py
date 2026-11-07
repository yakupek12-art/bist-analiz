"""
KAP PDF Parser - BIST KAP bildirimlerinden dip notları çıkarır.
kap_pdf_isle.py mantığını pipeline'a entegre edilebilir hale getirir.
"""
import os
import sys
import json
import re
import io
import urllib.request
from datetime import datetime
from typing import List, Dict, Any, Optional


WATCHLIST_DEFAULT = ["ASELS.IS", "THYAO.IS", "BIMAS.IS", "ESCOM.IS"]


def fetch_disclosure_ids(company: str) -> List[Dict[str, str]]:
    """KAP API'den şirketin bildirim ID'lerini çeker."""
    url = "https://www.kap.org.tr/tr/api/disclosures"
    data = {
        "companyQuery": {"text": company.replace(".IS", "").replace("AS", "")},
        "submit": "Getir",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except Exception as e:
        print(f"  [KAP PDF] API hatası ({company}): {e}")
        return []


def download_pdf(disclosure_id: str) -> Optional[bytes]:
    """KAP'tan PDF'i indirir."""
    url = f"https://www.kap.org.tr/tr/api/BildirimPdf/{disclosure_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as e:
        print(f"  [KAP PDF] İndirme hatası ({disclosure_id}): {e}")
        return None


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """PDF'den metin çıkarır (pdfplumber)."""
    try:
        import pdfplumber

        text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text
    except ImportError:
        print("  [KAP PDF] pdfplumber kurulu değil, metin çıkarılamıyor")
        return ""
    except Exception as e:
        print(f"  [KAP PDF] Metin çıkarma hatası: {e}")
        return ""


def extract_findings(text: str) -> Dict[str, int]:
    """PDF metninden KAP dip not anahtar kelimelerini sayar."""
    patterns = {
        "teminat": r"(teminat|rehin|ipotek|garanti\s+verilen)",
        "dava": r"(dava|icra|hukuki\s+içtihat|mahkeme)",
        "ilgili_taraf": r"(ilgili\s+taraf|bağlı\s+ortaklık|kontrol|ana\s+ortağ)",
        "kambiyo": r"(kambiyo|döviz\s+pozisyon|hedge|forward|swap|opsiyon|kur\s+risk)",
        "taahhut": r"(taahhüt|sözleşme|yatırım\s+taahhüdü|sipariş\s+taahhüdü)",
        "musteri_yogunlugu": r"(müşteri\s+yoğun|tek\s+müşteri|ana\s+müşteri|ihale|kamu\s+ihalesi)",
        "finansal_kirala": r"(finansal\s+kiralama|IFRS\s+16)",
        "ozkaynak_ozel": r"(öz\s+kaynak|kâr\s+zarar|geri\s+alım|bedelsiz|sermaye\s+artırımı)",
        "musteri_yogunluk": r"(müşteri\s+yoğun|tek\s+müşteri|ana\s+müşteri)",
        "diger_faaliyet_gelir": r"(diğer\s+faaliyet\s+gelir|faaliştesi_dışı\s+gelir)",
        "tedarikci": r"(tedarikçi|tek\s+tedarikçi)",
        "ertelenmis_vergi": r"(ertelenmiş\s+vergi|vergi\s+ertelenmesi)",
    }
    findings: Dict[str, int] = {}
    for name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            findings[name] = len(matches)
    return findings


def fetch_kap_pdf_notes(symbol: str, max_docs: int = 5) -> List[Dict[str, Any]]:
    """
    Belirli bir hisse için KAP PDF dip notlarını çeker ve yapılandırılmış liste döner.
    """
    company = symbol.replace(".IS", "").replace("AS", "")
    disclosures = fetch_disclosure_ids(company)

    results: List[Dict[str, Any]] = []
    for disc in disclosures[:max_docs]:
        disc_id = disc.get("disclosureId") or disc.get("id")
        title = disc.get("disclosureTitle", "")
        date = disc.get("disclosureDate", "")

        if not disc_id:
            continue

        pdf_bytes = download_pdf(disc_id)
        if not pdf_bytes:
            continue

        text = extract_pdf_text(pdf_bytes)
        findings = extract_findings(text)

        results.append(
            {
                "disclosureId": disc_id,
                "title": title,
                "date": date,
                "findings": findings,
                "text_length": len(text),
            }
        )

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KAP PDF Parser")
    parser.add_argument("--symbol", default="ASELS.IS", help="Hisse senedi sembolü")
    parser.add_argument("--max", type=int, default=5, help="Maksimum belge sayısı")
    args = parser.parse_args()

    notes = fetch_kap_pdf_notes(args.symbol, args.max)
    print(json.dumps(notes, ensure_ascii=False, indent=2))
