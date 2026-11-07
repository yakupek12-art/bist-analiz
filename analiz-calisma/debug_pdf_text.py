import pdfplumber
with pdfplumber.open("analiz-calisma/ASELS-veri/kap_test3.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            print(f"=== SAYFA {i+1} ===")
            print(text[:3000])
            print("...")