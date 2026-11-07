import csv, os

csv_dir = "analiz-calisma/ASELS-veri"
for fname in sorted(os.listdir(csv_dir)):
    if not (fname.endswith(".csv") and "bilanco" in fname.lower()): continue
    fpath = os.path.join(csv_dir, fname)
    codes = set()
    with open(fpath, "r", encoding="utf-8-sig") as f:
        first_line = f.readline().strip()
        cols = [c.strip().strip('"') for c in first_line.split(",")]
        cols = ["EMPTY" if c == "" else c for c in cols]
        reader = csv.DictReader(f, fieldnames=["EMPTY" if c == "" else c for c in cols])
        for row in reader:
            code = row.get("FINANCIAL_ITEM_CODE", "").strip()
            if code: codes.add(code)
    print(f"{fname}: {len(codes)} kod")
    # 3xx kodları
    inc = sorted([c for c in codes if c.startswith("3")])
    print("  3xx:", inc[:20])
    print()