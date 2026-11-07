"""
Structured Output Models - Agent'lar için JSON Schema / Pydantic modelleri
Agent'lar SADECE bu modelleri doldurur, monolog YOK.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class TrendDirection(str, Enum):
    YUKARI = "YUKARI"
    ASAGI = "ASAGI"
    YATAY = "YATAY"
    DALGALI = "DALGALI"


class SignalType(str, Enum):
    AL = "AL"
    SAT = "SAT"
    BEKLE = "BEKLE"
    NORMAL = "NORMAL"
    ASIRI_ALIM = "ASIRI_ALIM"
    ASIRI_SATIM = "ASIRI_SATIM"


class TrendDirectionEnum(str, Enum):
    ARTIS = "ARTIS"
    AZALIS = "AZALIS"
    DALGALI = "DALGALI"
    STABIL = "STABIL"


class RiskLevel(str, Enum):
    DUSUK = "DUSUK"
    ORTA = "ORTA"
    YUKSEK = "YUKSEK"
    KRITIK = "KRITIK"


class Verdict(str, Enum):
    GUCLU = "GUCLU"
    IZLE = "IZLE"
    RISKLI = "RISKLI"


# ============================================================
# TEMEL ANALIZ MODELLERİ
# ============================================================

class PeriodMetrics(BaseModel):
    """Tek dönem metrikleri"""
    period: str
    sales_mn_tl: Optional[float] = None
    favok_margin_pct: Optional[float] = None
    net_income_mn_tl: Optional[float] = None
    net_debt_favok: Optional[float] = None
    current_ratio: Optional[float] = None
    fcf_net_income_pct: Optional[float] = None
    roic_pct: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    fcf_mn_tl: Optional[float] = None
    equity_mn_tl: Optional[float] = None
    net_debt_mn_tl: Optional[float] = None
    cash_mn_tl: Optional[float] = None
    trend: Optional[str] = None  # "ARTIS", "AZALIS", "DALGALI", "STABIL"


class FundamentalTable(BaseModel):
    """5 dönemlik temel analiz tablosu"""
    periods: List[dict] = Field(default_factory=list)  # Her period dict: {period, sales, favok_margin, net_income, net_debt_favok, current_ratio, fcf_net_income, roic, gross_margin, net_margin, fcf, equity, net_debt, cash, trend}
    piotroski: dict = Field(default_factory=dict)  # {"score": 7, "details": {...}}
    cash_profit_alignment: dict = Field(default_factory=dict)  # {"verdict": "Evet", "detail": "FCF/NetKar %100, trend: Yüksek"}
    
    class Config:
        json_schema_extra = {
            "example": {
                "periods": [
                    {"period": "2026/6", "sales": 1174.1, "favok_margin": 16.17, "net_income": 23.4, "net_debt_favok": 3.64, "current_ratio": 3.51, "fcf_net_income": -1702, "roic": 6.59, "gross_margin": 30.9, "net_margin": 2.14, "fcf": -427.3, "equity": 2881.4, "net_debt": 691.8, "cash": 134.1, "trend": "VOLATILE"},
                    {"period": "2025/12", "sales": 2543.4, "favok_margin": 11.3, "net_income": 35.6, "net_debt_favok": 0.58, "current_ratio": 4.35, "fcf_net_income": -900.7, "roic": 11.3, "gross_margin": 25.2, "net_margin": 1.4, "fcf": -321.4, "equity": 2869.7, "net_debt": 166.6, "cash": 422.4, "trend": "IMPROVING"},
                ],
                "piotroski": {"score": 7, "details": {"net_income_pos": 1, "cfo_positive": 1, "roa_improving": 0, "cfo_gt_ni": 1, "debt_decreasing": 0, "current_ratio_improving": 1, "no_dilution": 0, "gross_margin_improving": 0, "asset_turnover_improving": 1}},
                "cash_profit_alignment": {"verdict": "Hayir", "detail": "FCF negatif (-427M), Net Kar pozitif (23M)"}
            }
        }
        
# ============================================================
# HENDEK (MOAT) MODELLERİ
# ============================================================

class MoatComponent(BaseModel):
    component: str
    score: int = Field(ge=0, le=100)
    evidence: str

class MoatAnalysis(BaseModel):
    """Hendek (Moat) Analizi"""
    components: List[MoatComponent] = Field(min_items=5, max_items=5)
    total_score: int = Field(ge=0, le=100)
    classification: Literal["GENIS", "DAR", "YOK"]
    differentiation: str
    risks: List[str] = Field(default_factory=list)
    
    @property
    def total(self) -> int:
        return sum(c.score for c in self.components) // len(self.components) if self.components else 0


# ============================================================
# HİKAYE VE SEKTÖR MODELLERİ
# ============================================================

class InvestmentProject(BaseModel):
    name: str
    timeline: str
    capex: str
    roic_target: str
    description: str

class Catalyst(BaseModel):
    name: str
    impact: Literal["Pozitif", "Negatif", "Notr"]
    timeline: str
    description: str

class StorySector(BaseModel):
    sector_name: str
    sector_outlook: str
    investment_map: List[InvestmentProject] = []
    catalysts: List[Catalyst] = []


# ============================================================
# RAKİP AYRIŞMA MODELLERİ
# ============================================================

class PeerComparisonRow(BaseModel):
    metric: str
    target: Optional[float] = None
    peers: Dict[str, Optional[float]] = {}
    sector_median: Optional[float] = None
    winner: str

class PeerComparison(BaseModel):
    """Rakip Ayrışma Tablosu"""
    rows: List[PeerComparisonRow]
    summary: str
    watch_items: List[str] = []


# ============================================================
# RİSK VE DUYARLILIK MODELLERİ
# ============================================================

class SensitivityRow(BaseModel):
    risk_factor: str
    shock: str
    favok_impact: str
    net_debt_favok_impact: str
    note: str

class BreakingPoint(BaseModel):
    metric: str
    current: str
    red_line: str
    distance: str
    consequence: str

class RiskAnalysis(BaseModel):
    """Risk ve Duyarlılık Analizi"""
    sensitivities: List[SensitivityRow]
    breaking_points: List[BreakingPoint]
    overall_risk: Literal["DUSUK", "ORTA", "YUKSEK", "KRITIK"]
    key_risks: List[str] = []


# ============================================================
# DEĞERLEME MODELLERİ
# ============================================================

class ValuationRow(BaseModel):
    method: str
    five_year_avg_multiple: Optional[float] = None
    current_multiple: Optional[float] = None
    fair_value_tl: Optional[float] = None
    safety_margin_pct: Optional[float] = None

class ValuationAnalysis(BaseModel):
    """Değerleme Analizi"""
    current_price: float
    market_cap_mn: float
    net_cash_mn: float
    enterprise_value_mn: float
    rows: List[ValuationRow]
    fair_value_range: str
    current_price: float
    discount_pct: float
    moat_impact: str
    dcf_note: str = ""


# ============================================================
# TEKNİK ANALİZ MODELLERİ
# ============================================================

class TechnicalPosition(BaseModel):
    """Teknik Pozisyon"""
    trend: Literal["YUKARI", "ASAGI", "YATAY"]
    rsi: float
    rsi_signal: Literal["ASIRI_ALIM", "ASIRI_SATIM", "NORMAL"]
    macd: float
    macd_signal: Literal["AL", "SAT", "BEKLE"]
    adx: float
    adx_strength: Literal["ZAYIF", "ORTA", "GUCLU", "COK_GUCLU"]
    volume_avg_20: Optional[float] = None
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma200: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    adx: Optional[float] = None
    atr: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_middle: Optional[float] = None
    trend: Literal["YUKARI", "ASAGI", "YATAY"]
    support: float
    resistance: float
    stop_loss: float
    target: float
    risk_reward: str
    macd_signal_val: Optional[float] = None


# ============================================================
# RİSK ANALİZİ MODELLERİ
# ============================================================

class SensitivityItem(BaseModel):
    risk_factor: str
    shock: str
    favok_impact: str
    net_debt_favok_impact: str
    note: str

class BreakingPointItem(BaseModel):
    metric: str
    current: str
    red_line: str
    distance: str
    consequence: str

class RiskAnalysis(BaseModel):
    sensitivities: List[dict] = []
    breaking_points: List[dict] = []
    overall_risk: Literal["DUSUK", "ORTA", "YUKSEK", "KRITIK"]
    key_risks: List[str] = []


# ============================================================
# DEĞERLEME MODELLERİ
# ============================================================

class ValuationRow(BaseModel):
    method: str
    five_year_avg_multiple: Optional[float] = None
    current_multiple: Optional[float] = None
    fair_value_tl: Optional[float] = None
    safety_margin_pct: Optional[float] = None

class ValuationAnalysis(BaseModel):
    current_price: float
    market_cap_mn: float
    net_cash_mn: float
    enterprise_value_mn: float
    rows: List[dict] = []
    fair_value_range: str
    current_price: float
    discount_pct: float
    moat_impact: str
    dcf_note: str = ""


# ============================================================
# TEKNİK POZİSYON MODELLERİ
# ============================================================

class TechnicalPosition(BaseModel):
    trend: Literal["YUKARI", "ASAGI", "YATAY"]
    rsi: float
    rsi_signal: Literal["ASIRI_ALIM", "ASIRI_SATIM", "NORMAL"]
    macd: float
    macd_signal: Literal["AL", "SAT", "BEKLE"]
    adx: float
    adx_strength: Literal["ZAYIF", "ORTA", "GUCLU", "COK_GUCLU"]
    volume_avg_20: Optional[float] = None
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma200: Optional[float] = None
    macd: Optional[float] = None
    macd_signal_val: Optional[float] = None
    adx: Optional[float] = None
    atr: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_middle: Optional[float] = None
    trend: Literal["YUKARI", "ASAGI", "YATAY"]
    support: float
    resistance: float
    stop_loss: float
    target: float
    risk_reward: str
    macd_signal_val: Optional[float] = None


# ============================================================
# DELTA (DEĞİŞİM) ANALİZİ
# ============================================================

class DeltaRow(BaseModel):
    metric: str
    values: List[dict]  # [{"period": "2026/6", "value": 16.17}, ...]
    trend: str

class DeltaAnalysis(BaseModel):
    rows: List[dict] = []  # [{"metric": "FAVOK Marji %", "values": [{"period": "2026/6", "value": 16.17}, ...], "trend": "IYILESME"}]


# ============================================================
# KAP DİP NOTLARI
# ============================================================

class KAPNote(BaseModel):
    type: str
    date: str
    summary: str
    url: str

class KAPNotes(BaseModel):
    notes: List[dict] = []


# ============================================================
# DELTA ANALİZİ
# ============================================================

class DeltaAnalysis(BaseModel):
    rows: List[dict] = []


# ============================================================
# KAP DİP NOTLARI
# ============================================================

class KAPNote(BaseModel):
    type: str
    date: str
    summary: str
    url: str


# ============================================================
# MASTER ANALİZ ÇIKTISI
# ============================================================

class CompleteAnalysis(BaseModel):
    """Tüm analiz çıktısının birleşimi"""
    symbol: str
    date: str
    verdict: Literal["GUCLU", "IZLE", "RISKLI"]
    verdict_emoji: str
    rationale: List[str]
    
    moat: MoatAnalysis
    story_sector: StorySector
    fundamental: FundamentalTable
    peer_comparison: PeerComparison
    risk: RiskAnalysis
    valuation: ValuationAnalysis
    technical: TechnicalPosition
    kap_notes: List[dict] = []
    delta: DeltaAnalysis
    technical_position: Optional[dict] = None
    disclaimer: str = "Bu analiz bilgi amaçlıdır; yatırım tavsiyesi değildir."


# ============================================================
# AGENT OUTPUT WRAPPERS
# ============================================================

class AgentOutput(BaseModel):
    """Her ajan için standart çıktı wrapper'ı"""
    agent_name: str
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: int = 0


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Enums
    "TrendDirection",
    "SignalType",
    "RiskLevel",
    "Verdict",
    
    # Core Models
    "PeriodMetrics",
    "FundamentalTable",
    "MoatAnalysis",
    "MoatComponent",
    "StorySector",
    "InvestmentProject",
    "Catalyst",
    "PeerComparison",
    "PeerComparisonRow",
    "RiskAnalysis",
    "SensitivityItem",
    "BreakingPointItem",
    "ValuationAnalysis",
    "ValuationRow",
    "TechnicalPosition",
    "TechnicalPosition",
    "DeltaAnalysis",
    "KAPNotes",
    "KAPNote",
    "CompleteAnalysis",
    "AgentOutput",
    
    # Enums
    "TrendDirection",
    "SignalType",
    "RiskLevel",
    "Verdict",
    "TrendDirectionEnum",
    "RiskLevel",
]

if __name__ == "__main__":
    # Test JSON schema generation
    import json
    print(json.dumps(FundamentalTable.model_json_schema(), indent=2, ensure_ascii=False))