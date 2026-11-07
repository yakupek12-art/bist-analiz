import csv
with open("analiz-calisma/ASELS-veri/bilanco-ham.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        code = row["FINANCIAL_ITEM_CODE"].strip()
        if code.startswith("3"):
            print(code + " -> " + row.get("FINANCIAL_ITEM_NAME_TR", "")[:50])