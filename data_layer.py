"""
Data Layer - Çoklu kaynak, cache, retry, schema validation
Async, paralel veri çekme için tasarlandı.
Pandas/yfinance opsiyonel - olmazsa fallback'ler çalışır.
"""

import asyncio
import json
import os
import csv
import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from functools import lru_cache

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import diskcache
from pydantic import BaseModel, Field, validator, field_validator
from pydantic_settings import BaseSettings

# Optional imports - pandas/yfinance olmazsa fallback'ler çalışır
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False
    print("[WARNING] yfinance not available, using fallback prices")

PANDAS_AVAILABLE = False
pd = None
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except (ImportError, AttributeError):
    pd = None
    PANDAS_AVAILABLE = False
    print("[WARNING] pandas not available, using raw data parsing")


# ============================================================
# CONFIG
# ============================================================

class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # .env'de ekstra alanlar olsa hata verme
    
    # API Keys (optional)
    alpha_vantage_key: str = ""
    polygon_key: str = ""
    nvidia_api_key: str = ""  # NVIDIA API key for AI calls
    
    # Cache settings
    cache_dir: str = "./cache"
    cache_ttl: int = 86400  # 24 hours (was 1 hour)
    
    # HTTP settings
    timeout: int = 120  # isyatirimhisse için 60->120s
    max_retries: int = 5
    retry_wait: float = 2.0


settings = Settings()


# ============================================================
# YAHOO FINANCE API HELPER METHODS
# ============================================================

async def fetch_yahoo_chart(symbol: str, time_range: str = "1y", interval: str = "1d") -> dict:
    """
    Yahoo Finance Chart API'den veri çeker.
    URL: https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={time_range}&interval={interval}
    """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"range": time_range, "interval": interval}
    
    async with httpx.AsyncClient(timeout=30.0, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}) as client:
        # Retry logic for 429
        for attempt in range(3):
            response = await client.get(url, params=params)
            if response.status_code == 429:
                wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                print(f"[yahoo_chart] Rate limited (429), waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            response.raise_for_status()
            return response.json()
        # Last attempt
        response.raise_for_status()
        return response.json()


async def fetch_yahoo_quote_summary(symbol: str) -> dict:
    """
    Yahoo Finance Quote Summary API'den finansal verileri çeker.
    Modules: financialData, defaultKeyStatistics, incomeStatementHistory, 
             balanceSheetHistory, cashflowStatementHistory, calendarEvents
    """
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {
        "modules": "financialData,defaultKeyStatistics,incomeStatementHistory,"
                   "balanceSheetHistory,cashflowStatementHistory,calendarEvents"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        # Retry logic for 429
        for attempt in range(3):
            response = await client.get(url, params=params)
            if response.status_code == 429:
                wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                print(f"[yahoo_quote] Rate limited (429), waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            if response.status_code == 401:
                print(f"[yahoo_quote] 401 Unauthorized - trying alternative approach...")
                # Try with crumb if needed
                break
            response.raise_for_status()
            return response.json()
        # If we get here, raise the last error
        response.raise_for_status()
        return response.json()


async def fetch_yahoo_financials(symbol: str) -> List[PeriodData]:
    """
    Yahoo Finance'ten finansal verileri çeker ve PeriodData listesine dönüştürür.
    401 hatasında boş liste döner (fallback için).
    """
    try:
        data = await fetch_yahoo_quote_summary(symbol)
        result = data.get("quoteSummary", {}).get("result", [])
        if not result:
            return []
        
        quote = result[0]
        periods = []
        
        # Income Statement History
        income_history = quote.get("incomeStatementHistory", {}).get("incomeStatementHistory", [])
        balance_history = quote.get("balanceSheetHistory", {}).get("balanceSheetStatements", [])
        cashflow_history = quote.get("cashflowStatementHistory", {}).get("cashflowStatements", [])
        
        # Build period map from income statement
        for stmt in income_history:
            period_raw = stmt.get("endDate", {}).get("fmt", "")
            if not period_raw:
                continue
            
            try:
                # Parse date - format like "2023-12-31"
                dt = datetime.strptime(period_raw, "%Y-%m-%d")
                period_str = dt.strftime("%Y/%m")
            except:
                continue
            
            # Helper to get raw value from Yahoo's format
            def get_raw(obj, key):
                if isinstance(obj, dict) and key in obj:
                    val = obj[key].get("raw")
                    if val is not None:
                        return val
                return None
            
            pdata = {"period": period_str}
            
            # Income statement items
            pdata["sales"] = get_raw(stmt, "totalRevenue")
            pdata["net_income"] = get_raw(stmt, "netIncome")
            pdata["favok"] = get_raw(stmt, "ebitda")  # EBITDA as FAVOK proxy
            
            # Find matching balance sheet
            for bs in balance_history:
                bs_date = bs.get("endDate", {}).get("fmt", "")
                if bs_date == period_raw:
                    pdata["total_assets"] = get_raw(bs, "totalAssets")
                    pdata["equity"] = get_raw(bs, "totalEquity")
                    pdata["short_debt"] = get_raw(bs, "shortLongTermDebt")
                    pdata["long_debt"] = get_raw(bs, "longTermDebt")
                    pdata["cash"] = get_raw(bs, "cash")
                    break
            
            # Find matching cash flow
            for cf in cashflow_history:
                cf_date = cf.get("endDate", {}).get("fmt", "")
                if cf_date == period_raw:
                    pdata["fcf"] = get_raw(cf, "freeCashFlow")
                    pdata["cfo"] = get_raw(cf, "operatingCashFlow")
                    break
            
            periods.append(pdata)
        
        # Convert to PeriodData objects (values are in raw numbers, convert to Mn TL)
        result_periods = []
        for p in periods:
            # Convert to millions TL
            for field in ["sales", "favok", "net_income", "fcf", "cfo", "equity", 
                         "short_debt", "long_debt", "cash", "total_assets"]:
                if p.get(field) is not None:
                    p[field] = p[field] / 1_000_000
            
            # Calculate derived fields
            if p.get("favok") and p.get("sales") and p["sales"] > 0:
                p["favok_margin"] = round(p["favok"] / p["sales"] * 100, 2)
            if p.get("net_income") and p.get("sales") and p["sales"] > 0:
                p["net_margin"] = round(p["net_income"] / p["sales"] * 100, 2)
            
            net_debt = (p.get("short_debt", 0) or 0) + (p.get("long_debt", 0) or 0) - (p.get("cash", 0) or 0)
            p["net_debt"] = net_debt
            if p.get("favok") and p["favok"] > 0:
                p["net_debt_favok"] = round(net_debt / p["favok"], 2)
            
            if p.get("cfo") and p.get("net_income") and p["net_income"] != 0:
                p["fcf_net_income"] = round(p["cfo"] / p["net_income"], 2)
            
            if p.get("net_income") and p.get("equity") and p["equity"] > 0:
                p["roic"] = round(p["net_income"] / p["equity"] * 100, 2)
                p["roic_pct"] = p["roic"]
            
            if p.get("favok") and p.get("sales") and p["sales"] > 0:
                p["gross_margin"] = p["favok_margin"]
                p["gross_margin_pct"] = p["favok_margin"]
            
            if p.get("net_income") and p.get("sales") and p["sales"] > 0:
                p["net_margin_pct"] = p["net_margin"]
            
            # Current ratio (simplified)
            current_assets = p.get("cash", 0) or 0
            current_liabilities = p.get("short_debt", 0) or 0
            if current_liabilities > 0:
                p["current_ratio"] = round(current_assets / current_liabilities, 2)
            
            result_periods.append(PeriodData(**p))
        
        return result_periods
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print(f"[yahoo_financials] 401 Unauthorized - Quote Summary API requires authentication, returning empty for fallback")
            return []
        print(f"[yahoo_financials] HTTP Error: {e}")
        return []
    except Exception as e:
        print(f"[yahoo_financials] Error: {e}")
        import traceback
        traceback.print_exc()
        return []


async def fetch_yahoo_technical(symbol: str) -> TechnicalData:
    """
    Yahoo Finance Chart API'den fiyat verisi çeker ve teknik indikatörleri hesaplar.
    """
    import numpy as np
    import talib
    
    try:
        # Get 1 year daily data
        chart_data = await fetch_yahoo_chart(symbol, time_range="1y", interval="1d")
        result = chart_data.get("chart", {}).get("result", [])
        if not result:
            raise ValueError("No chart data")
        
        chart = result[0]
        timestamps = chart.get("timestamp", [])
        indicators = chart.get("indicators", {}).get("quote", [{}])[0]
        adjclose_list = chart.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [[]])
        adjclose = adjclose_list[0] if adjclose_list else []
        
        if not timestamps or not indicators.get("close"):
            raise ValueError("No price data")
        
        closes = indicators["close"]
        highs = indicators["high"]
        lows = indicators["low"]
        volumes = indicators["volume"]
        
        # Filter out None values
        valid_data = []
        for i, (t, c, h, l, v) in enumerate(zip(timestamps, closes, highs, lows, volumes)):
            if c is not None and h is not None and l is not None and v is not None:
                valid_data.append((t, c, h, l, v))
        
        if len(valid_data) < 50:
            raise ValueError(f"Insufficient data points: {len(valid_data)}")
        
        # Use adjusted close if available, otherwise close
        if adjclose and isinstance(adjclose, list) and len(adjclose) == len(closes):
            closes = [adjclose[i] if adjclose[i] is not None else closes[i] for i in range(len(closes))]
        
        closes_arr = np.array([d[1] for d in valid_data], dtype=float)
        highs_arr = np.array([d[2] for d in valid_data], dtype=float)
        lows_arr = np.array([d[3] for d in valid_data], dtype=float)
        vols_arr = np.array([d[4] for d in valid_data], dtype=float)
        
        rsi = talib.RSI(closes_arr, 14)[-1]
        macd, signal, hist = talib.MACD(closes_arr)
        sma20 = talib.SMA(closes_arr, 20)[-1]
        sma50 = talib.SMA(closes_arr, 50)[-1]
        sma200 = talib.SMA(closes_arr, 200)[-1]
        adx = talib.ADX(highs_arr, lows_arr, closes_arr, 14)[-1]
        atr = talib.ATR(highs_arr, lows_arr, closes_arr, 14)[-1]
        bb_up, bb_mid, bb_low = talib.BBANDS(closes_arr, 20)
        vol_avg = np.mean(vols_arr[-20:])
        
        last_price = closes_arr[-1]
        trend = "YUKARI" if last_price > sma200 else ("ASAGI" if last_price < sma50 else "YATAY")
        
        return TechnicalData(
            symbol=symbol.replace('.IS', ''),
            price=last_price,
            sma20=float(sma20) if not np.isnan(sma20) else None,
            sma50=float(sma50) if not np.isnan(sma50) else None,
            sma200=float(sma200) if not np.isnan(sma200) else None,
            rsi=float(rsi) if not np.isnan(rsi) else None,
            macd=float(macd[-1]) if not np.isnan(macd[-1]) else None,
            macd_signal=float(signal[-1]) if not np.isnan(signal[-1]) else None,
            adx=float(adx) if not np.isnan(adx) else None,
            atr=float(atr) if not np.isnan(atr) else None,
            bb_upper=float(bb_up[-1]) if not np.isnan(bb_up[-1]) else None,
            bb_lower=float(bb_low[-1]) if not np.isnan(bb_low[-1]) else None,
            bb_middle=float(bb_mid[-1]) if not np.isnan(bb_mid[-1]) else None,
            volume_avg_20=float(vol_avg) if not np.isnan(vol_avg) else None,
            trend=trend,
            support=float(sma50) if not np.isnan(sma50) else None,
            resistance=float(sma20) if not np.isnan(sma20) else None,
            stop_loss=round(last_price - 2 * atr, 2) if not np.isnan(atr) else None,
            target=round(last_price + 3 * atr, 2) if not np.isnan(atr) else None,
            risk_reward=f"1:{round(3 * atr / (2 * atr), 1)}" if not np.isnan(atr) else "1:3"
        )
        
    except Exception as e:
        print(f"[yahoo_technical] Error: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to KAP price
        return TechnicalData(symbol=symbol.replace('.IS', ''), price=0)


# ============================================================
# PYDANTIC MODELS - Schema Validation
# ============================================================

class PeriodData(BaseModel):
    """Tek bir dönem için finansal veriler"""
    period: str
    sales: Optional[float] = None          # Mn TL
    favok: Optional[float] = None          # Mn TL
    net_income: Optional[float] = None     # Mn TL
    favok_margin: Optional[float] = None   # %
    net_margin: Optional[float] = None     # %
    net_debt_favok: Optional[float] = None # x
    current_ratio: Optional[float] = None  # x
    fcf_net_income: Optional[float] = None # %
    roic: Optional[float] = None           # %
    gross_margin: Optional[float] = None   # %
    fcf: Optional[float] = None            # Mn TL
    equity: Optional[float] = None         # Mn TL
    net_debt: Optional[float] = None       # Mn TL
    cash: Optional[float] = None           # Mn TL
    short_debt: Optional[float] = None     # Mn TL
    long_debt: Optional[float] = None      # Mn TL
    total_assets: Optional[float] = None   # Mn TL
    cfo: Optional[float] = None            # Mn TL - İşletme nakit akışı
    roic_pct: Optional[float] = None       # %
    gross_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    
    @field_validator('*', mode='before')
    @classmethod
    def convert_to_float(cls, v, info):
        # Skip period field - it should remain a string
        if info.field_name == 'period':
            return v
        if v is None or v == '' or v == '-':
            return None
        if isinstance(v, str):
            v = v.replace(',', '').replace('%', '').strip()
            if v == '' or v.lower() in ('nan', 'null', 'none', '-'):
                return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class FinancialData(BaseModel):
    """Normalize edilmiş finansal veri"""
    symbol: str
    periods: List[PeriodData] = []
    metadata: Dict = {}
    
    @property
    def periods_sorted(self) -> List[PeriodData]:
        """En güncel -> en eski (sadece 5 yıl sonu: 2026/6, 2025/12, 2024/12, 2023/12, 2022/12)"""
        def period_key(p: PeriodData):
            try:
                return datetime.strptime(p.period, "%Y/%m")
            except:
                return datetime.min
        # Sadece yıl sonu dönemleri: /12 veya /6 (yıl sonu)
        year_ends = [p for p in self.periods if p.period.endswith('/12') or p.period.endswith('/6')]
        return sorted(year_ends, key=period_key, reverse=True)[:5]
    
    def get_latest_period(self) -> Optional[PeriodData]:
        """En güncel dönem"""
        sorted_periods = self.periods_sorted
        return sorted_periods[0] if sorted_periods else None
    
    def get_year_ends(self) -> List[PeriodData]:
        """Yıl sonu dönemler (2026/6, 2025/12, 2024/12, 2023/12, 2022/12) - en fazla 5 adet"""
        year_ends = [p for p in self.periods if p.period.endswith('/12') or p.period.endswith('/6')]
        return sorted(year_ends, key=lambda p: datetime.strptime(p.period, "%Y/%m"), reverse=True)[:5]
    
    def get_piotroski_fscore(self) -> Dict:
        """Piotroski F-Skoru hesapla (son 2 yıl sonu karşılaştırma)"""
        year_ends = self.get_year_ends()
        if len(year_ends) < 2:
            return {"score": 0, "details": {}, "error": "Yeterli dönem yok"}
        
        current = year_ends[0]   # En güncel yıl sonu
        prior = year_ends[1]     # Önceki yıl sonu
        
        score = 0
        details = {}
        
        # 1. Net Income > 0
        ni_pos = 1 if (current.net_income or 0) > 0 else 0
        score += ni_pos
        details["net_income_pos"] = ni_pos
        details["net_income_pos_val"] = current.net_income
        
        # 2. CFO > 0 (Operating Cash Flow)
        cfo = getattr(current, 'cfo', None)
        cfo_pos = 1 if (cfo or 0) > 0 else 0
        score += cfo_pos
        details["cfo_positive"] = cfo_pos
        details["cfo_positive_val"] = cfo
        
        # 3. ROA improving (Net Income / Total Assets)
        roa_cur = (current.net_income or 0) / (current.total_assets or 1) if current.total_assets else 0
        roa_pri = (prior.net_income or 0) / (prior.total_assets or 1) if prior.total_assets else 0
        roa_imp = 1 if roa_cur > roa_pri else 0
        score += roa_imp
        details["roa_improving"] = roa_imp
        details["roa_improving_val"] = f"{round(roa_cur*100,2)}% vs {round(roa_pri*100,2)}%"
        
        # 4. CFO > Net Income (Quality of earnings)
        cfo_gt_ni = 1 if (cfo or 0) > (current.net_income or 0) else 0
        score += cfo_gt_ni
        details["cfo_gt_ni"] = cfo_gt_ni
        details["cfo_gt_ni_val"] = f"CFO: {cfo:.1f}M, NI: {current.net_income:.1f}M" if cfo else "CFO verisi yok"
        
        # 5. Long-term debt decreasing
        lt_debt_cur = current.long_debt or 0
        lt_debt_pri = prior.long_debt or 0
        debt_dec = 1 if lt_debt_cur < lt_debt_pri else 0
        score += debt_dec
        details["debt_decreasing"] = debt_dec
        details["debt_decreasing_val"] = f"{lt_debt_cur:.1f}M vs {lt_debt_pri:.1f}M"
        
        # 6. Current ratio improving
        cr_cur = current.current_ratio or 0
        cr_pri = prior.current_ratio or 0
        cr_imp = 1 if cr_cur > cr_pri else 0
        score += cr_imp
        details["current_ratio_improving"] = cr_imp
        details["current_ratio_improving_val"] = f"{cr_cur:.2f}x vs {cr_pri:.2f}x"
        
        # 7. No dilution (Equity growth <= Net Income growth + tolerance)
        eq_cur = current.equity or 0
        eq_pri = prior.equity or 0
        ni_growth = ((current.net_income or 0) - (prior.net_income or 0)) / abs(prior.net_income or 1) if prior.net_income else 0
        eq_growth = (eq_cur - eq_pri) / abs(eq_pri) if eq_pri else 0
        no_dil = 1 if eq_growth <= ni_growth + 0.1 else 0
        score += no_dil
        details["no_dilution"] = no_dil
        details["no_dilution_val"] = f"Özkaynak büyüme: {round(eq_growth*100,1)}%, Kâr büyüme: {round(ni_growth*100,1)}%"
        
        # 8. Gross margin improving
        gm_cur = current.gross_margin or current.favok_margin or 0
        gm_pri = prior.gross_margin or prior.favok_margin or 0
        gm_imp = 1 if gm_cur > gm_pri else 0
        score += gm_imp
        details["gross_margin_improving"] = gm_imp
        details["gross_margin_improving_val"] = f"{gm_cur:.2f}% vs {gm_pri:.2f}%"
        
        # 9. Asset turnover improving (Sales / Total Assets)
        at_cur = (current.sales or 0) / (current.total_assets or 1) if current.total_assets else 0
        at_pri = (prior.sales or 0) / (prior.total_assets or 1) if prior.total_assets else 0
        at_imp = 1 if at_cur > at_pri else 0
        score += at_imp
        details["asset_turnover_improving"] = at_imp
        details["asset_turnover_improving_val"] = f"{round(at_cur,2)}x vs {round(at_pri,2)}x"
        
        return {
            "score": score,
            "details": details,
            "period_current": current.period,
            "period_prior": prior.period
        }
    
    def get_cash_profit_alignment(self) -> Dict:
        """Kar-Nakit uyumu: CFO vs Net Income"""
        year_ends = self.get_year_ends()
        if not year_ends:
            return {"verdict": "VERI_YOK", "detail": "Dönem yok"}
        
        latest = year_ends[0]
        cfo = getattr(latest, 'cfo', None)
        net_income = latest.net_income
        
        if cfo is None or net_income is None:
            return {"verdict": "VERI_YOK", "detail": "CFO veya Net Kar verisi yok"}
        
        # CFO already in Mn TL after conversion
        cfo_mn = cfo
        ni_mn = net_income
        
        if cfo_mn > 0 and ni_mn > 0:
            ratio = cfo_mn / ni_mn
            if ratio >= 1.0:
                return {"verdict": "EVET", "detail": f"CFO ({cfo_mn:.1f}M) > Net Kar ({ni_mn:.1f}M), oran: {ratio:.2f}x"}
            else:
                return {"verdict": "KISMEN", "detail": f"CFO ({cfo_mn:.1f}M) < Net Kar ({ni_mn:.1f}M), oran: {ratio:.2f}x"}
        elif cfo_mn < 0 and ni_mn > 0:
            return {"verdict": "HAYIR", "detail": f"CFO negatif ({cfo_mn:.1f}M), Net Kar pozitif ({ni_mn:.1f}M) - Kâr nakite dönmüyor"}
        else:
            return {"verdict": "KARMAŞIK", "detail": f"CFO: {cfo_mn:.1f}M, Net Kar: {ni_mn:.1f}M"}


class TechnicalData(BaseModel):
    """Teknik analiz verileri"""
    symbol: str
    price: float
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma200: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    adx: Optional[float] = None
    atr: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_middle: Optional[float] = None
    volume_avg_20: Optional[float] = None
    trend: str = "UNKNOWN"
    support: Optional[float] = None
    resistance: Optional[float] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    risk_reward: Optional[str] = None


class NewsItem(BaseModel):
    title: str
    source: str
    date: str
    url: str
    summary: str = ""


class KAPNotification(BaseModel):
    disclosure_type: str
    title: str
    date: str
    url: str
    summary: str = ""


class CompleteData(BaseModel):
    """Tüm verilerin birleşimi"""
    symbol: str
    financial: FinancialData
    technical: TechnicalData
    news: List[NewsItem] = []
    kap_notifications: List[KAPNotification] = []
    sector_peers: List[str] = []
    sector_name: str = ""
    fetched_at: str = ""


# ============================================================
# HTTP CLIENT WITH RETRY + CACHE
# ============================================================

class DataFetcher:
    """Async HTTP client with retry, cache, multi-source"""
    
    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self.cache = diskcache.Cache(self.settings.cache_dir)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.settings.timeout),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FinancialAnalysis/1.0"}
        )
    
    async def close(self):
        await self.client.aclose()
        self.cache.close()
    
    def _cache_key(self, prefix: str, *args) -> str:
        # Include all args to ensure symbol isolation
        return f"{prefix}:{':'.join(str(a) for a in args)}"
    
    def _get_cached(self, key: str):
        try:
            return self.cache.get(key)
        except:
            return None
    
    def _set_cache(self, key: str, value: Any, ttl: int = None):
        try:
            self.cache.set(key, value, expire=ttl or self.settings.cache_ttl)
        except:
            pass
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError))
    )
    async def _fetch_with_retry(self, url: str, params: dict = None) -> httpx.Response:
        response = await self.client.get(url, params=params)
        # 429/503 için özel handling
        if response.status_code in (429, 503):
            response.raise_for_status()
        return response
    
    async def fetch_json(self, url: str, params: dict = None, cache_key: str = None, cache_ttl: int = None) -> dict:
        """JSON fetch with cache"""
        if cache_key:
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        response = await self._fetch_with_retry(url, params)
        data = response.json()
        
        if cache_key:
            self._set_cache(cache_key, data, cache_ttl)
        return data
    
    async def fetch_text(self, url: str, params: dict = None, cache_key: str = None, cache_ttl: int = None) -> str:
        """Text fetch with cache"""
        if cache_key:
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        response = await self._fetch_with_retry(url, params)
        text = response.text
        
        if cache_key:
            self._set_cache(cache_key, text, cache_ttl)
        return text


# ============================================================
# VERİ KAYNAKLARI - MULTI SOURCE
# ============================================================

class FinancialDataProvider:
    """Çoklu kaynak finansal veri sağlayıcı - Yahoo Finance ana kaynak"""
    
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher
    
    async def fetch_yahoo_financials(self, symbol: str) -> List[PeriodData]:
        """Yahoo Finance API'den finansal verileri çek (ana kaynak)"""
        return await fetch_yahoo_financials(symbol)
    
    async def fetch_isfinansal(self, symbol: str) -> List[PeriodData]:
        """isyatirimhisse verisi çek - fallback olarak tutuluyor"""
        try:
            import isyatirimhisse
        except (ImportError, AttributeError) as e:
            print(f"[isyatirimhisse] Not available: {e}")
            return []
        
        # isyatirimhisse python paketi sync olduğu için thread pool'da çalıştır
        loop = asyncio.get_event_loop()
        
        def _fetch():
            try:
                from isyatirimhisse import fetch_financials
                df = fetch_financials(symbols=symbol.replace('.IS', ''), start_year="2020", end_year="2026")
                return df
            except Exception as e:
                print(f"[isyatirimhisse] Error: {e}")
                return None
        
        try:
            df = await asyncio.get_event_loop().run_in_executor(None, _fetch)
            if df is None or (hasattr(df, 'empty') and df.empty):
                return []
            
            # Get period columns (those with / and starting with digit)
            period_cols = [col for col in df.columns if isinstance(col, str) and '/' in col and col[0].isdigit()]
            
            # Helper to get value for a financial item code
            def get_value(code: str, period: str):
                row = df[df['FINANCIAL_ITEM_CODE'] == code]
                if not row.empty:
                    val = row[period].values[0]
                    try:
                        return float(val)
                    except:
                        return None
                return None
            
            # Map of field names to financial item codes
            field_codes = {
                'sales': ['3C', 'satislar'],
                'favok': ['3DF', 'favok'],
                'net_income': ['3Z', 'net_kar_anaortak'],
                'fcf': ['4CB', 'fcf'],
                'cfo': ['4CA', 'isletme_nakit_akimi'],  # CFO - Operating Cash Flow
                'equity': ['2N', 'ozkaynak'],
                'short_debt': ['2AA', 'kisa_vadeli_borc'],
                'long_debt': ['2BA', 'uzun_vadeli_borc'],
                'cash': ['1AA', 'nakit'],
                'total_assets': ['1A', 'toplam_varlik'],
            }
            
            periods = []
            for period in period_cols:
                # Build period data
                pdata = {'period': period}
                
                for field, codes in field_codes.items():
                    val = None
                    for code in codes:
                        val = get_value(code, period)
                        if val is not None:
                            break
                    pdata[field] = val
                
                # Calculate derived fields if possible
                if pdata.get('favok') and pdata.get('sales') and pdata['sales'] > 0:
                    pdata['favok_margin'] = round(pdata['favok'] / pdata['sales'] * 100, 2)
                
                if pdata.get('net_income') and pdata.get('sales') and pdata['sales'] > 0:
                    pdata['net_margin'] = round(pdata['net_income'] / pdata['sales'] * 100, 2)
                
                # Net debt / FAVOK
                net_debt = (pdata.get('short_debt', 0) or 0) + (pdata.get('long_debt', 0) or 0) - (pdata.get('cash', 0) or 0)
                if pdata.get('favok') and pdata['favok'] > 0:
                    pdata['net_debt_favok'] = round(net_debt / pdata['favok'], 2)
                
                # Current ratio
                current_assets = pdata.get('cash', 0) or 0  # Simplified
                current_liabilities = pdata.get('short_debt', 0) or 0
                if current_liabilities > 0:
                    pdata['current_ratio'] = round(current_assets / current_liabilities, 2)
                
                # FCF / Net Income
                if pdata.get('fcf') and pdata.get('net_income') and pdata['net_income'] != 0:
                    pdata['fcf_net_income'] = round(pdata['fcf'] / pdata['net_income'], 2)
                
                # ROIC - simplified
                if pdata.get('net_income') and pdata.get('equity') and pdata['equity'] > 0:
                    pdata['roic'] = round(pdata['net_income'] / pdata['equity'] * 100, 2)
                
                period_obj = PeriodData(**pdata)
                periods.append(period_obj)
            
            # Convert to Mn TL
            for p in periods:
                for field in ['sales', 'favok', 'net_income', 'fcf', 'cfo', 'equity', 'net_debt', 'cash', 'short_debt', 'long_debt', 'total_assets']:
                    val = getattr(p, field)
                    if val is not None:
                        setattr(p, field, val / 1_000_000)
            
            return periods
        except Exception as e:
            print(f"[isyatirimhisse] Error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def fetch_yfinance(self, symbol: str) -> List[PeriodData]:
        """yfinance fallback - pandas/yfinance yoksa boş döner"""
        if not YFINANCE_AVAILABLE:
            print("[yfinance] Not available, skipping")
            return []
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5y", interval="1mo")
            if hist.empty:
                return []
            
            # Get financials
            fin = ticker.financials
            if fin.empty:
                return []
            
            periods = []
            for col in fin.columns:
                if hasattr(col, 'strftime'):
                    period_str = col.strftime("%Y/%m")
                    row = fin[col]
                    periods.append(PeriodData(
                        period=period_str,
                        sales=row.get('Total Revenue', 0) / 1_000_000,
                        favok=row.get('EBITDA', 0) / 1_000_000,
                        net_income=row.get('Net Income', 0) / 1_000_000,
                        fcf=row.get('Free Cash Flow', 0) / 1_000_000,
                        equity=row.get('Total Equity', 0) / 1_000_000,
                        net_debt=row.get('Net Debt', 0) / 1_000_000,
                        cash=row.get('Cash', 0) / 1_000_000,
                    ))
            return periods
        except Exception as e:
            print(f"[yfinance] Error: {e}")
            return []
    
    async def fetch_price_technical(self, symbol: str) -> TechnicalData:
        """Fiyat ve teknik veriler - Yahoo Finance API (ana kaynak)"""
        # Yahoo Finance API'yi doğrudan kullan (yfinance kütüphanesine bağımlılık yok)
        try:
            return await fetch_yahoo_technical(symbol)
        except Exception as e:
            print(f"[technical] Yahoo Finance API Error: {e}, trying yfinance fallback...")
            
            # Fallback to yfinance if available
            if YFINANCE_AVAILABLE:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1y", interval="1d")
                    if not hist.empty:
                        closes = hist['Close'].values
                        highs = hist['High'].values
                        lows = hist['Low'].values
                        volumes = hist['Volume'].values
                        
                        import numpy as np
                        import talib
                        
                        closes_arr = np.array(closes, dtype=float)
                        highs_arr = np.array(highs, dtype=float)
                        lows_arr = np.array(lows, dtype=float)
                        vols_arr = np.array(volumes, dtype=float)
                        
                        rsi = talib.RSI(closes_arr, 14)[-1]
                        macd, signal, hist = talib.MACD(closes_arr)
                        sma20 = talib.SMA(closes_arr, 20)[-1]
                        sma50 = talib.SMA(closes_arr, 50)[-1]
                        sma200 = talib.SMA(closes_arr, 200)[-1]
                        adx = talib.ADX(highs_arr, lows_arr, closes_arr, 14)[-1]
                        atr = talib.ATR(highs_arr, lows_arr, closes_arr, 14)[-1]
                        bb_up, bb_mid, bb_low = talib.BBANDS(closes_arr, 20)
                        vol_avg = np.mean(volumes[-20:])
                        
                        last_price = closes[-1]
                        trend = "YUKARI" if last_price > sma200 else ("ASAGI" if last_price < sma50 else "YATAY")
                        
                        return TechnicalData(
                            symbol=symbol.replace('.IS', ''),
                            price=last_price,
                            sma20=float(sma20) if not np.isnan(sma20) else None,
                            sma50=float(sma50) if not np.isnan(sma50) else None,
                            sma200=float(sma200) if not np.isnan(sma200) else None,
                            rsi=float(rsi) if not np.isnan(rsi) else None,
                            macd=float(macd[-1]) if not np.isnan(macd[-1]) else None,
                            macd_signal=float(signal[-1]) if not np.isnan(signal[-1]) else None,
                            adx=float(adx) if not np.isnan(adx) else None,
                            atr=float(atr) if not np.isnan(atr) else None,
                            bb_upper=float(bb_up[-1]) if not np.isnan(bb_up[-1]) else None,
                            bb_lower=float(bb_low[-1]) if not np.isnan(bb_low[-1]) else None,
                            bb_middle=float(bb_mid[-1]) if not np.isnan(bb_mid[-1]) else None,
                            volume_avg_20=float(vol_avg) if not np.isnan(vol_avg) else None,
                            trend=trend,
                            support=float(sma50) if not np.isnan(sma50) else None,
                            resistance=float(sma20) if not np.isnan(sma20) else None,
                            stop_loss=round(last_price - 2 * atr, 2) if not np.isnan(atr) else None,
                            target=round(last_price + 3 * atr, 2) if not np.isnan(atr) else None,
                            risk_reward=f"1:{round(3 * atr / (2 * atr), 1)}" if not np.isnan(atr) else "1:3"
                        )
                except Exception as e2:
                    print(f"[technical] yfinance fallback Error: {e2}")
            
            # Final fallback: pandas-datareader
            print("[technical] Using pandas-datareader fallback...")
            return await self._fetch_price_technical_fallback(symbol)
    
    async def _fetch_price_technical_fallback(self, symbol: str) -> TechnicalData:
        """pandas-datareader ile yfinance fallback - teknik indikatörler hesapla"""
        try:
            import pandas_datareader.data as web
            import numpy as np
            import talib
            
            sym = symbol.replace('.IS', '')
            # Yahoo Finance'ten veri çek
            end = datetime.now()
            start = end - timedelta(days=365)
            
            try:
                df = web.DataReader(sym, 'yahoo', start, end)
            except:
                # Alpha Vantage fallback
                df = web.DataReader(sym, 'av-daily', start, end)
            
            if df.empty:
                price = await self._fetch_price_from_kap(symbol)
                return TechnicalData(symbol=symbol.replace('.IS', ''), price=price or 0)
            
            closes = df['Close'].values
            highs = df['High'].values
            lows = df['Low'].values
            volumes = df['Volume'].values
            
            import talib
            import numpy as np
            
            closes_arr = np.array(closes, dtype=float)
            highs_arr = np.array(highs, dtype=float)
            lows_arr = np.array(lows, dtype=float)
            vols_arr = np.array(volumes, dtype=float)
            
            rsi = talib.RSI(closes_arr, 14)[-1]
            macd, signal, hist = talib.MACD(closes_arr)
            sma20 = talib.SMA(closes_arr, 20)[-1]
            sma50 = talib.SMA(closes_arr, 50)[-1]
            sma200 = talib.SMA(closes_arr, 200)[-1]
            adx = talib.ADX(highs_arr, lows_arr, closes_arr, 14)[-1]
            atr = talib.ATR(highs_arr, lows_arr, closes_arr, 14)[-1]
            bb_up, bb_mid, bb_low = talib.BBANDS(closes_arr, 20)
            vol_avg = np.mean(volumes[-20:])
            
            last_price = closes[-1]
            trend = "YUKARI" if last_price > sma200 else ("ASAGI" if last_price < sma50 else "YATAY")
            
            return TechnicalData(
                symbol=symbol.replace('.IS', ''),
                price=last_price,
                sma20=float(sma20) if not np.isnan(sma20) else None,
                sma50=float(sma50) if not np.isnan(sma50) else None,
                sma200=float(sma200) if not np.isnan(sma200) else None,
                rsi=float(rsi) if not np.isnan(rsi) else None,
                macd=float(macd[-1]) if not np.isnan(macd[-1]) else None,
                macd_signal=float(signal[-1]) if not np.isnan(signal[-1]) else None,
                adx=float(adx) if not np.isnan(adx) else None,
                atr=float(atr) if not np.isnan(atr) else None,
                bb_upper=float(bb_up[-1]) if not np.isnan(bb_up[-1]) else None,
                bb_lower=float(bb_low[-1]) if not np.isnan(bb_low[-1]) else None,
                bb_middle=float(bb_mid[-1]) if not np.isnan(bb_mid[-1]) else None,
                volume_avg_20=float(vol_avg) if not np.isnan(vol_avg) else None,
                trend=trend,
                support=float(sma50) if not np.isnan(sma50) else None,
                resistance=float(sma20) if not np.isnan(sma20) else None,
                stop_loss=round(last_price - 2 * atr, 2) if not np.isnan(atr) else None,
                target=round(last_price + 3 * atr, 2) if not np.isnan(atr) else None,
                risk_reward=f"1:{round(3 * atr / (2 * atr), 1)}" if not np.isnan(atr) else "1:3"
            )
        except Exception as e:
            print(f"[technical] fallback Error: {e}")
            # Fallback: KAP'tan fiyat
            price = await self._fetch_price_from_kap(symbol)
            return TechnicalData(symbol=symbol.replace('.IS', ''), price=price or 0)
    
    async def _fetch_price_from_kap(self, symbol: str) -> Optional[float]:
        """KAP'tan son fiyat al (basit fallback)"""
        # Bilinen son fiyatlar (fallback)
        known_prices = {
            'SDTTR': 11.50,
            'TUPRS': 180.00,
            'ASELS': 65.00,
            'THYAO': 280.00,
            'EREGL': 45.00,
            'SISE': 35.00,
            'PETKM': 20.00,
        }
        sym = symbol.replace('.IS', '')
        return known_prices.get(sym)
    
    async def fetch_news(self, symbol: str) -> List[NewsItem]:
        """Haber verisi (Google News RSS fallback)"""
        try:
            sym = symbol.replace('.IS', '')
            url = f"https://news.google.com/rss/search?q={sym}&hl=tr&gl=TR&ceid=TR:tr"
            async with httpx.AsyncClient() as client:
                resp = await self.fetcher._fetch_with_retry(url, params={})
                # RSS parse (basit)
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.content)
                items = []
                for item in root.findall('.//item')[:10]:
                    title = item.findtext('title', '')
                    source = item.findtext('source', '')
                    date = item.findtext('pubDate', '')
                    link = item.findtext('link', '')
                    desc = item.findtext('description', '')
                    items.append(NewsItem(title=title, source=source, date=date, url=link, summary=desc))
                return items
        except:
            return []
    
    async def fetch_kap(self, symbol: str) -> List[KAPNotification]:
        """KAP bildirimleri - PDF dip notları ile zenginleştirilmiş"""
        try:
            # kap_pdf_parser'dan güvenli PDF tabanlı çekim
            from kap_pdf_parser import fetch_kap_pdf_notes
            pdf_notes = fetch_kap_pdf_notes(symbol, max_docs=10)

            notifications: List[KAPNotification] = []
            for note in pdf_notes:
                # En çok geçen anahtarı disclosure_type olarak ata
                findings = note.get("findings", {})
                if findings:
                    top_type = max(findings, key=findings.get)
                else:
                    top_type = "genel"

                notifications.append(KAPNotification(
                    disclosure_type=top_type,
                    title=note.get("title", ""),
                    date=note.get("date", ""),
                    url=f"https://www.kap.org.tr/tr/Bildirim/{note.get('disclosureId', '')}",
                    summary=f"PDF dip not found ({note.get('text_length', 0)} chars, findings: {findings})"
                ))

            if notifications:
                return notifications[:20]

            # Fallback: pykap dene (eğer kuruluysa)
            from pykap import BISTCompany
            company = BISTCompany(symbol.replace('.IS', ''))
            notifications = []
            for dtype in ['FAR', 'KYUR', 'SUR', 'KDP', 'DEG', 'SYI', 'UNV']:
                try:
                    discs = company.get_disclosures(dtype)
                    for d in discs[:5]:
                        notifications.append(KAPNotification(
                            disclosure_type=dtype,
                            title=d.get('title', ''),
                            date=d.get('publishDate', ''),
                            url=f"https://www.kap.org.tr/tr/Bildirim/{d.get('disclosureIndex')}",
                            summary=d.get('title', '')[:200]
                        ))
                except:
                    pass
            return notifications[:20]
        except Exception as e:
            print(f"[fetch_kap] Hata: {e}")
            return []
    
    async def fetch_peer_financials(self, peer_symbols: List[str]) -> Dict[str, List[PeriodData]]:
        """Rakip şirketlerin finansal verilerini paralel çek - Yahoo Finance API"""
        results = {}
        tasks = []
        for sym in peer_symbols:
            if sym:  # Boş değilse
                tasks.append(self.fetch_yahoo_financials(f"{sym}.IS"))
            else:
                tasks.append(asyncio.sleep(0, result=[]))
        
        peer_data = await asyncio.gather(*tasks, return_exceptions=True)
        
        for sym, data in zip(peer_symbols, peer_data):
            if isinstance(data, Exception):
                print(f"[peer] {sym} hata: {data}")
                results[sym] = []
            else:
                # Fallback: Eğer Yahoo Finance'den veri gelmezse isyatirimhisse dene
                if not data or len(data) == 0:
                    print(f"[peer] {sym} Yahoo'dan veri alınamadı, isyatirimhisse deneniyor...")
                    try:
                        fallback_data = await self.fetch_isfinansal(f"{sym}.IS")
                        results[sym] = fallback_data
                    except:
                        results[sym] = []
                else:
                    results[sym] = data
        
        return results
    
    def compute_peer_comparison(self, target_symbol: str, target_periods: List[PeriodData], 
                                 peer_data: Dict[str, List[PeriodData]]) -> Dict:
        """Rakip karşılaştırma metrikleri hesapla"""
        target_latest = target_periods[0] if target_periods else None
        if not target_latest:
            return {"rows": [], "summary": "Hedef şirket verisi yok", "watch_items": []}
        
        # Metrikler: 5Y ortalamalar için en az 3 yıl sonu lazım
        def get_5y_avg(periods: List[PeriodData], attr: str) -> Optional[float]:
            vals = [getattr(p, attr, None) for p in periods if getattr(p, attr, None) is not None]
            return round(sum(vals) / len(vals), 2) if vals else None
        
        target_favok_5y = get_5y_avg(target_periods, 'favok_margin')
        target_roic_5y = get_5y_avg(target_periods, 'roic')
        target_sales_cagr = self._calc_cagr(target_periods, 'sales')
        target_fcf_ni_5y = get_5y_avg(target_periods, 'fcf_net_income')
        target_net_debt_favok = get_5y_avg(target_periods, 'net_debt_favok')
        target_market_share = None  # Hesaplanması zoru
        
        rows = []
        peer_names = [p for p in peer_data.keys() if p != target_symbol]
        
        # Helper to safely find max/min ignoring None
        def safe_max(d: dict, default="VERI YOK"):
            valid = {k: v for k, v in d.items() if v is not None}
            return max(valid, key=valid.get) if valid else default
        
        def safe_min(d: dict, default="VERI YOK"):
            valid = {k: v for k, v in d.items() if v is not None}
            return min(valid, key=valid.get) if valid else default
        
        # 1. FAVOK Marji (5Y ort)
        peer_favok = {p: get_5y_avg(peer_data[p], 'favok_margin') for p in peer_names}
        peer_favok_vals = [v for v in peer_favok.values() if v is not None]
        sector_median_favok = round(sorted(peer_favok_vals)[len(peer_favok_vals)//2], 2) if peer_favok_vals else None
        winner_favok = safe_max(peer_favok)
        rows.append({
            "metric": "FAVOK Marji (5Y ort)",
            "target": target_favok_5y,
            "peers": peer_favok,
            "sector_median": sector_median_favok,
            "winner": winner_favok
        })
        
        # 2. ROIC (5Y ort)
        peer_roic = {p: get_5y_avg(peer_data[p], 'roic') for p in peer_names}
        peer_roic_vals = [v for v in peer_roic.values() if v is not None]
        sector_median_roic = round(sorted(peer_roic_vals)[len(peer_roic_vals)//2], 2) if peer_roic_vals else None
        winner_roic = safe_max(peer_roic)
        rows.append({
            "metric": "ROIC (5Y ort)",
            "target": target_roic_5y,
            "peers": peer_roic,
            "sector_median": sector_median_roic,
            "winner": winner_roic
        })
        
        # 3. Pazar Payı % (Son yıl satışlara göre)
        target_sales = target_latest.sales or 0
        peer_sales = {p: (peer_data[p][0].sales if peer_data[p] else 0) for p in peer_names}
        total_sales = target_sales + sum(peer_sales.values())
        peer_share = {p: round(v / total_sales * 100, 1) if total_sales > 0 else 0 for p, v in peer_sales.items()}
        target_share = round(target_sales / total_sales * 100, 1) if total_sales > 0 else 0
        winner_share = safe_max({**peer_share, target_symbol: target_share})
        rows.append({
            "metric": "Pazar Payı %",
            "target": target_share,
            "peers": peer_share,
            "sector_median": None,
            "winner": winner_share
        })
        
        # 4. Net Borç/FAVOK (düşük olan kazanır)
        peer_nd_favok = {p: get_5y_avg(peer_data[p], 'net_debt_favok') for p in peer_names}
        peer_nd_vals = [v for v in peer_nd_favok.values() if v is not None]
        sector_median_nd = round(sorted(peer_nd_vals)[len(peer_nd_vals)//2], 2) if peer_nd_vals else None
        winner_nd = safe_min(peer_nd_favok)
        rows.append({
            "metric": "Net Borç/FAVOK",
            "target": target_net_debt_favok,
            "peers": peer_nd_favok,
            "sector_median": sector_median_nd,
            "winner": winner_nd
        })
        
        # 5. Satış CAGR 5Y %
        peer_cagr = {p: self._calc_cagr(peer_data[p], 'sales') for p in peer_names}
        peer_cagr_vals = [v for v in peer_cagr.values() if v is not None]
        sector_median_cagr = round(sorted(peer_cagr_vals)[len(peer_cagr_vals)//2], 2) if peer_cagr_vals else None
        winner_cagr = safe_max(peer_cagr)
        rows.append({
            "metric": "Satış CAGR 5Y %",
            "target": target_sales_cagr,
            "peers": peer_cagr,
            "sector_median": sector_median_cagr,
            "winner": winner_cagr
        })
        
        # 6. FCF/Net Kar %
        peer_fcf_ni = {p: get_5y_avg(peer_data[p], 'fcf_net_income') for p in peer_names}
        peer_fcf_vals = [v for v in peer_fcf_ni.values() if v is not None]
        sector_median_fcf = round(sorted(peer_fcf_vals)[len(peer_fcf_vals)//2], 2) if peer_fcf_vals else None
        winner_fcf = safe_max(peer_fcf_ni)
        rows.append({
            "metric": "FCF/Net Kar %",
            "target": target_fcf_ni_5y,
            "peers": peer_fcf_ni,
            "sector_median": sector_median_fcf,
            "winner": winner_fcf
        })
        
        # Özet
        summary_parts = []
        if target_favok_5y and sector_median_favok:
            if target_favok_5y > sector_median_favok:
                summary_parts.append(f"FAVOK marjı sektör medyanının üzerinde ({target_favok_5y}% vs {sector_median_favok}%)")
            else:
                summary_parts.append(f"FAVOK marjı sektör medyanının altında ({target_favok_5y}% vs {sector_median_favok}%)")
        if target_roic_5y and sector_median_roic:
            if target_roic_5y > sector_median_roic:
                summary_parts.append(f"ROIC sektörden üstünde ({target_roic_5y}% vs {sector_median_roic}%)")
            else:
                summary_parts.append(f"ROIC sektörden altında ({target_roic_5y}% vs {sector_median_roic}%)")
        
        return {
            "rows": rows,
            "summary": " | ".join(summary_parts) if summary_parts else "Karşılaştırma verisi yetersiz",
            "watch_items": [f"{r['metric']}: {r['winner']} önde" for r in rows if r['winner'] != "VERI YOK"],
            "peer_names": peer_names,
            "target_symbol": target_symbol
        }
    
    def _calc_cagr(self, periods: List[PeriodData], attr: str) -> Optional[float]:
        """5 yıl CAGR hesapla (en eski ve en yeni yıl sonu)"""
        year_ends = [p for p in periods if p.period.endswith('/12') or p.period.endswith('/6')]
        if len(year_ends) < 2:
            return None
        year_ends.sort(key=lambda p: datetime.strptime(p.period, "%Y/%m"))
        first = getattr(year_ends[0], attr, None)
        last = getattr(year_ends[-1], attr, None)
        if first and first > 0 and last and last > 0:
            years = (datetime.strptime(year_ends[-1].period, "%Y/%m") - datetime.strptime(year_ends[0].period, "%Y/%m")).days / 365.25
            if years > 0:
                return round(((last / first) ** (1/years) - 1) * 100, 2)
        return None
    
    async def fetch_market_cap(self, symbol: str) -> Dict:
        """Piyasa değeri hesapla (yfinance + fallback)"""
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                shares = info.get('sharesOutstanding') or info.get('impliedSharesOutstanding')
                price = info.get('currentPrice') or info.get('regularMarketPrice')
                
                if shares and price:
                    market_cap_mn = round(shares * price / 1_000_000, 1)
                    return {"market_cap_mn": market_cap_mn, "price": price, "shares": shares}
            except:
                pass
        
        # Fallback: KAP'tan son fiyat / İş Yatırım
        # Basit fallback: technical data'dan price al
        tech = await self.fetch_price_technical(symbol)
        if tech and tech.price and tech.price > 0:
            # Hisse adedi tahmini (genellikle KAP'ta var)
            # SDTTR: ~250Mn, ASELS: ~5.5Bn, TUPRS: ~2.5Bn
            shares_map = {
                'SDTTR': 250.4,
                'ASELS': 5500,
                'TUPRS': 2500,
                'THYAO': 1380,
                'EREGL': 3900,
                'SISE': 3000,
            }
            sym = symbol.replace('.IS', '')
            shares = shares_map.get(sym, 1000) * 1_000_000
            market_cap_mn = round(shares * tech.price / 1_000_000, 1)
            return {"market_cap_mn": market_cap_mn, "price": tech.price, "shares": shares / 1_000_000}
        
        return {"market_cap_mn": 0, "price": 0, "shares": 0}
    
    def compute_valuation_multiples(self, symbol: str, periods: List[PeriodData], market_cap_data: Dict, net_debt_mn: float = 0) -> Dict:
        """5Y ortalama değerleme çarpanları ve fair value hesapla"""
        try:
            # Yıl sonu dönemleri al (en fazla 5)
            year_ends = [p for p in periods if p.period.endswith('/12') or p.period.endswith('/6')]
            year_ends.sort(key=lambda p: datetime.strptime(p.period, "%Y/%m"), reverse=True)
            year_ends = year_ends[:5]
            
            if not year_ends:
                return self._empty_valuation()
            
            latest = year_ends[0]
            price = market_cap_data.get('price', 0)
            market_cap = market_cap_data.get('market_cap_mn', 0)
            shares = market_cap_data.get('shares', 0)
            
            if price <= 0 or market_cap <= 0 or shares <= 0:
                return self._empty_valuation()
            
            # Net nakit = nakit - net borç
            cash = latest.cash or 0
            net_cash = cash - net_debt_mn
            enterprise_value = market_cap + net_debt_mn - cash
            
            # 5Y ortalama çarpanları hesapla
            pe_ratios = []
            ev_favok_ratios = []
            ev_sales_ratios = []
            pb_ratios = []
            pfcf_ratios = []
            
            for p in year_ends:
                # P/E = Market Cap / Net Income
                if p.net_income and p.net_income > 0:
                    pe_ratios.append(market_cap / p.net_income)
                
                # EV/FAVOK
                if p.favok and p.favok > 0:
                    ev_favok_ratios.append(enterprise_value / p.favok)
                
                # EV/Sales
                if p.sales and p.sales > 0:
                    ev_sales_ratios.append(enterprise_value / p.sales)
                
                # P/B = Market Cap / Equity
                if p.equity and p.equity > 0:
                    pb_ratios.append(market_cap / p.equity)
                
                # P/FCF
                if p.fcf and p.fcf > 0:
                    pfcf_ratios.append(market_cap / p.fcf)
            
            def avg(vals):
                return round(sum(vals) / len(vals), 1) if vals else None
            
            pe_5y = avg(pe_ratios)
            ev_favok_5y = avg(ev_favok_ratios)
            ev_sales_5y = avg(ev_sales_ratios)
            pb_5y = avg(pb_ratios)
            pfcf_5y = avg(pfcf_ratios)
            
            # Güncel çarpanlar
            current_pe = round(market_cap / latest.net_income, 1) if latest.net_income and latest.net_income > 0 else None
            current_ev_favok = round(enterprise_value / latest.favok, 1) if latest.favok and latest.favok > 0 else None
            current_ev_sales = round(enterprise_value / latest.sales, 1) if latest.sales and latest.sales > 0 else None
            current_pb = round(market_cap / latest.equity, 1) if latest.equity and latest.equity > 0 else None
            current_pfcf = round(market_cap / latest.fcf, 1) if latest.fcf and latest.fcf > 0 else None
            
            # Fair Value hesaplamaları
            rows = []
            if pe_5y and latest.net_income and latest.net_income > 0:
                fair_pe = round(pe_5y * latest.net_income / shares * 1_000_000, 2)
                rows.append({
                    "method": "P/E",
                    "five_year_avg_multiple": pe_5y,
                    "current_multiple": current_pe,
                    "fair_value_tl": fair_pe,
                    "safety_margin_pct": round((fair_pe - price) / price * 100, 1) if price > 0 else None
                })
            
            if ev_favok_5y and latest.favok and latest.favok > 0:
                fair_ev = round((ev_favok_5y * latest.favok - net_debt_mn + cash) / shares * 1_000_000, 2)
                rows.append({
                    "method": "EV/FAVOK",
                    "five_year_avg_multiple": ev_favok_5y,
                    "current_multiple": current_ev_favok,
                    "fair_value_tl": fair_ev,
                    "safety_margin_pct": round((fair_ev - price) / price * 100, 1) if price > 0 else None
                })
            
            if ev_sales_5y and latest.sales and latest.sales > 0:
                fair_evs = round((ev_sales_5y * latest.sales - net_debt_mn + cash) / shares * 1_000_000, 2)
                rows.append({
                    "method": "EV/Sales",
                    "five_year_avg_multiple": ev_sales_5y,
                    "current_multiple": current_ev_sales,
                    "fair_value_tl": fair_evs,
                    "safety_margin_pct": round((fair_evs - price) / price * 100, 1) if price > 0 else None
                })
            
            if pb_5y and latest.equity and latest.equity > 0:
                fair_pb = round(pb_5y * latest.equity / shares * 1_000_000, 2)
                rows.append({
                    "method": "P/B",
                    "five_year_avg_multiple": pb_5y,
                    "current_multiple": current_pb,
                    "fair_value_tl": fair_pb,
                    "safety_margin_pct": round((fair_pb - price) / price * 100, 1) if price > 0 else None
                })
            
            if pfcf_5y and latest.fcf and latest.fcf > 0:
                fair_pfcf = round(pfcf_5y * latest.fcf / shares * 1_000_000, 2)
                rows.append({
                    "method": "P/FCF",
                    "five_year_avg_multiple": pfcf_5y,
                    "current_multiple": current_pfcf,
                    "fair_value_tl": fair_pfcf,
                    "safety_margin_pct": round((fair_pfcf - price) / price * 100, 1) if price > 0 else None
                })
            
            # Fair value aralığı
            fair_values = [r["fair_value_tl"] for r in rows if r["fair_value_tl"] is not None]
            if fair_values:
                fair_min = round(min(fair_values), 2)
                fair_max = round(max(fair_values), 2)
                fair_range = f"{fair_min} - {fair_max} TL"
            else:
                fair_range = "VERI YOK"
            
            # Güncel fiyat ve indirim
            discount_pct = 0
            if price > 0 and fair_values:
                avg_fair = sum(fair_values) / len(fair_values)
                discount_pct = round((avg_fair - price) / price * 100, 1)
            
            # Moat etkisi (basit)
            moat_impact = "Hendek GENIŞ -> Çarpan üstünde" if fair_values and avg_fair > price else "Hendek DAR -> Çarpan altında"
            
            return {
                "market_cap_mn": market_cap,
                "net_cash_mn": round(net_cash, 1),
                "enterprise_value_mn": round(enterprise_value, 1),
                "rows": rows,
                "fair_value_range": fair_range,
                "current_price": price,
                "discount_pct": discount_pct,
                "moat_impact": moat_impact,
                "current_multiples": {
                    "pe": current_pe,
                    "ev_favok": current_ev_favok,
                    "ev_sales": current_ev_sales,
                    "pb": current_pb,
                    "pfcf": current_pfcf
                },
                "five_year_avg_multiples": {
                    "pe": pe_5y,
                    "ev_favok": ev_favok_5y,
                    "ev_sales": ev_sales_5y,
                    "pb": pb_5y,
                    "pfcf": pfcf_5y
                }
            }
            
        except Exception as e:
            print(f"[valuation] Error: {e}")
            return self._empty_valuation()
    
    def _empty_valuation(self) -> Dict:
        return {
            "market_cap_mn": 0,
            "net_cash_mn": 0,
            "enterprise_value_mn": 0,
            "rows": [],
            "fair_value_range": "VERI YOK",
            "current_price": 0,
            "discount_pct": 0,
            "moat_impact": "VERI YOK",
            "current_multiples": {},
            "five_year_avg_multiples": {}
        }
    
    async def fetch_all(self, symbol: str) -> CompleteData:
        """Tüm verileri paralel çek - Yahoo Finance ana kaynak"""
        symbol_clean = symbol.replace('.IS', '')
        
        # Paralel çekim - ana veriler (Yahoo Finance PRIORITY)
        tasks = [
            self.fetch_price_technical(symbol),
            self.fetch_yahoo_financials(symbol),  # Yahoo Finance API (ana kaynak)
            self.fetch_news(symbol),
            self.fetch_kap(symbol),
        ]
        
        technical, periods, news, kap = await asyncio.gather(*tasks)
        
        # Fallback: Eğer Yahoo Finance'den veri gelmezse isyatirimhisse dene
        if not periods or len(periods) == 0:
            print(f"[fetch_all] Yahoo Finance'den veri alınamadı, isyatirimhisse deneniyor...")
            periods = await self.fetch_isfinansal(symbol)
        
        # FinancialData oluştur
        financial = FinancialData(symbol=symbol, periods=periods)
        
        # Sektör peerleri (otomatik tespit)
        sector_peers = get_sector_peers(symbol)
        
        # Rakip finansal verilerini çek (arka planda, hata vermez)
        peer_financials = {}
        try:
            peer_symbols = [p for p in sector_peers if p.replace('.IS', '') != symbol_clean]
            if peer_symbols:
                peer_financials = await self.fetch_peer_financials(peer_symbols)
                # Sadece veri olan peer'ları tut
                peer_financials = {k: v for k, v in peer_financials.items() if v and len(v) > 0}
        except Exception as e:
            print(f"[peer fetch] Hata: {e}")
            peer_financials = {}
        
        # Piyasa değeri
        market_cap_data = {}
        try:
            market_cap_data = await self.fetch_market_cap(symbol)
        except Exception as e:
            print(f"[market cap] Hata: {e}")
        
        # Değerleme çarpanları (net borç hesapla)
        net_debt_mn = 0
        if periods:
            latest = periods[0]
            net_debt_mn = (latest.short_debt or 0) + (latest.long_debt or 0) - (latest.cash or 0)
        
        valuation_data = {}
        try:
            valuation_data = self.compute_valuation_multiples(symbol, financial.get_year_ends(), market_cap_data, net_debt_mn)
        except Exception as e:
            print(f"[valuation] Hata: {e}")
            valuation_data = self._empty_valuation()
        
        # Metadata'ya ekle
        financial.metadata = {
            "peer_financials": {k: [p.model_dump() for p in v] for k, v in peer_financials.items()},
            "market_cap": market_cap_data,
            "peer_comparison": self.compute_peer_comparison(symbol_clean, financial.get_year_ends(), peer_financials) if peer_financials else {},
            "valuation": valuation_data
        }
        
        return CompleteData(
            symbol=symbol,
            financial=financial,
            technical=technical,
            news=news,
            kap_notifications=kap,
            sector_peers=SECTOR_PEERS.get(symbol.replace('.IS', ''), [symbol]),
            sector_name=self._get_sector_name(symbol),
            fetched_at=datetime.now().isoformat()
        )
    
    def _get_sector_name(self, symbol: str) -> str:
        sector_map = {
            'TUPRS': 'Rafineri/Petrol',
            'THYAO': 'Havacılık',
            'ASELS': 'Savunma/Havacılık',
            'EREGL': 'Demir Çelik',
            'SISE': 'Cam/Çimento',
            'ASELS': 'Savunma/Havacılık',
            'TURKSAT': 'Uydu/Havacılık',
            'HAVELSAN': 'Savunma/Yazılım',
            'TAI': 'Havacılık',
            'TURKNET': 'Telekom',
            'SDTTR': 'Savunma/Uzay',
            'SISE': 'Cam/Çimento',
            'KCHOL': 'Holding',
            'ECILC': 'Cam/Çimento',
            'EREGL': 'Demir Çelik',
            'ISDMR': 'Demir Çelik',
            'KRDMD': 'Demir Çelik',
            'OTOKAR': 'Savunma/Kara',
            'PNKRT': 'Savunma',
            'TAI': 'Havacılık',
            'TURKSAT': 'Uydu/İletişim',
            'TURKNET': 'Telekom/İnternet',
            'HAVELSAN': 'Savunma/Yazılım',
        }
        return sector_map.get(symbol.replace('.IS', ''), 'Diğer')


# ============================================================
# SEKTÖR PEER MAPPING
# ============================================================

# ============================================================
# SEKTÖR PEER MAPPING (temel liste, otomatik genişletilir)
# ============================================================

SECTOR_PEERS = {
    'TUPRS': ['TUPRS', 'PETKM', 'SASA', 'AKSA', 'ISCTR'],
    'THYAO': ['THYAO', 'PGSUS', 'ARCLK', 'ISCTR', 'AKSA'],
    'SISE': ['SISE', 'KCHOL', 'ECILC', 'TUPRS', 'ASELS'],
    'EREGL': ['EREGL', 'ISDMR', 'KRDMD', 'TUPRS', 'PETKM'],
    'ASELS': ['ASELS', 'OTOKAR', 'PNKRT', 'HAVELSAN', 'TURKSAT'],
    'AKBNK': ['AKBNK', 'GARAN', 'ISCTR', 'YKBNK', 'VAKBN'],
    'SDTTR': ['SDTTR', 'ASELS', 'HAVELSAN', 'TURKSAT', 'TURKNET'],
}

# Sektör önbelleği: {symbol_clean: sektor_adi}
SECTOR_CACHE: Dict[str, str] = {}


def fetch_sector_from_yahoo(symbol: str) -> str:
    """Yahoo Finance'tan hissenin sektörünü çeker. Bulamazsa 'BILINMIYOR' döner."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        sector = info.get('sector') or info.get('industry') or 'BILINMIYOR'
        return sector
    except Exception:
        return 'BILINMIYOR'


def get_sector_peers(symbol: str) -> list:
    """
    Belirli bir hisse için sektöründeki peerleri döner.
    1. SECTOR_PEERS'de varsa oradan al
    2. Yoksa Yahoo'dan sektörü çek, SECTOR_CACHE'e kaydet
    3. Sektöre ait tüm BIST hisselerinden en fazla 5 tanesi döner
    """
    symbol_clean = symbol.replace('.IS', '')

    # 1. Manuel map'te varsa direkt döndür (SECTOR_PEERS zaten .IS'siz)
    if symbol_clean in SECTOR_PEERS:
        peers = SECTOR_PEERS[symbol_clean]
        return peers  # .IS EKLEME - zaten temiz

    # 2. Sektör cache'de yoksa çek
    if symbol_clean not in SECTOR_CACHE:
        SECTOR_CACHE[symbol_clean] = fetch_sector_from_yahoo(symbol)

    sector = SECTOR_CACHE[symbol_clean]
    print(f"[SEKTOR] {symbol_clean} sektörü: {sector}")

    # 3. Aynı sektördeki bilinen hisseleri bul (basit eşleşme)
    # SECTOR_PEERS'deki tüm hisselerden aynı sektöre ait olanları topla
    all_known_peers = set()
    for peer_list in SECTOR_PEERS.values():
        for p in peer_list:
            all_known_peers.add(p)  # zaten .IS'siz

    # Sektöre özel peer listesi yoksa, bilinen hisselerden en fazla 5 tanesi döndür
    # (Gerçek sektör bazlı filtreleme için KAP/Yahoo sektör verisi gerekir)
    result = [p for p in all_known_peers if p != symbol_clean][:5]
    return result


# ============================================================
# MAIN ENTRY POINT
# ============================================================

class DataLayer:
    """Ana veri katmanı - tek giriş noktası"""
    
    def __init__(self):
        self.settings = Settings()
        self.fetcher = DataFetcher()
        self.provider = FinancialDataProvider(self.fetcher)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.fetcher.close()
    
    async def fetch_complete(self, symbol: str) -> CompleteData:
        """Tüm verileri çek ve normalize et"""
        return await self.provider.fetch_all(symbol)
    
    async def close(self):
        await self.fetcher.close()


# ============================================================
# SYNC WRAPPER (eski kod uyumluluğu)
# ============================================================

def fetch_complete_sync(symbol: str) -> CompleteData:
    """Sync wrapper"""
    async def _run():
        async with DataLayer() as dl:
            return await dl.fetch_complete(symbol)
    
    return asyncio.run(_run())


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "SDTTR.IS"
    
    print(f"Fetching data for {symbol}...")
    data = fetch_complete_sync(symbol)
    
    print(f"\n=== {data.symbol} ===")
    print(f"Sektör: {data.sector_name}")
    print(f"Peerler: {data.sector_peers}")
    print(f"\nFiyat: {data.technical.price} TL")
    print(f"Trend: {data.technical.trend}")
    print(f"RSI: {data.technical.rsi}")
    print(f"Trend: {data.technical.trend}")
    
    print(f"\n=== Finansal Veriler ({len(data.financial.periods)} dönem) ===")
    for p in data.financial.periods_sorted[:5]:
        print(f"  {p.period}: Satış={p.sales:.1f}M, FAVOK={p.favok:.1f}M, NetKar={p.net_income:.1f}M, "
              f"FavokM={p.favok_margin}%, NetMarj={p.net_margin}%, NetBorc/Favok={p.net_debt_favok}, "
              f"Cari={p.current_ratio}, ROIC={p.roic_pct}%")
    
    print(f"\nTeknik: Trend={data.technical.trend}, RSI={data.technical.rsi}, Destek={data.technical.support}, Direnç={data.technical.resistance}")
    print(f"Haber: {len(data.news)} adet")
    print(f"KAP: {len(data.kap_notifications)} adet")
    print(f"Peerler: {data.sector_peers}")