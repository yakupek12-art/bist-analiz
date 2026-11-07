"""
Değerleme Modülü - DCF, NAV, ters DCF, çarpan tabanlı değerleme
run_valuation.py tarafından çağrılır.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


def calculate_valuation(
    all_rows: Dict[str, Dict[str, str]],
    period_cols: List[str],
    price_per_share: Optional[float] = None,
    shares: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Bilanço verilerinden değerleme çarpanları hesaplar.

    Parametreler:
        all_rows: {FINANCIAL_ITEM_CODE: {period: value}}  (veri/bilanco.csv'den)
        period_cols: ['2022/12', '2023/12', ...] sıralı dönemler
        price_per_share: Hisse başına fiyat (TL)
        shares: Hisse adedi

    Döndürür:
        dict: P/E, EV/FAVOK, EV/Sales, P/B, P/FCF çarpanları + fair value
    """
    def _to_float(v) -> Optional[float]:
        if v is None or v == "" or v == "-":
            return None
        try:
            return float(str(v).replace(",", "").replace("%", "").strip())
        except (ValueError, TypeError):
            return None

    def _get(code: str, period: str) -> Optional[float]:
        row = all_rows.get(code, {})
        return _to_float(row.get(period))

    # En son dönem (fair value hesaplaması için)
    latest_period = period_cols[-1] if period_cols else None

    # Temel kalemler (son dönem)
    sales = _get("3C", latest_period) if latest_period else None       # Satış geliri
    favok = _get("3DF", latest_period) if latest_period else None     # Faaliyet karı (FAVÖK proxy)
    net_income = _get("3Z", latest_period) if latest_period else None # Net kar
    equity = _get("1AJ", latest_period) if latest_period else None    # Toplam özkaynak
    cash = _get("1AA", latest_period) if latest_period else None      # Nakit
    short_debt = _get("2AA", latest_period) if latest_period else None
    long_debt = _get("2BA", latest_period) if latest_period else None
    fcf = _get("4CB", latest_period) if latest_period else None       # Serbest nakit akışı

    # Net borç
    net_debt = 0
    if short_debt is not None:
        net_debt += short_debt
    if long_debt is not None:
        net_debt += long_debt
    if cash is not None:
        net_debt -= cash

    # Piyasa değeri
    market_cap = None
    if price_per_share and shares:
        market_cap = price_per_share * shares

    enterprise_value = None
    if market_cap is not None:
        enterprise_value = market_cap + net_debt - (cash or 0)

    # 5 yıllık ortalama çarpanlar (basit: mevcut dönem üzerinden)
    def _safe_div(a, b):
        if a is None or b is None or b == 0:
            return None
        return a / b

    result: Dict[str, Any] = {
        "symbol": None,
        "price_per_share": price_per_share,
        "shares": shares,
        "market_cap_mn": round(market_cap / 1e6, 2) if market_cap else None,
        "net_debt_mn": round(net_debt / 1e6, 2),
        "cash_mn": round(cash / 1e6, 2) if cash else None,
        "enterprise_value_mn": round(enterprise_value / 1e6, 2) if enterprise_value else None,
        "latest_period": latest_period,
        "sales_mn": round(sales / 1e6, 2) if sales else None,
        "favok_mn": round(favok / 1e6, 2) if favok else None,
        "net_income_mn": round(net_income / 1e6, 2) if net_income else None,
        "equity_mn": round(equity / 1e6, 2) if equity else None,
        "fcf_mn": round(fcf / 1e6, 2) if fcf else None,
        "net_debt_favok": round(_safe_div(net_debt, favok), 2) if (net_debt and favok) else None,
        "valuation": {},
    }

    rows = []

    # P/E = Market Cap / Net Income
    pe = _safe_div(market_cap, net_income)
    if pe is not None:
        fair_pe = None
        if price_per_share and shares and net_income:
            fair_pe = round((pe * net_income) / shares / 1e6, 4) * 1e6  # dummy, aşağıda düzeltiliyor
        rows.append({
            "method": "P/E",
            "multiple": round(pe, 2),
            "fair_value_tl": round((pe * net_income) / shares, 2) if (pe and net_income and shares) else None,
        })

    # EV/FAVOK
    ev_favok = _safe_div(enterprise_value, favok)
    if ev_favok is not None:
        rows.append({
            "method": "EV/FAVOK",
            "multiple": round(ev_favok, 2),
            "fair_value_tl": round(((ev_favok * favok) - net_debt + (cash or 0)) / shares, 2) if (ev_favok and favok and shares) else None,
        })

    # EV/Sales
    ev_sales = _safe_div(enterprise_value, sales)
    if ev_sales is not None:
        rows.append({
            "method": "EV/Sales",
            "multiple": round(ev_sales, 2),
            "fair_value_tl": round(((ev_sales * sales) - net_debt + (cash or 0)) / shares, 2) if (ev_sales and sales and shares) else None,
        })

    # P/B = Market Cap / Equity
    pb = _safe_div(market_cap, equity)
    if pb is not None:
        rows.append({
            "method": "P/B",
            "multiple": round(pb, 2),
            "fair_value_tl": round((pb * equity) / shares, 2) if (pb and equity and shares) else None,
        })

    # P/FCF
    p_fcf = _safe_div(market_cap, fcf)
    if p_fcf is not None:
        rows.append({
            "method": "P/FCF",
            "multiple": round(p_fcf, 2),
            "fair_value_tl": round((p_fcf * fcf) / shares, 2) if (p_fcf and fcf and shares) else None,
        })

    result["valuation"]["rows"] = rows
    result["valuation"]["count"] = len(rows)

    # Fair value aralığı
    fair_values = [r["fair_value_tl"] for r in rows if r["fair_value_tl"] is not None]
    if fair_values:
        result["valuation"]["fair_value_min"] = round(min(fair_values), 2)
        result["valuation"]["fair_value_max"] = round(max(fair_values), 2)
        result["valuation"]["fair_value_avg"] = round(sum(fair_values) / len(fair_values), 2)
        if price_per_share:
            result["valuation"]["discount_pct"] = round(
                (result["valuation"]["fair_value_avg"] - price_per_share) / price_per_share * 100, 2
            )

    # DCF basit (3 senaryo) - işletme kârı üzerinden
    if favok and shares:
        wacc = 0.15
        growth = 0.03
        years = 5
        dcf_scenarios = {}
        for name, mult in [("kötü", 0.7), ("base", 1.0), ("iyi", 1.3)]:
            proj_favok = favok * mult
            dcf_value = 0
            for y in range(1, years + 1):
                dcf_value += proj_favok * ((1 + growth) ** y) / ((1 + wacc) ** y)
            terminal = proj_favok * (1 + growth) / (wacc - growth) / ((1 + wacc) ** years)
            dcf_value += terminal
            equity_value = dcf_value - net_debt + (cash or 0)
            dcf_scenarios[name] = {
                "dcf_value_mn": round(dcf_value / 1e6, 2),
                "equity_value_mn": round(equity_value / 1e6, 2),
                "fair_value_tl": round(equity_value / shares, 2),
            }
        result["valuation"]["dcf_scenarios"] = dcf_scenarios

    result["generated_at"] = datetime.now().isoformat()
    return result


if __name__ == "__main__":
    import json
    # Test
    test_rows = {
        "3C": {"2024/12": "1000000000", "2023/12": "900000000"},
        "3DF": {"2024/12": "200000000", "2023/12": "180000000"},
        "3Z": {"2024/12": "100000000", "2023/12": "90000000"},
        "1AJ": {"2024/12": "500000000", "2023/12": "450000000"},
        "1AA": {"2024/12": "50000000", "2023/12": "40000000"},
        "2AA": {"2024/12": "100000000", "2023/12": "90000000"},
        "2BA": {"2024/12": "200000000", "2023/12": "180000000"},
        "4CB": {"2024/12": "80000000", "2023/12": "70000000"},
    }
    test_cols = ["2023/12", "2024/12"]
    res = calculate_valuation(test_rows, test_cols, price_per_share=50.0, shares=10000000)
    print(json.dumps(res, ensure_ascii=False, indent=2))
