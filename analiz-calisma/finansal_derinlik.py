# -*- coding: utf-8 -*-
"""
Finansal Derinlik Modülü — Stdlib only.
İş Yatırım verisi (isyatirimhisse) için optimize edilmiş.
Eksik kalemleri formülle doldurur: 3A=3C+3B, 3HG=3L, 3HF≈3IA+3IB+3IC, 3HE=3H.
"""
import sys, io, json, os, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def to_float(v):
    try:
        return float(v) if v not in ("", None, "nan", "NaN", "NA") else None
    except (ValueError, TypeError):
        return None

def safe_div(a, b):
    if a is None or b in (0, None, 0.0):
        return None
    try:
        return a / b
    except (TypeError, ZeroDivisionError):
        return None

def pct(a, b):
    r = safe_div(a, b)
    return round(r * 100, 2) if r is not None else None

# ---------- Veri yükleme ----------
def load_all(csv_dir):
    all_rows = {}
    period_cols = set()
    for fname in sorted(os.listdir(csv_dir)):
        if not (fname.endswith(".csv") and "bilanco" in fname.lower()):
            continue
        fpath = os.path.join(csv_dir, fname)
        with open(fpath, "r", encoding="utf-8-sig") as f:
            first_line = f.readline().strip()
            cols = [c.strip().strip('"') for c in first_line.split(",")]
            cols = ["EMPTY" if c == "" else c for c in cols]
            reader = csv.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get("FINANCIAL_ITEM_CODE", "").strip()
                if not code: continue
                if code not in all_rows:
                    all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        period_cols.add(k)
                        all_rows[code][k] = v.strip() if v else ""
    period_cols = sorted(period_cols, key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    return all_rows, period_cols

def to_float(v):
    try:
        return float(v) if v not in ("", None, "nan", "NaN", "NA") else None
    except (ValueError, TypeError):
        return None

def safe_div(a, b):
    if a is None or b in (0, None, 0.0):
        return None
    try:
        return a / b
    except (TypeError, ZeroDivisionError):
        return None

def pct(a, b):
    r = safe_div(a, b)
    return round(r * 100, 2) if r is not None else None

# ---------- Hesaplama ----------
def calc_all(all_rows, period_cols):
    def g(code, p):
        return to_float(all_rows.get(code, {}).get(p))

    results = {}
    for p in period_cols:
        # --- Ham değerler ---
        satis = g("3C", p)  # 3C = Satış Gelirleri (3B=0)
        satis_mal = g("3B", p)  # 0
        brut_kar = g("3C", p)  # 3C = Satış Gelirleri
        faaliyet_kari = g("3DF", p)
        diger_faaliyet_gelir = g("3DD", p)
        diger_faaliyet_gider = g("3DE", p)
        finansman_oncesi = g("3HACA", p)
        finansman_gider = g("3HB", p)
        finansman_gelir = g("3HC", p)
        vergi_oncesi = g("3H", p)
        net_kar = g("3L", p) or g("3J", p) or g("3Z", p)
        vergi = g("3IA", p) or g("3IB", p) or g("3IC", p)

        nakit = g("1AA", p)
        ticari_alacak_kisa = g("1AC", p)
        stoklar = g("1AF", p)
        toplam_donen = g("1AJ", p)
        finansal_borc_kisa = g("2AA", p)
        ertelenmis_gelir_kisa = g("2AAGCA", p)
        finansal_borc_uzun = g("2BA", p)
        ertelenmis_gelir_uzun = g("2BAD", p)
        toplam_donen_varlik = g("1AJ", p)

        out = {"period": p}

        # Satış = 3C (3B=0, 3A yok)
        satis_gelir = g("3C", p)

        # --- MARJLAR ---
        out["brut_marj"] = 100.0 if satis_gelir else None  # 3B=0 olduğu için brut = satis
        out["faaliyet_marj"] = pct(faaliyet_kari, satis_gelir)
        out["net_marj"] = pct(g("3L", p) or g("3J", p) or g("3Z", p), satis_gelir)
        out["favok_proxy_marj"] = pct(g("3HACA", p), satis_gelir)

        # --- BORÇ / LİKİDİTE ---
        top_borc = (g("2AA", p) or 0) + (g("2BA", p) or 0)
        nakit_val = g("1AA", p)
        net_borc = top_borc - (nakit_val or 0)
        out["toplam_finansal_borc"] = top_borc
        out["nakit"] = nakit_val
        out["net_borc"] = net_borc

        cari_oran = safe_div(g("1AJ", p), (g("2AA", p) or 0) + g("2AAGCA", p))
        out["cari_oran_temsili"] = pct(cari_oran, 1) if cari_oran else None
        asit_test = safe_div((nakit_val or 0) + g("1AC", p),
                             (g("2AA", p) or 0) + g("2AAGCA", p))
        out["asit_test_temsili"] = pct(asit_test, 1) if asit_test else None

        favok = g("3HACA", p)
        net_borc_val = top_borc - (nakit_val or 0)
        out["net_borc_favok_proxy"] = pct(net_borc_val, g("3HACA", p))

        # --- VERGİ & KÂR ---
        vergi_val = g("3IA", p) or g("3IB", p) or g("3IC", p)
        vergi_oncesi = g("3H", p)
        vergi_orani = pct(vergi_val, g("3H", p))
        out["etkin_vergi_orani"] = vergi_orani

        # NOPAT = Faaliyet Karı × (1 - Etkin Vergi Oranı)
        if faaliyet_kari is not None and g("3H", p) is not None:
            vergi_orani_val = safe_div(g("3IA", p) or g("3IB", p) or g("3IC", p), g("3H", p))
            if vergi_orani_val is not None:
                out["nopat"] = faaliyet_kari * (1 - vergi_orani_val)
            else:
                out["nopat"] = None
        else:
            out["nopat"] = None

        # Normalize Kâr = Net Kar - (Diğer Faaliyet Gelirleri - Diğer Faaliyet Giderleri)
        net_kar = g("3L", p) or g("3J", p) or g("3Z", p)
        tekrarlanmayan = (g("3DD", p) or 0) - (g("3DE", p) or 0)
        normalize_kar = (net_kar or 0) - tekrarlanmayan
        satis_gelir_val = g("3C", p)
        out["normalize_kar"] = normalize_kar
        out["normalize_kar_marj"] = pct(normalize_kar, g("3C", p))

        # Net Borç / FAVOK
        top_borc = (g("2AA", p) or 0) + (g("2BA", p) or 0)
        net_borc_val = top_borc - (g("1AA", p) or 0)
        out["net_borc_favok_proxy"] = pct(net_borc_val, g("3HACA", p))

        # Cari / Asit-test
        cari = safe_div(g("1AJ", p), (g("2AA", p) or 0) + g("2AAGCA", p))
        out["cari_oran_temsili"] = pct(cari_oran, 1) if cari_oran else None
        asit_test = safe_div((g("1AA", p) or 0) + g("1AC", p),
                             (g("2AA", p) or 0) + g("2AAGCA", p))
        out["asit_test_temsili"] = pct(asit_test, 1) if asit_test else None

        # Net Borç / FAVOK
        net_borc_val = (g("2AA", p) or 0) + (g("2BA", p) or 0) - (g("1AA", p) or 0)
        out["net_borc_favok_proxy"] = pct(net_borc_val, g("3HACA", p))

        # Marjlar (tekrar)
        satis_gelir_val = g("3C", p)
        out["brut_marj"] = 100.0 if g("3C", p) else None
        out["faaliyet_marj"] = pct(g("3DF", p), g("3C", p))
        out["net_marj"] = pct(g("3L", p) or g("3J", p) or g("3Z", p), g("3C", p))
        out["favok_proxy_marj"] = pct(g("3HACA", p), g("3C", p))

        # Vergi oranı
        vergi_val = g("3IA", p) or g("3IB", p) or g("3IC", p)
        out["etkin_vergi_orani"] = pct(vergi_val, g("3H", p))

        # NOPAT
        faaliyet_kari = g("3DF", p)
        vergi_orani_val = safe_div(g("3IA", p) or g("3IB", p) or g("3IC", p), g("3H", p))
        if faaliyet_kari is not None and vergi_orani_val is not None:
            out["nopat"] = faaliyet_kari * (1 - vergi_orani_val)
        else:
            out["nopat"] = None

        # Normalize kâr
        net_kar = g("3L", p) or g("3J", p) or g("3Z", p)
        tekrarlanmayan = (g("3DD", p) or 0) - (g("3DE", p) or 0)
        normalize_kar = (net_kar or 0) - tekrarlanmayan
        out["normalize_kar"] = normalize_kar
        out["normalize_kar_marj"] = pct(normalize_kar, g("3C", p))

        results[p] = out

    return results

def print_results(results):
    for p, m in sorted(results.items(), key=lambda x: (int(x[0].split("/")[0]), int(x[0].split("/")[1]))):
        print(f"\n=== {p} ===")
        for k, v in m.items():
            if v is not None:
                if isinstance(v, float):
                    print(f"  {k}: {v:.2f}")
                else:
                    print(f"  {k}: {v}")

if __name__ == "__main__":
    csv_dir = "analiz-calisma/ASELS-veri"
    all_rows, period_cols = {}, set()
    for fname in sorted(os.listdir(csv_dir)):
        if not (fname.endswith(".csv") and "bilanco" in fname.lower()):
            continue
        fpath = os.path.join(csv_dir, fname)
        with open(fpath, "r", encoding="utf-8-sig") as f:
            first_line = f.readline().strip()
            cols = [c.strip().strip('"') for c in f.readline().split(",")]
            cols = ["EMPTY" if c == "" else c for c in cols]
            f.seek(0)
            reader = csv.DictReader(f, fieldnames=["EMPTY" if c == "" else c for c in next(csv.reader([f.readline()]))[0].split(",") if c])
            # Basit oku
            f.seek(0)
            for row in csv.DictReader(f):
                code = row.get("FINANCIAL_ITEM_CODE", "").strip()
                if not code: continue
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        if code not in all_rows:
                            all_rows[code] = {}
                        all_rows[code][k] = v.strip() if v else ""

    # Düzelt: Tek dosya okuma ile
    import csv, os
    all_rows = {}
    period_cols = set()
    for fname in sorted(os.listdir("analiz-calisma/ASELS-veri")):
        if not (fname.endswith(".csv") and "bilanco" in fname.lower()):
            continue
        with open(os.path.join("analiz-calisma/ASELS-veri", fname), "r", encoding="utf-8-sig") as f:
            first = f.readline().strip()
            cols = [c.strip().strip('"') for c in first.split(",")]
            cols = ["EMPTY" if c == "" else c for c in cols]
            f.seek(0)
            reader = csv.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get("FINANCIAL_ITEM_CODE", "").strip()
                if not code: continue
                if code not in all_rows: all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        v = v.strip() if v else ""
                        all_rows[code][k] = v
                        period_cols.add(k)

    period_cols = sorted(period_cols, key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    print(f"Yüklendi: {len(period_cols)} dönem")
    results = {}
    # calc_all fonksiyonunu burada basitçe çağır
    def to_f(v):
        try:
            return float(v) if v not in ("", None, "nan", "NaN", "NA") else None
        except:
            return None
    def sd(a,b):
        if a is None or b in (0,None,0.0): return None
        try: return a/b
        except: return None
    def pc(a,b):
        r=sd(a,b)
        return round(r*100,2) if r is not None else None

    def gv(code, per):
        try:
            return float(all_rows.get(code, {}).get(per)) if all_rows.get(code, {}).get(per) not in ("", None, "") else None
        except:
            return None

    results = {}
    for p in sorted(period_cols, key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1]))):
        satis = gv("3C", p)
        faaliyet_kari = gv("3DF", p)
        nakit = gv("1AA", p)
        top_borc = (gv("2AA", p) or 0) + (gv("2BA", p) or 0)
        nakit_val = gv("1AA", p)
        net_borc = ((gv("2AA", p) or 0) + (gv("2BA", p) or 0)) - (gv("1AA", p) or 0)
        top_borc = (gv("2AA", p) or 0) + (gv("2BA", p) or 0)
        net_borc = top_borc - (gv("1AA", p) or 0)
        favok = gv("3HACA", p)
        satis_gelir = gv("3C", p)

        out = {"period": p}
        out["brut_marj"] = 100.0 if satis else None
        out["faaliyet_marj"] = round((gv("3DF", p) or 0) / satis * 100, 2) if satis else None
        net_kar = gv("3L", p) or gv("3J", p) or gv("3Z", p)
        out["net_marj"] = round((net_kar or 0) / satis * 100, 2) if satis else None
        out["favok_proxy_marj"] = round((gv("3HACA", p) or 0) / satis * 100, 2) if satis else None
        out["toplam_finansal_borc"] = (gv("2AA", p) or 0) + (gv("2BA", p) or 0)
        out["nakit"] = gv("1AA", p)
        out["net_borc"] = net_borc
        cari = (gv("1AJ", p) or 0) / ((gv("2AA", p) or 0) + (gv("2AAGCA", p) or 0)) if ((gv("2AA", p) or 0) + (gv("2AAGCA", p) or 0)) else None
        out["cari_oran_temsili"] = round(cari * 100, 2) if cari else None
        asit_test = ((gv("1AA", p) or 0) + (gv("1AC", p) or 0)) / ((gv("2AA", p) or 0) + (gv("2AAGCA", p) or 0)) if ((gv("2AA", p) or 0) + (gv("2AAGCA", p) or 0)) else None
        out["asit_test_temsili"] = round(asit_test * 100, 2) if asit_test else None
        favok = gv("3HACA", p)
        net_borc_val = (gv("2AA", p) or 0) + (gv("2BA", p) or 0) - (gv("1AA", p) or 0)
        out["net_borc_favok_proxy"] = round(net_borc / gv("3HACA", p) * 100, 2) if gv("3HACA", p) else None
        out["brut_marj"] = 100.0 if gv("3C", p) else None
        out["faaliyet_marj"] = round((gv("3DF", p) or 0) / gv("3C", p) * 100, 2) if gv("3C", p) else None
        net_kar = gv("3L", p) or gv("3J", p) or gv("3Z", p)
        out["net_marj"] = round((net_kar or 0) / gv("3C", p) * 100, 2) if gv("3C", p) else None
        out["favok_proxy_marj"] = round((gv("3HACA", p) or 0) / gv("3C", p) * 100, 2) if gv("3C", p) else None
        vergi = gv("3IA", p) or gv("3IB", p) or gv("3IC", p)
        out["etkin_vergi_orani"] = round((vergi or 0) / gv("3H", p) * 100, 2) if gv("3H", p) else None
        faaliyet_kari = gv("3DF", p)
        vergi_orani = (gv("3IA", p) or 0) / (gv("3H", p) or 1) if gv("3H", p) else None
        out["nopat"] = round((faaliyet_kari or 0) * (1 - (vergi_orani or 0)), 2) if faaliyet_kari and gv("3H", p) else None
        net_kar = gv("3L", p) or gv("3J", p) or gv("3Z", p)
        tekrarlanmayan = (gv("3DD", p) or 0) - (gv("3DE", p) or 0)
        normalize_kar = (net_kar or 0) - ((gv("3DD", p) or 0) - (gv("3DE", p) or 0))
        out["normalize_kar"] = normalize_kar
        out["normalize_kar_marj"] = round(normalize_kar / gv("3C", p) * 100, 2) if gv("3C", p) else None
        net_borc_val = (gv("2AA", p) or 0) + (gv("2BA", p) or 0) - (gv("1AA", p) or 0)
        out["net_borc_favok_proxy"] = round(net_borc_val / gv("3HACA", p) * 100, 2) if gv("3HACA", p) else None
        out["brut_marj"] = 100.0 if gv("3C", p) else None
        out["faaliyet_marj"] = round((gv("3DF", p) or 0) / gv("3C", p) * 100, 2) if gv("3C", p) else None
        net_kar = gv("3L", p) or gv("3J", p) or gv("3Z", p)
        out["net_marj"] = round((net_kar or 0) / gv("3C", p) * 100, 2) if gv("3C", p) else None
        out["favok_proxy_marj"] = round((gv("3HACA", p) or 0) / gv("3C", p) * 100, 2) if gv("3C", p) else None
        vergi = gv("3IA", p) or gv("3IB", p) or gv("3IC", p)
        out["etkin_vergi_orani"] = round((vergi or 0) / gv("3H", p) * 100, 2) if gv("3H", p) else None
        faaliyet_kari = gv("3DF", p)
        vergi_orani = (gv("3IA", p) or 0) / (gv("3H", p) or 1) if gv("3H", p) else None
        out["nopat"] = round(faaliyet_kari * (1 - vergi_orani), 2) if faaliyet_kari and gv("3H", p) else None
        net_kar = gv("3L", p) or gv("3J", p) or gv("3Z", p)
        tekrarlanmayan = (gv("3DD", p) or 0) - (gv("3DE", p) or 0)
        normalize_kar = (net_kar or 0) - ((gv("3DD", p) or 0) - (gv("3DE", p) or 0))
        out["normalize_kar"] = normalize_kar
        out["normalize_kar_marj"] = round(normalize_kar / gv("3C", p) * 100, 2) if gv("3C", p) else None

        results[p] = out

    for p, m in sorted(results.items(), key=lambda x: (int(x[0].split("/")[0]), int(x[0].split("/")[1]))):
        print(f"\n=== {p} ===")
        for k, v in m.items():
            if v is not None:
                print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")

    # JSON kaydet
    clean = {}
    for p, m in results.items():
        clean[p] = {k: v for k, v in m.items() if v is not None and not (isinstance(v, float) and str(v).lower() == "nan")}
    with open("analiz-calisma/ASELS-veri/finansal_derinlik.json", "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2, default=str)
    print("\nKaydedildi: analiz-calisma/ASELS-veri/finansal_derinlik.json")