# -*- coding: utf-8 -*-
"""
KAP PDF Parser — Bildirim PDF'lerinden dip notları, taahhütler, teminatlar,
ilgili taraf işlemleri, kambiyo pozisyonu, müşteri yoğunluğu çıkarma.
"""
import sys, re, io, json, os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import pdfplumber
except ImportError:
    print("pdfplumber yok → pip install pdfplumber")
    sys.exit(1)

try:
    import fitz  # PyMuPDF fallback
except ImportError:
    fitz = None

# ---------- Regex kalıpları ----------
PATTERNS = {
    "teminat": re.compile(r"(teminat|rehin|ipotek|şirket lehine|bankaya?\s+verilen|garanti\s+verilen)", re.I),
    "dava": re.compile(r"(dava|icra|hukuki\s+içtihat|mahkeme|tahliye|itiraz|şikayet)", re.I),
    "ilgili_taraf": re.compile(r"(ilgili\s+taraf|anakart|bağlı\s+ortaklık|kontrol|bağlı\s+şirket|ana\s+ortağ|yonetim\s+kurulu\s+uyesi|aile|akraba)", re.I),
    "kambiyo": re.compile(r"(kambiyo| döviz\s+pozisyon|finansal\s+araç|türev\s+araç|hedge|forward|swap|opsiyon|kur\s+risk|döviz\s+risk)", re.I),
    "taahhut": re.compile(r"(taahhüt|sözleşme|gayri\s+menkul\s+alım|yatırım\s+taahhüdü|sipariş\s+taahhüdü|garanti\s+mektubu)", re.I),
    "musteri_yogunlugu": re.compile(r"(müşteri\s+yoğun|tek\s+müşteri|ana\s+müşteri|%?\s*\d+\s*müşteri|ihale|kamu\s+ihalesi|tek\s+tedarik)", re.I),
    "finansal_kirala": re.compile(r"(finansal\s+kiralama|operasyonel\s+kiralama|kiralama\s+yükümlülüğü|IFRS\s+16)", re.I),
    "ozkaynak_ozel": re.compile(r"(öz\s+kaynak|kâr\s+zarar|yatırım\s+fonu|finansal\s+varlık|geri\s+alım|bedelsiz|sermaye\s+artırımı|ikraz)", re.I),
    "baglanti_notu": re.compile(r"(dip\s+not|not\s+\d+|ek\s+\d+|belge\s+no|tablosu\s+altındaki)", re.I),
}

# ---------- Yardımcı fonksiyonlar ----------
def extract_text_pdfplumber(pdf_path):
    """pdfplumber ile metin çıkar (tablo da yakalar)."""
    text = ""
    tables_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    text += f"\n--- SAYFA {i+1} ---\n{t}"
                # Tablolar
                tbls = page.extract_tables()
                for ti, tbl in enumerate(tbls):
                    if tbl:
                        tables_data.append({"page": i+1, "table_index": ti, "data": tbl})
    except Exception as e:
        print(f"pdfplumber hata: {e}")
    return text, tables_data

def extract_text_pymupdf(pdf_path):
    """PyMuPDF fallback."""
    if not fitz:
        return "", []
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            text += f"\n--- SAYFA {i+1} ---\n{page.get_text()}"
        doc.close()
    except Exception as e:
        print(f"PyMuPDF hata: {e}")
    return text, []

def find_relevant_sections(text, patterns):
    """İlgili kalıpları içeren paragrafları bul."""
    results = {k: [] for k in patterns}
    # Paragraf böl (boş satır veya sayfa sonu)
    paragraphs = re.split(r'\n\s*\n|\n--- SAYFA \d+ ---\n', text)
    for para in paragraphs:
        if len(para.strip()) < 30:
            continue
        for name, pat in patterns.items():
            if pat.search(para):
                # Bağlam: 200 karakter öncesi/sonrası
                start = max(0, para.find(pat.search(para).group()) - 200)
                end = min(len(para), pat.search(para).end() + 500)
                snippet = para[start:end].strip()
                results[name].append(snippet)
    return results

def extract_tables_with_keywords(tables_data, keywords):
    """Tablolarda anahtar kelime ara."""
    hits = []
    for tbl in tables_data:
        for row in tbl["data"]:
            row_text = " ".join([str(c) for c in row if c])
            for kw in keywords:
                if re.search(kw, row_text, re.I):
                    hits.append({"page": tbl["page"], "row": row, "keyword": kw})
    return hits

def parse_kap_pdf(pdf_path):
    """Ana fonksiyon: PDF'ten dip not bilgilerini çıkar."""
    print(f"İşleniyor: {pdf_path}")
    text, tables = extract_text_pdfplumber(pdf_path)
    if not text.strip() and fitz:
        text, tables = extract_text_pymupdf(pdf_path)

    # Kalıp arama
    findings = find_relevant_sections(text, PATTERNS)

    # Tablo arama (teminat, kambiyo, ilgili taraf tabloları genelde tablo içinde)
    table_keywords = ["teminat", "rehin", "ipotek", "kambiyo", "döviz", "hedge", "ilgili taraf", "bağlı", "taahhüt", "dava"]
    table_hits = extract_tables_with_keywords(tables, table_keywords)

    # Özet
    summary = {
        "file": os.path.basename(pdf_path),
        "total_pages": len(re.findall(r'--- SAYFA \d+ ---', text)),
        "findings": {k: len(v) for k, v in findings.items()},
        "table_hits": len(table_hits),
        "details": findings,
        "table_details": table_hits[:20],  # ilk 20
    }
    return summary

# ---------- CLI ----------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KAP PDF Dip Not Çıkarıcı")
    parser.add_argument("pdf_path", help="PDF dosya yolu")
    parser.add_argument("-o", "--output", help="Çıktı JSON dosyası")
    args = parser.parse_args()

    result = parse_kap_pdf(args.pdf_path)
    out_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"Kaydedildi: {args.output}")
    else:
        print(out_json)