# -*- coding: utf-8 -*-
"""
Finansal Derinlik Modülü — Stdlib only, eksik kalemleri formülle doldurur.
3A = 3C + 3B (Satış = Brüt Kar + Maliyet)
3HG = 3J (Dönem Karı = Net Kar)
3HF ≈ 3IA + 3IB + 3IC (Vergi Gideri ≈ Ertelenmiş + Dönem + Ertelenmiş Vergi Geliri)
3HE = 3H (Vergi Öncesi Kar = Net Faaliyet Karı)
"""
import sys, io, json, os, math, csv
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

# ---------- Veri yükleme (tüm CSV birleştir) ----------
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

def calc_all(all_rows, period_cols):
    # Önce ham serileri çek
    raw_series = {}
    for code in set(list(all_rows.keys())):
        raw_series[code] = get_series(all_rows, code, period_cols)

    # --- Hesaplanmış seriler (eksikleri doldur) ---
    series = {}

    # 3A = 3C + 3B (Satış = Brüt Kar + Maliyet)
    series["satis_geliri"] = {}
    for p in period_cols:
        c = raw_series.get("3C", {}).get(p)
        b = raw_series.get("3B", {}).get(p)
        try:
            series["satis_geliri"][p] = (float(c) if c else 0) + (float(b) if b else 0)
        except (ValueError, TypeError):
            series["satis_geliri"][p] = None

    # 3HG = 3J (Dönem Karı = Net Kar) — 3J genellikle 3L/3Z ile aynı
    series["donem_kari"] = {}
    for p in period_cols:
        v = all_rows.get("3L", {}).get(p) or all_rows.get("3J", {}).get(p) or all_rows.get("3Z", {}).get(p)
        series["donem_kari"][p] = to_float(v) if v else None

    # 3HF ≈ 3IA + 3IB + 3IC (Vergi Gideri ≈ Ertelenmiş + Dönem + Ertelenmiş Vergi Geliri)
    series["vergi_gideri_geliri"] = {}
    for p in period_cols:
        ia = to_float(all_rows.get("3IA", {}).get(p))
        ib = to_float(all_rows.get("3IB", {}).get(p))
        ic = to_float(all_rows.get("3IC", {}).get(p))
        hf = all_rows.get("3HF", {}).get(p)
        if hf:
            series["vergi_gideri_geliri"][p] = to_float(hf)
        elif ia is not None or ib is not None or ic is not None:
            s = (ia or 0) + (ib or 0) + (ic or 0)
            series["vergi_gideri_geliri"][p] = s if s != 0 else None
        else:
            series["vergi_gideri_geliri"][p] = None

    # 3HE = 3H (Vergi Öncesi Kar = Net Faaliyet Karı)
    series["vergi_oncesi_kari"] = {}
    for p in period_cols:
        h = all_rows.get("3H", {}).get(p)
        series["vergi_oncesi_kari"][p] = to_float(h) if h else None

    # Diğer doğrudan kodlar
    direct_keys = {
        "3A": "satis_geliri",  # zaten hesaplandı
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
        "3HE": "vergi_oncesi_kari",  # zaten hesaplandı
        "3HF": "vergi_gideri_geliri",  # zaten hesaplandı
        "3HG": "donem_kari",  # zaten hesaplandı
        "3IA": "surelenmis_vergi_geliri",
        "3IB": "donem_vergi_geliri",
        "3IC": "ertelenmis_vergi_geliri",
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
        "3DD": "diger_faaliyet_gelirleri",
        "3DE": "diger_faaliyet_giderleri",
        "3DF": "faaliyet_kari",
        "3HACA": "finansman_gideri_oncesi_faaliyet_kari",
        "3HB": "finansman_giderleri",
        "3HC": "finansman_gelirleri",
        "3HD": "diger_giderler",
    }

    # Ham serileri yükle
    series = {}
    for code, name in direct_keys.items():
        if name not in series:
            series[name] = get_series_any(all_rows, code, period_cols)

    # Hesaplanmışları ekle/güncelle
    # 3A = 3C + 3B
    series["satis_geliri"] = {}
    for p in period_cols:
        c = to_float(all_rows.get("3C", {}).get(p))
        b = to_float(all_rows.get("3B", {}).get(p))
        if c is not None and b is not None:
            series["satis_geliri"][p] = c + b
        else:
            series["satis_geliri"][p] = None

    # 3HG = 3L (Dönem Karı = Ana Ortaklık Payları Net Karı)
    series["donem_kari"] = {}
    for p in period_cols:
        v = all_rows.get("3L", {}).get(p) or all_rows.get("3J", {}).get(p) or all_rows.get("3Z", {}).get(p)
        series["donem_kari"][p] = to_float(v) if v else None

    # 3HF ≈ 3IA + 3IB + 3IC
    series["vergi_gideri_geliri"] = {}
    for p in period_cols:
        hf = all_rows.get("3HF", {}).get(p)
        if hf:
            series["vergi_gideri_geliri"][p] = to_float(hf)
        else:
            ia = to_float(all_rows.get("3IA", {}).get(p))
            ib = to_float(all_rows.get("3IB", {}).get(p))
            ic = to_float(all_rows.get("3IC", {}).get(p))
            s = (ia or 0) + (ib or 0) + (ic or 0)
            series["vergi_gideri_geliri"][p] = s if s != 0 else None

    # 3HE = 3H
    series["vergi_oncesi_kari"] = {}
    for p in period_cols:
        h = all_rows.get("3H", {}).get(p)
        series["vergi_oncesi_kari"][p] = to_float(h) if h else None

    # --- Hesaplamalar ---
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

    def gf(name):
        return series.get(name, {})

    def gf_val(name, p):
        return series.get(name, {}).get(p)

    def to_f(v):
        try:
            return float(v) if v not in ("", None, "nan", "NaN", "NA") else None
        except (ValueError, TypeError):
            return None

    results = {}
    for p in period_cols:
        satis = to_float(series.get("satis_geliri", {}).get(p))
        satis_mal = to_float(all_rows.get("3B", {}).get(p))
        brut = to_float(all_rows.get("3C", {}).get(p))
        faaliyet_kari = to_float(all_rows.get("3DF", {}).get(p))
        diger_faaliyet_gelir = to_float(all_rows.get("3DD", {}).get(p))
        diger_faaliyet_gider = to_float(all_rows.get("3DE", {}).get(p))
        finansman_oncesi = to_float(all_rows.get("3HACA", {}).get(p))
        finansman_gider = to_float(all_rows.get("3HB", {}).get(p))
        finansman_gelir = to_float(all_rows.get("3HC", {}).get(p))
        vergi_oncesi = to_float(all_rows.get("3H", {}).get(p))
        vergi = to_float(all_rows.get("3IA", {}).get(p)) or to_float(all_rows.get("3IB", {}).get(p)) or to_float(all_rows.get("3IC", {}).get(p))
        net_kar = to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p))

        nakit = to_float(all_rows.get("1AA", {}).get(p))
        ticari_alacak_kisa = to_float(all_rows.get("1AC", {}).get(p))
        stoklar = to_float(all_rows.get("1AF", {}).get(p))
        toplam_donen = to_float(all_rows.get("1AJ", {}).get(p))
        finansal_borc_kisa = to_float(all_rows.get("2AA", {}).get(p))
        ertelenmis_gelir_kisa = to_float(all_rows.get("2AAGCA", {}).get(p))
        finansal_borc_uzun = to_float(all_rows.get("2BA", {}).get(p))
        ertelenmis_gelir_uzun = to_float(all_rows.get("2BAD", {}).get(p))
        toplam_donen_varlik = to_float(all_rows.get("1AJ", {}).get(p))
        brut_kar = to_float(all_rows.get("3C", {}).get(p))
        faaliyet_kari = to_float(all_rows.get("3DF", {}).get(p))
        finansman_oncesi = to_float(all_rows.get("3HACA", {}).get(p))
        finansman_gider = to_float(all_rows.get("3HB", {}).get(p))
        finansman_gelir = to_float(all_rows.get("3HC", {}).get(p))
        vergi_oncesi = to_float(all_rows.get("3H", {}).get(p))
        net_kar = to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p))

        out = {"period": p}

        # Marjlar
        out["brut_marj"] = pct(to_float(all_rows.get("3C", {}).get(p)), to_float(all_rows.get("3A", {}).get(p)) if "3A" in all_rows else None)
        # 3A hesaplanmış mı kontrol et
        satis = to_float(all_rows.get("3A", {}).get(p))
        if satis is None:
            c = to_float(all_rows.get("3C", {}).get(p))
            b = to_float(all_rows.get("3B", {}).get(p))
            if c is not None and b is not None:
                satis = c + b
        out["brut_marj"] = pct(to_float(all_rows.get("3C", {}).get(p)), satis)
        out["faaliyet_marj"] = pct(to_float(all_rows.get("3DF", {}).get(p)), satis)
        out["net_marj"] = pct(to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p)), satis)
        out["favok_proxy_marj"] = pct(to_float(all_rows.get("3HACA", {}).get(p)), satis)

        # Borç / Likidite
        nakit = to_float(all_rows.get("1AA", {}).get(p))
        finansal_borc_kisa = to_float(all_rows.get("2AA", {}).get(p))
        finansal_borc_uzun = to_float(all_rows.get("2BA", {}).get(p))
        top_borc = (to_float(all_rows.get("2AA", {}).get(p)) or 0) + (to_float(all_rows.get("2BA", {}).get(p)) or 0)
        nakit_val = to_float(all_rows.get("1AA", {}).get(p))
        net_borc = top_borc - (nakit_val or 0)
        out["toplam_finansal_borc"] = top_borc
        out["nakit"] = nakit_val
        out["net_borc"] = net_borc

        cari_oran = safe_div(to_float(all_rows.get("1AJ", {}).get(p)), (to_float(all_rows.get("2AA", {}).get(p)) or 0) + to_float(all_rows.get("2AAGCA", {}).get(p)))
        out["cari_oran_temsili"] = pct(cari_oran, 1) if cari_oran else None

        asit_test = safe_div((to_float(all_rows.get("1AA", {}).get(p)) or 0) + to_float(all_rows.get("1AC", {}).get(p)),
                             (to_float(all_rows.get("2AA", {}).get(p)) or 0) + to_float(all_rows.get("2AAGCA", {}).get(p)))
        out["asit_test_temsili"] = pct(asit_test, 1) if asit_test else None

        favok = to_float(all_rows.get("3HACA", {}).get(p))
        net_borc_val = (to_float(all_rows.get("2AA", {}).get(p)) or 0) + (to_float(all_rows.get("2BA", {}).get(p)) or 0) - (to_float(all_rows.get("1AA", {}).get(p)) or 0)
        out["net_borc_favok_proxy"] = pct(net_borc_val, to_float(all_rows.get("3HACA", {}).get(p)))

        # Marjlar
        out["brut_marj"] = pct(to_float(all_rows.get("3C", {}).get(p)), satis)
        out["faaliyet_marj"] = pct(to_float(all_rows.get("3DF", {}).get(p)), satis)
        out["net_marj"] = pct(to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p)), satis)
        out["favok_proxy_marj"] = pct(to_float(all_rows.get("3HACA", {}).get(p)), satis)

        # Vergi oranı
        vergi = to_float(all_rows.get("3IA", {}).get(p)) or to_float(all_rows.get("3IB", {}).get(p)) or to_float(all_rows.get("3IC", {}).get(p))
        vergi_oncesi = to_float(all_rows.get("3H", {}).get(p))
        vergi_orani = pct(vergi, vergi_oncesi)
        out["etkin_vergi_orani"] = vergi_orani

        # NOPAT
        faaliyet_kari_val = to_float(all_rows.get("3DF", {}).get(p))
        vergi_orani_val = safe_div(to_float(all_rows.get("3IA", {}).get(p)) or to_float(all_rows.get("3IB", {}).get(p)) or to_float(all_rows.get("3IC", {}).get(p)), to_float(all_rows.get("3H", {}).get(p)))
        if faaliyet_kari_val is not None and vergi_orani_val is not None:
            out["nopat"] = faaliyet_kari_val * (1 - vergi_orani_val)
        else:
            out["nopat"] = None

        # Normalize kâr
        net_kar = to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p))
        diger_faaliyet_gelir = to_float(all_rows.get("3DD", {}).get(p))
        diger_faaliyet_gider = to_float(all_rows.get("3DE", {}).get(p))
        tekrarlanmayan = (to_float(all_rows.get("3DD", {}).get(p)) or 0) - (to_float(all_rows.get("3DE", {}).get(p)) or 0)
        normalize_kar = (to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p)) or 0) - tekrarlanmayan
        out["normalize_kar"] = normalize_kar
        out["normalize_kar_marj"] = pct(normalize_kar, satis)

        # Net borç / FAVOK
        top_borc = (to_float(all_rows.get("2AA", {}).get(p)) or 0) + (to_float(all_rows.get("2BA", {}).get(p)) or 0)
        nakit_val = to_float(all_rows.get("1AA", {}).get(p))
        net_borc_val = top_borc - (nakit_val or 0)
        favok = to_float(all_rows.get("3HACA", {}).get(p))
        out["net_borc_favok_proxy"] = pct(net_borc_val, to_float(all_rows.get("3HACA", {}).get(p)))

        # Cari / Asit-test
        cari = safe_div(to_float(all_rows.get("1AJ", {}).get(p)), (to_float(all_rows.get("2AA", {}).get(p)) or 0) + to_float(all_rows.get("2AAGCA", {}).get(p)))
        out["cari_oran_temsili"] = pct(cari_oran, 1) if cari_oran else None
        asit_test = safe_div((to_float(all_rows.get("1AA", {}).get(p)) or 0) + to_float(all_rows.get("1AC", {}).get(p)),
                             (to_float(all_rows.get("2AA", {}).get(p)) or 0) + to_float(all_rows.get("2AAGCA", {}).get(p)))
        out["asit_test_temsili"] = pct(asit_test, 1) if asit_test else None

        # Net borç / FAVOK
        net_borc_val = (to_float(all_rows.get("2AA", {}).get(p)) or 0) + (to_float(all_rows.get("2BA", {}).get(p)) or 0) - (to_float(all_rows.get("1AA", {}).get(p)) or 0)
        favok = to_float(all_rows.get("3HACA", {}).get(p))
        out["net_borc_favok_proxy"] = pct(net_borc_val, favok) if favok else None

        # Vergi oranı
        vergi_orani = pct(to_float(all_rows.get("3IA", {}).get(p)) or to_float(all_rows.get("3IB", {}).get(p)) or to_float(all_rows.get("3IC", {}).get(p)), to_float(all_rows.get("3H", {}).get(p)))
        out["etkin_vergi_orani"] = vergi_orani

        # NOPAT
        faaliyet_kari_val = to_float(all_rows.get("3DF", {}).get(p))
        vergi_orani_val = safe_div(to_float(all_rows.get("3IA", {}).get(p)) or to_float(all_rows.get("3IB", {}).get(p)) or to_float(all_rows.get("3IC", {}).get(p)), to_float(all_rows.get("3H", {}).get(p)))
        if faaliyet_kari_val is not None and vergi_orani_val is not None:
            out["nopat"] = faaliyet_kari_val * (1 - vergi_orani_val)
        else:
            out["nopat"] = None

        # Normalize kâr
        net_kar = to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p))
        tekrarlanmayan = (to_float(all_rows.get("3DD", {}).get(p)) or 0) - (to_float(all_rows.get("3DE", {}).get(p)) or 0)
        normalize_kar = (to_float(all_rows.get("3L", {}).get(p)) or to_float(all_rows.get("3J", {}).get(p)) or to_float(all_rows.get("3Z", {}).get(p)) or 0) - tekrarlanmayan
        out["normalize_kar"] = normalize_kar
        out["normalize_kar_marj"] = pct(normalize_kar, satis)

        # NOPAT
        faaliyet_kari_val = to_float(all_rows.get("3DF", {}).get(p))
        vergi_orani_val = safe_div(to_float(all_rows.get("3IA", {}).get(p)) or to_float(all_rows.get("3IB", {}).get(p)) or to_float(all_rows.get("3IC", {}).get(p)), to_float(all_rows.get("3H", {}).get(p)))
        if faaliyet_kari_val is not None and vergi_orani_val is not None:
            out["nopat"] = faaliyet_kari_val * (1 - vergi_orani_val)
        else:
            out["nopat"] = None

        out["normalize_kar"] = normalize_kar
        out["normalize_kar_marj"] = pct(normalize_kar, satis)

        results[p] = out

    return results

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

# ---------- MAIN ----------
if __name__ == "__main__":
    csv_dir = "analiz-calisma/ASELS-veri"
    # CSV yükle
    all_rows = {}
    period_cols = set()
    for fname in sorted(os.listdir("analiz-calisma/ASELS-veri")):
        if not (fname.endswith(".csv") and "bilanco" in fname.lower()):
            continue
        fpath = os.path.join("analiz-calisma/ASELS-veri", fname)
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
                        v = v.strip() if v else ""
                        all_rows[code][k] = v
    period_cols = sorted(set().union(*[set(r.keys()) for r in all_rows.values() if isinstance(r, dict)]),
                         key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    print(f"Yüklendi: {len(period_cols)} dönem")
    results = {}
    for p in sorted(set().union(*[set(r.keys()) for r in all_rows.values() if isinstance(r, dict)]),
                         key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1]))):
        pass
    # calc_all içinde tekrar yükleme var, direkt çağır
    # Basit test: sadece 2024/12 için
    print("Test 2024/12:")
    print("3A (hesaplı):", to_float(all_rows.get("3C", {}).get("2024/12")) + to_float(all_rows.get("3B", {}).get("2024/12")))
    print("3DF:", all_rows.get("3DF", {}).get("2024/12"))
    print("3HACA:", all_rows.get("3HACA", {}).get("2024/12"))
    print("3L:", all_rows.get("3L", {}).get("2024/12"))
    print("3L (net kar):", all_rows.get("3L", {}).get("2024/12"))