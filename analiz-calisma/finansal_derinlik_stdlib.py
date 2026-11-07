# -*- coding: utf-8 -*-
"""
Finansal Derinlik Modülü — Stdlib only (pandas yok, csv/json kullanır).
Nakit akışı, DuPont, ROIC, Owner Earnings, Capex/Depr, Normalize kâr.
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
def load_merged_csv(csv_dir):
    """Tüm bilanco CSV'lerini birleştir, dönem kolonlarını sırala."""
    all_rows = {}  # code -> {col: value}
    period_cols = set()

    for fname in sorted(os.listdir(csv_dir)):
        if not (fname.endswith(".csv") and "bilanco" in fname.lower()):
            continue
        fpath = os.path.join(csv_dir, fname)
        with open(fpath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
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

    # Dönem kolonlarını sırala (2023/3, 2023/6, ...)
    period_cols = sorted(list(period_cols), key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    print(f"Yüklendi: {len(period_cols)} dönem, {len(all_rows)} kalem")
    return all_rows, period_cols

def get_series(all_rows, code, period_cols):
    """Belirli kalem için dönem serisi."""
    row = all_rows.get(code, {})
    series = {}
    for p in period_cols:
        v = row.get(p, "").strip()
        try:
            series[p] = float(v) if v else None
        except (ValueError, TypeError):
            series[p] = None
    return series

# ---------- Anahtar kalemler ----------
KEY_MAP = {
    # Bilanço
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
    # Gelir tablosu
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
}

# ---------- Hesaplama ----------
def calc_all(all_rows, period_cols):
    # Seri yükle
    series = {}
    for code, name in KEY_MAP.items():
        series[name] = get_series(all_rows, code, period_cols)

    results = {}
    for p in period_cols:
        # Ham verileri çek
        def g(name): return series.get(name, {}).get(p)

        satis = to_float(g("satis_geliri"))
        satis_mal = to_float(g("satis_maliyeti"))
        brut = to_float(g("brut_kar"))
        faaliyet_kari = to_float(g("faaliyet_kari"))
        diger_faaliyet_gelir = to_float(g("diger_faaliyet_gelirleri"))
        diger_faaliyet_gider = to_float(g("diger_faaliyet_giderleri"))
        finansman_oncesi = to_float(g("finansman_gideri_oncesi_faaliyet_kari"))
        finansman_gider = to_float(g("finansman_giderleri"))
        finansman_gelir = to_float(g("finansman_gelirleri"))
        vergi_oncesi = to_float(g("vergi_oncesi_kari"))
        vergi = to_float(g("vergi_gideri_geliri"))
        net_kar = to_float(g("donem_kari"))

        nakit = to_float(g("nakit"))
        ticari_alacak_kisa = to_float(g("ticari_alacak_kisa"))
        stoklar = to_float(g("stoklar"))
        toplam_donen = to_float(g("toplam_donen_varlik"))
        finansal_borc_kisa = to_float(g("finansal_borc_kisa"))
        ertelenmis_gelir_kisa = to_float(g("ertelenmis_gelir_kisa"))
        finansal_borc_uzun = to_float(g("finansal_borc_uzun"))
        ertelenmis_gelir_uzun = to_float(g("ertelenmis_gelir_uzun"))

        out = {"period": p}

        # --- 1. MARJLAR ---
        out["brut_marj"] = pct(brut, satis)
        out["faaliyet_marj"] = pct(faaliyet_kari, satis)
        out["net_marj"] = pct(net_kar, satis)
        out["favok_proxy_marj"] = pct(finansman_oncesi, satis) if finansman_oncesi else None

        # --- 2. BORÇ / LİKİDİTE ---
        top_borc = safe_div(finansal_borc_kisa, 1) + safe_div(finansal_borc_uzun, 1)
        net_borc = safe_div(top_borc, 1) - safe_div(nakit, 1) if nakit else None
        out["toplam_finansal_borc"] = top_borc
        out["nakit"] = nakit
        out["net_borc"] = net_borc

        cari_oran = safe_div(toplam_donen, safe_div(finansal_borc_kisa, 1) + safe_div(ertelenmis_gelir_kisa, 1))
        out["cari_oran_temsili"] = cari_oran
        asit_test = safe_div(safe_div(nakit, 1) + safe_div(ticari_alacak_kisa, 1),
                             safe_div(finansal_borc_kisa, 1) + safe_div(ertelenmis_gelir_kisa, 1))
        out["asit_test_temsili"] = asit_test
        out["net_borc_favok_proxy"] = safe_div(net_borc, finansman_oncesi) if finansman_oncesi else None

        # --- 3. VERGİ ORANI & NOPAT ---
        vergi_orani = safe_div(series.get("vergi_gideri_geliri", {}).get(p),
                               series.get("vergi_oncesi_kari", {}).get(p))
        vergi_orani_val = to_float(vergi_orani)
        faaliyet_kari_val = to_float(series.get("faaliyet_kari", {}).get(p))
        vergi_orani_pct = pct(series.get("vergi_gideri_geliri", {}).get(p),
                              series.get("vergi_oncesi_kari", {}).get(p))
        nopat = None
        if faaliyet_kari is not None and vergi_orani is not None:
            nopat = faaliyet_kari * (1 - vergi_orani)
        out["nopat"] = nopat
        out["etkin_vergi_orani"] = pct(to_float(series.get("vergi_gideri_geliri", {}).get(p)),
                                       to_float(series.get("vergi_oncesi_kari", {}).get(p)))

        # --- 4. NORMALİZE KÂR ---
        net_kar = to_float(series.get("donem_kari", {}).get(p))
        diger_faaliyet_gelir = to_float(series.get("diger_faaliyet_gelirleri", {}).get(p))
        diger_faaliyet_gider = to_float(series.get("diger_faaliyet_giderleri", {}).get(p))
        tekrarlanmayan = 0
        if diger_faaliyet_gelir: tekrarlanmayan += diger_faaliyet_gelir
        if diger_faaliyet_gider: tekrarlanmayan -= diger_faaliyet_gider
        normalize_kar = safe_div(series.get("donem_kari", {}).get(p), 1)
        if normalize_kar is not None:
            normalize_kar -= tekrarlanmayan
        out["normalize_kar"] = normalize_kar

        # --- 5. BORÇ / FAVOK PROXY ---
        top_borc_val = safe_div(top_borc, 1)
        nakit_val = to_float(series.get("nakit", {}).get(p))
        net_borc_val = None
        if top_borc_val is not None and nakit_val is not None:
            net_borc_val = top_borc_val - nakit_val
        out["net_borc"] = net_borc_val
        out["net_borc_favok_proxy"] = safe_div(net_borc_val, to_float(series.get("finansman_gideri_oncesi_faaliyet_kari", {}).get(p)))

        # --- 6. ÇALIŞMA SERMAYESİ TRENDİ (sadece değerler, değişim hesaplanmaz) ---
        # Sonraki versiyonda ΔWC eklenecek

        results[p] = out

    return results

# ---------- Yardımcı (tekrar tanım) ----------
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

# ---------- Çıktı ----------
def print_results(results):
    for p, m in sorted(results.items(), key=lambda x: (int(x[0].split("/")[0]), int(x[0].split("/")[1]))):
        print(f"\n=== {p} ===")
        for k, v in m.items():
            if v is not None:
                if isinstance(v, float):
                    print(f"  {k}: {v:.2f}")
                else:
                    print(f"  {k}: {v}")

# ---------- MAIN ----------
if __name__ == "__main__":
    csv_dir = "analiz-calisma/ASELS-veri"
    all_rows, periods = load_merged_csv(csv_dir)
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