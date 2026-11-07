# -*- coding: utf-8 -*-
"""
Finansal Derinlik Modülü — Stdlib only (pandas yok).
Bilanço + Gelir Tablosu + Nakit Akışı (varsa) birleşik analiz.
"""
import sys, io, json, os, math, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------- Yardımcı ----------
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
def load_all_csv(csv_dir):
    """Tüm CSV'leri birleştir: code -> {period: value}."""
    all_rows = {}
    period_cols = set()

    for fname in sorted(os.listdir(csv_dir)):
        if not (fname.endswith(".csv") and "bilanco" in fname.lower()):
            continue
        fpath = os.path.join(csv_dir, fname)
        with open(fpath, "r", encoding="utf-8-sig") as f:
            # İlk satırı manuel oku kolon isimlerini al
            first_line = f.readline().strip()
            cols = [c.strip().strip('"') for c in first_line.split(",")]
            # Boş kolon adını düzelt
            cols = ["EMPTY" if c == "" else c for c in cols]
            reader = csv.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get("FINANCIAL_ITEM_CODE", "").strip()
                if not code:
                    continue
                if code not in all_rows:
                    all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        all_rows[code][k] = v.strip() if v else ""

    period_cols = sorted([c for c in all_rows.get(list(all_rows.keys())[0], {}) if "/" in c and c[0].isdigit()],
                         key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    print(f"Yüklendi: {len(period_cols)} dönem, {len(all_rows)} kalem")
    return all_rows, sorted(list(set().union(*[set(r.keys()) for r in all_rows.values() if isinstance(r, dict)])))

def get_series(all_rows, code, period_cols):
    row = all_rows.get(code, {})
    series = {}
    for p in period_cols:
        v = all_rows.get(code, {}).get(p, "").strip()
        try:
            series[p] = float(v) if v else None
        except (ValueError, TypeError):
            series[p] = None
    return series

# ---------- TÜM KALEMLER (Bilanço + Gelir Tablosu) ----------
ALL_KEYS = {
    # --- BİLANÇO ---
    "1AA": "nakit",
    "1AC": "ticari_alacak_kisa",
    "1AF": "stoklar",
    "1B": "ticari_alacak_uzun",
    "1AH": "diger_donen_varlik",
    "1AJ": "toplam_donen_varlik",
    "1B": "ticari_alacak_uzun",
    "1BC": "finansal_yatirim",
    "1BF": "maddi_duran",
    "1BH": "maddi_olmayan_duran",
    "1BJ": "ertelenmis_vergi_varlik",
    "2AA": "finansal_borc_kisa",
    "2AAGCA": "ertelenmis_gelir_kisa",
    "2AAGH": "satis_amacli_duran_yuk",
    "2BA": "finansal_borc_uzun",
    "2BAD": "ertelenmis_gelir_uzun",
    # --- GELİR TABLOSU ---
    "3A": "satis_geliri",
    "3B": "satis_maliyeti",
    "3C": "brut_kar",
    "3D": "faaliyet_gelirleri",
    "3DD": "diger_faaliyet_gelirleri",
    "3DE": "diger_faaliyet_giderleri",
    "3DF": "faaliyet_kari",
    "3HACA": "finansman_gideri_oncesi_faaliyet_kari",
    "3HB": "finansman_giderleri",
    "3HC": "finansman_gelirleri",
    "3HD": "diger_giderler",
    "3HE": "vergi_oncesi_kari",
    "3HF": "vergi_gideri_geliri",
    "3HG": "donem_kari",
    # Ertelenmiş vergi ayrıntı
    "3IA": "surelenmis_vergi_geliri",
    "3IB": "donem_vergi_geliri",
    "3IC": "ertelenmis_vergi_geliri",
}

def load_all_rows(csv_dir):
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
                if not code:
                    continue
                if code not in all_rows:
                    all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        all_rows[code][k] = v.strip() if v else ""
    return all_rows

def get_series(all_rows, code, period_cols):
    row = all_rows.get(code, {})
    series = {}
    for p in period_cols:
        v = all_rows.get(code, {}).get(p, "").strip()
        try:
            series[p] = float(v) if v else None
        except (ValueError, TypeError):
            series[p] = None
    return series

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
                if not code:
                    continue
                if code not in all_rows:
                    all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        period_cols.add(k)
                        all_rows[code][k] = v.strip() if v else ""
    period_cols = sorted(period_cols, key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    return all_rows, period_cols

def get_series(all_rows, code, period_cols):
    series = {}
    for p in period_cols:
        v = all_rows.get(code, {}).get(p, "").strip()
        try:
            series[p] = float(v) if v else None
        except (ValueError, TypeError):
            series[p] = None
    return series

# ---------- Hesaplama ----------
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

ALL_KEYS = {
    "1AA": "nakit",
    "1AC": "ticari_alacak_kisa",
    "1AF": "stoklar",
    "1B": "ticari_alacak_uzun",
    "1AH": "diger_donen_varlik",
    "1AJ": "toplam_donen_varlik",
    "1B": "ticari_alacak_uzun",
    "1BC": "finansal_yatirim",
    "1BF": "maddi_duran",
    "1BH": "maddi_olmayan_duran",
    "1BJ": "ertelenmis_vergi_varlik",
    "2AA": "finansal_borc_kisa",
    "2AAGCA": "ertelenmis_gelir_kisa",
    "2AAGH": "satis_amacli_duran_yuk",
    "2BA": "finansal_borc_uzun",
    "2BAD": "ertelenmis_gelir_uzun",
    "3A": "satis_geliri",
    "3B": "satis_maliyeti",
    "3C": "brut_kar",
    "3D": "faaliyet_gelirleri",
    "3DD": "diger_faaliyet_gelirleri",
    "3DE": "diger_faaliyet_giderleri",
    "3DF": "faaliyet_kari",
    "3HACA": "finansman_gideri_oncesi_faaliyet_kari",
    "3HB": "finansman_giderleri",
    "3HC": "finansman_gelirleri",
    "3HD": "diger_giderler",
    "3HE": "vergi_oncesi_kari",
    "3HF": "vergi_gideri_geliri",
    "3HG": "donem_kari",
    "3IA": "surelenmis_vergi_geliri",
    "3IB": "donem_vergi_geliri",
    "3IC": "ertelenmis_vergi_geliri",
}

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
                if not code:
                    continue
                if code not in all_rows:
                    all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        period_cols.add(k)
                        all_rows[code][k] = v.strip() if v else ""
    period_cols = sorted(period_cols, key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    return all_rows, period_cols

def get_series(all_rows, code, period_cols):
    series = {}
    for p in period_cols:
        v = all_rows.get(code, {}).get(p, "").strip()
        try:
            series[p] = float(v) if v else None
        except (ValueError, TypeError):
            series[p] = None
    return series

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

ALL_KEYS = {
    "1AA": "nakit", "1AC": "ticari_alacak_kisa", "1AF": "stoklar",
    "1B": "ticari_alacak_uzun", "1AH": "diger_donen_varlik",
    "1AJ": "toplam_donen_varlik", "1B": "ticari_alacak_uzun",
    "1BC": "finansal_yatirim", "1BF": "maddi_duran",
    "1BH": "maddi_olmayan_duran", "1BJ": "ertelenmis_vergi_varlik",
    "2AA": "finansal_borc_kisa", "2AAGCA": "ertelenmis_gelir_kisa",
    "2AAGH": "satis_amacli_duran_yuk", "2BA": "finansal_borc_uzun",
    "2BAD": "ertelenmis_gelir_uzun",
    "3A": "satis_geliri", "3B": "satis_maliyeti", "3C": "brut_kar",
    "3D": "faaliyet_gelirleri", "3DD": "diger_faaliyet_gelirleri",
    "3DE": "diger_faaliyet_giderleri", "3DF": "faaliyet_kari",
    "3HACA": "finansman_gideri_oncesi_faaliyet_kari",
    "3HB": "finansman_giderleri", "3HC": "finansman_gelirleri",
    "3HD": "diger_giderler", "3HE": "vergi_oncesi_kari",
    "3HF": "vergi_gideri_geliri", "3HG": "donem_kari",
    "3IA": "surelenmis_vergi_geliri", "3IB": "donem_vergi_geliri",
    "3IC": "ertelenmis_vergi_geliri",
}

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
                if not code:
                    continue
                if code not in all_rows:
                    all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        period_cols.add(k)
                        all_rows[code][k] = v.strip() if v else ""
    period_cols = sorted(period_cols, key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    return all_rows, period_cols

def get_series(all_rows, code, period_cols):
    series = {}
    for p in period_cols:
        v = all_rows.get(code, {}).get(p, "").strip()
        try:
            series[p] = float(v) if v else None
        except (ValueError, TypeError):
            series[p] = None
    return series

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
    series = {}
    for code, name in ALL_KEYS.items():
        series[name] = get_series(all_rows, code, period_cols)

    results = {}
    for p in period_cols:
        def g(name): return series.get(name, {}).get(p)
        def gf(name): return to_float(series.get(name, {}).get(p))

        satis = gf("satis_geliri")
        satis_mal = gf("satis_maliyeti")
        brut = gf("brut_kar")
        faaliyet_kari = gf("faaliyet_kari")
        diger_faaliyet_gelir = gf("diger_faaliyet_gelirleri")
        diger_faaliyet_gider = gf("diger_faaliyet_giderleri")
        finansman_oncesi = gf("finansman_gideri_oncesi_faaliyet_kari")
        finansman_gider = gf("finansman_giderleri")
        finansman_gelir = gf("finansman_gelirleri")
        vergi_oncesi = gf("vergi_oncesi_kari")
        vergi = gf("vergi_gideri_geliri")
        net_kar = gf("donem_kari")
        ertelenmis_vergi = gf("ertelenmis_vergi_geliri")

        nakit = gf("nakit")
        ticari_alacak_kisa = gf("ticari_alacak_kisa")
        stoklar = gf("stoklar")
        toplam_donen = gf("toplam_donen_varlik")
        finansal_borc_kisa = gf("finansal_borc_kisa")
        ertelenmis_gelir_kisa = gf("ertelenmis_gelir_kisa")
        finansal_borc_uzun = gf("finansal_borc_uzun")
        ertelenmis_gelir_uzun = gf("ertelenmis_gelir_uzun")
        toplam_donen_varlik = gf("toplam_donen_varlik")

        out = {"period": p}

        # Marjlar
        out["brut_marj"] = pct(gf("brut_kar"), gf("satis_geliri"))
        out["faaliyet_marj"] = pct(gf("faaliyet_kari"), gf("satis_geliri"))
        out["net_marj"] = pct(gf("donem_kari"), gf("satis_geliri"))
        out["favok_proxy_marj"] = pct(gf("finansman_gideri_oncesi_faaliyet_kari"), gf("satis_geliri"))

        # Borç / Likidite
        top_borc = safe_div(gf("finansal_borc_kisa"), 1) + safe_div(gf("finansal_borc_uzun"), 1)
        nakit = gf("nakit")
        net_borc = safe_div(gf("finansal_borc_kisa"), 1) + safe_div(gf("finansal_borc_uzun"), 1)
        if nakit is not None:
            net_borc = (net_borc or 0) - nakit
        out["toplam_finansal_borc"] = safe_div(gf("finansal_borc_kisa"), 1) + safe_div(gf("finansal_borc_uzun"), 1)
        out["nakit"] = gf("nakit")
        out["net_borc"] = safe_div(gf("finansal_borc_kisa"), 1) + safe_div(gf("finansal_borc_uzun"), 1) - (gf("nakit") or 0)

        cari_oran = safe_div(gf("toplam_donen_varlik"), gf("finansal_borc_kisa") + gf("ertelenmis_gelir_kisa"))
        out["cari_oran_temsili"] = pct(cari_oran, 1) if cari_oran else None
        asit_test = safe_div((gf("nakit") or 0) + gf("ticari_alacak_kisa"),
                             (gf("finansal_borc_kisa") or 0) + gf("ertelenmis_gelir_kisa"))
        out["asit_test_temsili"] = pct(asit_test, 1) if asit_test else None
        favok = gf("finansman_gideri_oncesi_faaliyet_kari")
        net_borc_val = safe_div(gf("finansal_borc_kisa"), 1) + safe_div(gf("finansal_borc_uzun"), 1) - (gf("nakit") or 0)
        out["net_borc_favok_proxy"] = pct(net_borc_val, favok) if favok and net_borc_val is not None else None

        # Marjlar
        out["brut_marj"] = pct(gf("brut_kar"), gf("satis_geliri"))
        out["faaliyet_marj"] = pct(gf("faaliyet_kari"), gf("satis_geliri"))
        out["net_marj"] = pct(gf("donem_kari"), gf("satis_geliri"))
        out["favok_proxy_marj"] = pct(gf("finansman_gideri_oncesi_faaliyet_kari"), gf("satis_geliri"))

        # Vergi oranı & NOPAT
        vergi = gf("vergi_gideri_geliri")
        vergi_oncesi = gf("vergi_oncesi_kari")
        vergi_orani = safe_div(gf("vergi_gideri_geliri"), gf("vergi_oncesi_kari"))
        faaliyet_kari = gf("faaliyet_kari")
        nopat = None
        if faaliyet_kari is not None and vergi_orani is not None:
            nopat = faaliyet_kari * (1 - vergi_orani)
        out["nopat"] = nopat
        out["etkin_vergi_orani"] = pct(gf("vergi_gideri_geliri"), gf("vergi_oncesi_kari"))

        # Normalize kâr
        net_kar = gf("donem_kari")
        diger_faaliyet_gelir = gf("diger_faaliyet_gelirleri")
        diger_faaliyet_gider = gf("diger_faaliyet_giderleri")
        tekrarlanmayan = (gf("diger_faaliyet_gelirleri") or 0) - (gf("diger_faaliyet_giderleri") or 0)
        normalize_kar = (gf("donem_kari") or 0) - tekrarlanmayan
        out["normalize_kar"] = normalize_kar

        # Borç / FAVOK
        top_borc = (gf("finansal_borc_kisa") or 0) + (gf("finansal_borc_uzun") or 0)
        nakit = gf("nakit")
        net_borc = top_borc - (nakit or 0)
        favok = gf("finansman_gideri_oncesi_faaliyet_kari")
        out["toplam_finansal_borc"] = top_borc
        out["nakit"] = nakit
        out["net_borc"] = net_borc
        out["net_borc_favok_proxy"] = pct(net_borc, favok) if favok else None

        # Marjlar tekrar
        out["brut_marj"] = pct(gf("brut_kar"), gf("satis_geliri"))
        out["faaliyet_marj"] = pct(gf("faaliyet_kari"), gf("satis_geliri"))
        out["net_marj"] = pct(gf("donem_kari"), gf("satis_geliri"))
        out["favok_proxy_marj"] = pct(gf("finansman_gideri_oncesi_faaliyet_kari"), gf("satis_geliri"))

        # Cari / Asit-test (temsili)
        cari = safe_div(gf("toplam_donen_varlik"), (gf("finansal_borc_kisa") or 0) + gf("ertelenmis_gelir_kisa"))
        out["cari_oran_temsili"] = pct(cari, 1) if cari else None
        asit_test = safe_div((gf("nakit") or 0) + (gf("ticari_alacak_kisa") or 0),
                             (gf("finansal_borc_kisa") or 0) + gf("ertelenmis_gelir_kisa"))
        out["asit_test_temsili"] = pct(asit_test, 1) if asit_test else None

        # Net borç / FAVOK
        net_borc_val = (gf("finansal_borc_kisa") or 0) + (gf("finansal_borc_uzun") or 0) - (gf("nakit") or 0)
        favok = gf("finansman_gideri_oncesi_faaliyet_kari")
        out["net_borc_favok_proxy"] = pct(net_borc_val, favok) if favok else None

        # Vergi oranı
        vergi_orani = pct(gf("vergi_gideri_geliri"), gf("vergi_oncesi_kari"))
        out["etkin_vergi_orani"] = vergi_orani

        # NOPAT
        faaliyet_kari = gf("faaliyet_kari")
        vergi_orani_val = safe_div(gf("vergi_gideri_geliri"), gf("vergi_oncesi_kari"))
        if faaliyet_kari is not None and vergi_orani_val is not None:
            out["nopat"] = faaliyet_kari * (1 - vergi_orani_val)
        else:
            out["nopat"] = None

        # Normalize kâr
        net_kar = gf("donem_kari")
        tekrarlanmayan = (gf("diger_faaliyet_gelirleri") or 0) - (gf("diger_faaliyet_giderleri") or 0)
        out["normalize_kar"] = (gf("donem_kari") or 0) - tekrarlanmayan

        # Normalize kâr marjı
        out["normalize_kar_marj"] = pct(out["normalize_kar"], gf("satis_geliri"))

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
    all_rows, periods = load_all(csv_dir)
    print(f"Yüklendi: {len(periods)} dönem, {len(all_rows)} kalem")
    results = calc_all(all_rows, periods)
    print_results(results)

    # JSON kaydet
    clean = {}
    for p, m in results.items():
        clean[p] = {k: v for k, v in m.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}
    out_path = "analiz-calisma/ASELS-veri/finansal_derinlik.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nKaydedildi: {out_path}")