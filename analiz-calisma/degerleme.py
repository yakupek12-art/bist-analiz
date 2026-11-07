# -*- coding: utf-8 -*-
"""
Değerleme Modülü — DCF (3 senaryo), Çarpan Percentile'leri,
Ters DCF (Piyasa neyi fiyatlıyor?), Güvenlik Marjı.
Stdlib only.
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
                if code not in all_rows: all_rows[code] = {}
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

# ---------- DCF Hesaplama ----------
def dcf_valuation(fcf, wacc, g_terminal, years=5, shares=None):
    """
    FCF (Free Cash Flow) bazlı DCF.
    fcf: son dönem FCF (TL)
    wacc: ağırlıklı ortalama sermaye maliyeti (örn. 0.15)
    g_terminal: sonsuz büyüme oranı (örn. 0.03)
    years: tahmin yılı (varsayılan 5)
    shares: hisse adedi (opsiyonel, hisse başına değer için)
    """
    if fcf is None or wacc is None or g_terminal is None:
        return None
    if wacc <= g_terminal:
        return {"error": "WACC <= g_terminal, DCF tanımsız"}

    # Basit: FCF sabit büyür (veya son FCF'tan başlar)
    pv_fcf = 0
    for i in range(1, years + 1):
        fcf_t = fcf * (1.05 ** i)  # %5 yıllık FCF büyüme varsayımı
        pv_fcf += fcf_t / ((1 + wacc) ** i)

    # Terminal value (Gordon Growth)
    fcf_terminal = fcf * (1.05 ** years) * (1 + g_terminal)
    tv = fcf_terminal / (wacc - g_terminal)
    pv_tv = tv / ((1 + wacc) ** years)

    ev = pv_fcf + pv_tv  # Enterprise Value
    result = {"enterprise_value": ev, "pv_fcf": pv_fcf, "pv_terminal": pv_tv}
    if shares and shares > 0:
        net_debt = 0  # Net borç ayrı verilecek
        equity = ev - net_debt
        result["equity_value"] = equity
        result["fair_price_per_share"] = safe_div(equity, shares)
    return result

# ---------- Çarpan Hesaplama ----------
def calculate_multiples(all_rows, period_cols, price_per_share=None, shares=None):
    """Son dönem için çarpanları hesapla."""
    p = period_cols[-1]  # En son dönem
    g = lambda code: to_float(all_rows.get(code, {}).get(p))

    satis = g("3C")
    net_kar = g("3L") or g("3J", p) or g("3Z", p)
    faaliyet_kari = g("3DF")
    favok = g("3HACA")
    net_borc = (g("2AA") or 0) + (g("2BA") or 0) - (g("1AA") or 0)
    ozkaynak = None  # 3L/3J/3Z net kar ama özkaynak ayrı kodla gelmez

    out = {"period": p}
    if satis:
        out["ps"] = safe_div(price_per_share * (shares or 1), satis) if price_per_share and shares else None
        out["ev_sales"] = safe_div((price_per_share * (shares or 1)) + (g("2AA") or 0) + (g("2BA") or 0) - (g("1AA") or 0), satis) if price_per_share else None
    if g("3DF"):
        out["ev_favok"] = None  # EV lazım
    if g("3L") or g("3J") or g("3Z"):
        out["p_e"] = safe_div(price_per_share, safe_div(g("3L") or g("3J") or g("3Z"), shares)) if price_per_share and shares else None
    out["favok_margin"] = pct(g("3HACA"), g("3C"))
    out["net_margin"] = pct(g("3L") or g("3J") or g("3Z"), g("3C"))
    out["net_borc_favok"] = safe_div((g("2AA") or 0) + (g("2BA") or 0) - (g("1AA") or 0), g("3HACA"))
    return out

# ---------- Ters DCF (Piyasa neyi fiyatlıyor?) ----------
def reverse_dcf(market_cap, net_debt, fcf, wacc, years=10):
    """
    Piyasa değerinden (market_cap + net_debt = EV), geriye kalan büyüme oranını (g) çöz.
    EV = Sum(FCF_t / (1+wacc)^t) + TV/(1+wacc)^n
    TV = FCF_n * (1+g) / (wacc - g)
    Bu denklemi g için çöz (iteratif).
    """
    ev = market_cap + net_debt
    if not ev or not fcf or not wacc:
        return None

    # Basit iteratif çözüm: g'yi 0'dan 0.1'e kadar ara
    best_g = None
    best_diff = float('inf')
    for g_test in [i * 0.001 for i in range(0, 101)]:  # 0% - 10%
        if g_test >= 0.15:  # WACC üstü olmaz
            continue
        # 10 yıl FCF projeksiyonu
        pv = 0
        for i in range(1, 11):
            fcf_t = fcf * (1.03 ** i)  # %3 FCF büyüme varsayımı
            pv += fcf * (1.03 ** i) / (1 + 0.12) ** i
        # Terminal
        if 0.12 > g_test:
            fcf_10 = fcf * (1.03 ** 10)
            tv = fcf_10 * (1 + g_test) / (0.12 - g_test)
            pv_tv = tv / (1.12 ** 10)
            total_ev = pv + pv_tv
            diff = abs(total_ev - ev)
            if diff < best_diff:
                best_diff = diff
                best_g = g_test
    return {"implied_growth": best_g, "ev": ev, "diff": best_diff} if best_g is not None else None

# ---------- Çarpan Percentile (Tarihsel) ----------
def percentile_rank(values, current):
    """Liste içindeki current değerinin percentile sırası (0-100)."""
    if not values or current is None:
        return None
    sorted_vals = sorted([v for v in values if v is not None])
    if not sorted_vals:
        return None
    count = sum(1 for v in sorted_vals if v <= current)
    return round((count / len(sorted_vals)) * 100, 1)

# ---------- Güvenlik Marjı ----------
def safety_margin(fair_value, current_price):
    """Güvenlik marjı = (Fair Value - Current Price) / Fair Value * 100"""
    return pct(fair_value - current_price, fair_value)

# ---------- Ana Hesaplama ----------
def calculate_valuation(all_rows, period_cols, price_per_share=None, shares=None):
    p = period_cols[-1]  # En son dönem
    g = lambda code: to_float(all_rows.get(code, {}).get(p))

    # Temel veriler
    fcf = None  # FCF verisi yok (nakit akışı tablosu yok)
    net_kar = g("3L") or g("3J") or g("3Z")
    satis = g("3C")
    favok = g("3HACA")
    net_kar_val = g("3L") or g("3J") or g("3Z")

    results = {"period": p}

    # --- Çarpanlar ---
    if price_per_share and shares:
        results["p_e"] = safe_div(price_per_share, safe_div(g("3L") or g("3J") or g("3Z"), shares))
        results["p_b"] = None  # Özkaynak verisi yok
        results["p_s"] = safe_div(price_per_share, safe_div(satis, shares))
        ev = (price_per_share * shares) + (g("2AA") or 0) + (g("2BA") or 0) - (g("1AA") or 0)
        results["ev_favok"] = safe_div(ev, g("3HACA"))
        results["ev_sales"] = safe_div(ev, g("3C"))
        results["ev_ebitda"] = None  # EBITDA yok
    else:
        results["p_e"] = results["p_b"] = results["p_s"] = results["ev_favok"] = results["ev_sales"] = None

    # Marjlar
    results["favok_margin"] = pct(g("3HACA"), g("3C"))
    results["net_margin"] = pct(g("3L") or g("3J") or g("3Z"), g("3C"))
    results["net_borc_favok"] = safe_div((g("2AA") or 0) + (g("2BA") or 0) - (g("1AA") or 0), g("3HACA"))

    # Fair value (basit: P/E * Net Kar * Pay = Fair Market Cap)
    # DCF için FCF lazım, FCF yok -> basit P/E bazlı
    if price_per_share and shares and net_kar:
        pe_sektor = 12  # Sektör ort. P/E (varsayım)
        fair_mc = net_kar * pe_sektor
        fair_price = safe_div(fair_mc, shares)
        results["fair_price_pe"] = fair_price
        results["safety_margin_pe"] = pct(fair_price - (price_per_share or 0), fair_price)

    # DCF (FCF yoksa basit: NOPAT - Capex ≈ FCF)
    # NOPAT = Faaliyet Karı * (1 - t)
    faaliyet_kari = to_float(all_rows.get("3DF", {}).get(period_cols[-1]))
    vergi_orani = safe_div(to_float(all_rows.get("3IA", {}).get(period_cols[-1])) or 0, g("3H"))
    nopat = None
    if faaliyet_kari:
        vergi_orani_val = safe_div(g("3IA") or g("3IB") or g("3IC"), g("3H"))
        if faaliyet_kari and vergi_orani:
            nopat = faaliyet_kari * (1 - vergi_orani)
    results["nopat"] = nopat

    # Basit DCF (NOPAT - Capex ≈ FCF, Capex ≈ Amortisman, veri yok)
    # Sadece formül göster
    results["dcf_note"] = "FCF verisi (nakit akışı tablosu) mevcut değil. Capex/Amortisman verisi için KAP PDF parser gerekli."

    return {
        "valuation": results,
        "dcf_note": "FCF verisi yok; tam DCF için nakit akışı tablosu / Capex verisi gerekli (KAP PDF parser)."
    }

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
    all_rows = {}
    period_cols = set()
    for fname in sorted(os.listdir(csv_dir)):
        if not (fname.endswith(".csv") and "bilanco" in fname.lower()):
            continue
        with open(os.path.join(csv_dir, fname), "r", encoding="utf-8-sig") as f:
            first_line = f.readline().strip()
            cols = [c.strip().strip('"') for c in first_line.split(",")]
            cols = ["EMPTY" if c == "" else c for c in cols]
            reader = csv.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get("FINANCIAL_ITEM_CODE", "").strip()
                if not code: continue
                if code not in all_rows: all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        period_cols.add(k)
                        all_rows[code][k] = v.strip() if v else ""

    period_cols = sorted(period_cols, key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
    result = calculate_valuation(all_rows, period_cols)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    # Test: 2024/12 fiyat 340 TL, hisse adedi ~3.5M (yaklaşık)
    print("\n--- Test: ASELS 340 TL, 3.5M hisse ---")
    test = calculate_valuation(all_rows, period_cols, price_per_share=340, shares=3500000)
    print(json.dumps(test, ensure_ascii=False, indent=2, default=str))