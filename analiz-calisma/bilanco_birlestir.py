# -*- coding: utf-8 -*-
"""bilanco-ham.csv (2023-2024) + bilanco-2025-2026.csv birlestirip anahtar kalemleri ozete dizer."""
import sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import pandas as pd

d = "analiz-calisma/ASELS-veri/"
df1 = pd.read_csv(d + "bilanco-ham.csv")
df2 = pd.read_csv(d + "bilanco-2025-2026.csv")
print("df2 kolonlar:", list(df2.columns)[:12])

key = "FINANCIAL_ITEM_CODE"
merged = pd.merge(df1, df2, on=key, how="outer", suffixes=("", "_y"))

name_col_y = "FINANCIAL_ITEM_NAME_TR_y" if "FINANCIAL_ITEM_NAME_TR_y" in merged.columns else None
kol = [c for c in merged.columns if "/" in c and c[0].isdigit()]
print("donem kolonlari:", kol)

kalip = (r"Sat|Gelir|Faaliyet|FAV|Net D|Ozak|Kısa V|Uzun V|Toplam Y|Nakit ve|"
         r"Stoklar|Ticari Alacak|Finansal Bor|Öz Sah|Es Sah|Cari")

out = []
for _, r in merged.iterrows():
    nm = r.get("FINANCIAL_ITEM_NAME_TR")
    if (nm is None or pd.isna(nm)) and name_col_y:
        nm = r.get(name_col_y)
    if (nm is None or pd.isna(nm)) and "FINANCIAL_ITEM_NAME_EN" in merged.columns:
        nm = r.get("FINANCIAL_ITEM_NAME_EN")
    nm = str(nm)
    if re.search(kalip, nm, re.IGNORECASE):
        degerler = []
        for k in kol:
            v = r[k]
            try:
                fv = float(v)
                degerler.append(f"{k}={round(fv/1e6,1)}mn")
            except (ValueError, TypeError):
                pass
        if degerler:
            out.append(f"{r[key]} | {nm}: " + ", ".join(degerler))

with open(d + "bilanco-ozet.txt", "w", encoding="utf-8") as f:
    f.write("ASELS/ASELSAN ANAHTAR BILANCO KALEMLERI (mn TL, kaynak: isyatirimhisse / isyatirim.com.tr)\n")
    f.write("\n".join(out))

print("toplam satir:", len(out))
print("\n".join(out[:8]))
