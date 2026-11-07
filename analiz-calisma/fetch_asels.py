# -*- coding: utf-8 -*-
"""ASELS bilanco verisi cekici — isyatirimhisse ile."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from isyatirimhisse import fetch_financials
import inspect

print("IMZA:", inspect.signature(fetch_financials))
print("---")

try:
    df = fetch_financials(symbols="ASELS", start_year="2015", end_year="2026")
    df.to_csv("analiz-calisma/ASELS-veri/bilanco-ham.csv")
    print(df.to_string())
except Exception as e:
    print("HATA:", type(e).__name__, str(e)[:500])
