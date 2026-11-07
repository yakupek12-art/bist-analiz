#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parallel Agent Runner - 7 ajan asyncio.gather ile paralelleştirilmiş
Structured Output (pydantic) zorunlu - monolog YOK
"""

import asyncio
import json
import os
import sys
import re
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nvidia_client import call_nvidia
from structured_output import (
    MoatAnalysis, StorySector, FundamentalTable, PeerComparison,
    RiskAnalysis, ValuationAnalysis, TechnicalPosition,
    DeltaAnalysis, KAPNote, CompleteAnalysis,
    MoatComponent, InvestmentProject, Catalyst,
    PeerComparisonRow, SensitivityRow, BreakingPoint,
    ValuationRow, TechnicalPosition, KAPNote
)
from data_layer import DataLayer, CompleteData, SECTOR_PEERS


@dataclass
class AgentResult:
    """Agent çalışma sonucu"""
    name: str
    success: bool
    data: Any = None
    error: str = ""
    execution_time_ms: int = 0


class ParallelAgentRunner:
    """7 ajanı paralelleştirilmiş çalıştırıcı"""

    def __init__(self, veri_cache: dict):
        self.veri_cache = veri_cache
        self.results = {}

    def _build_user_prompt(self, template: str) -> str:
        return template.format(**{k: str(v) for k, v in self.data.items()})

    def set_data(self, data: dict):
        self.data = data

    def _get_veri_cache(self) -> dict:
        return {
            'finansal': self.veri_cache.get('finansal', ''),
            'sektor_rakip': self.veri_cache.get('sektor_rakip', ''),
            'kap_dipnotlar': self.veri_cache.get('kap_dipnotlar', ''),
            'haberler': self.veri_cache.get('haberler', ''),
            'fiyat_teknik': self.veri_cache.get('fiyat_teknik', ''),
        }

    async def run_agent(self, layer_name: str, system_prompt: str, user_template: str, output_model: type = None) -> dict:
        """Tek ajanı çalıştır - Structured Output ile"""
        import time, json, re
        start = time.time()

        try:
            # Tek seferde formatla
            user_prompt = user_template.format(**self._get_veri_cache())

            # JSON Schema prompt'u ekle (Pydantic modelden)
            schema_prompt = ""
            if output_model:
                schema_prompt = f"\n\nCIKTI FORMATI (JSON Schema):\n{json.dumps(output_model.model_json_schema(), indent=2, ensure_ascii=False)}\n\nSADECE BU FORMATTA GEÇERLİ JSON ÜRET."

            enhanced_system = system_prompt + schema_prompt + "\n\nKURAL: SADECE GEÇERLİ JSON OBJESİ. HİÇBİR METİN, AÇIKLAMA, DÜŞÜNCE, MARKDOWN KOD BLOĞU YOK."

            # Use already imported call_nvidia from nvidia_client
            raw_output = await call_nvidia(enhanced_system, user_prompt)

            # GÜVENLİK: call_nvidia None döndürürse (timeout/retry sonrası implicit return)
            if raw_output is None:
                raw_output = "API_ERROR: call_nvidia returned None (timeout/retry exhausted)"

            # NVIDIA/API hata ön ekleri kontrolü - bunlar JSON değil, doğrudan hata döndür
            if isinstance(raw_output, str):
                error_prefixes = ("RATE_LIMIT", "API HATA", "TIMEOUT_ERROR", "CONNECTION_ERROR", "UNEXPECTED_ERROR", "MAX_RETRIES")
                if raw_output.startswith(error_prefixes):
                    return {
                        "success": False,
                        "data": None,
                        "error": raw_output,
                        "execution_time_ms": int((time.time() - start) * 1000)
                    }

            # Parse JSON
            raw = str(raw_output).strip()
            if not raw:
                raise ValueError("API returned empty response")

            # Markdown kod bloklarını güvenli şekilde temizle (IndexError riski yok)
            if raw.startswith('```json'):
                parts = raw.split('```json', 1)
                if len(parts) > 1:
                    raw = parts[1].rsplit('```', 1)[0]
            elif raw.startswith('```'):
                parts = raw.split('```', 1)
                if len(parts) > 1:
                    raw = parts[1].rsplit('```', 1)[0]

            raw = raw.strip()

            # İlk { ve son } arası JSON'u çıkar
            start_idx = raw.find('{')
            end_idx = raw.rfind('}')
            if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
                raise ValueError(f"No valid JSON object found in response. Preview: {raw[:200]}")

            json_str = raw[start_idx:end_idx + 1]
            parsed = json.loads(json_str)

            return {
                "success": True,
                "data": parsed,
                "error": None,
                "execution_time_ms": int((time.time() - start) * 1000)
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"JSON Parse Hatası: {str(e)}",
                "execution_time_ms": int((time.time() - start) * 1000)
            }

    async def run_all_parallel(self) -> Dict[str, dict]:
        """7 ajanı paralelleştir"""
        print(f"\n{'='*50}")
        print("7 AJAN PARALEL CALISIYOR")
        print(f"{'='*50}")

        from structured_output import (
            MoatAnalysis, StorySector, FundamentalTable, PeerComparison,
            RiskAnalysis, ValuationAnalysis, TechnicalPosition
        )

        OUTPUT_MODELS = {
            'sektor-ajani': None,
            'hendek-ajani': MoatAnalysis,
            'hikaye-ajani': StorySector,
            'temel-ajani': FundamentalTable,
            'rakip-ajani': PeerComparison,
            'yonetim-ajani': None,
            'sektor-karsilastirma-ajani': None,
            'risk-ajani': RiskAnalysis,
            'degerleme-ajani': ValuationAnalysis,
            'teknik-ajani': TechnicalPosition,
        }

        tasks = []
        for layer_name in LAYER_ORDER:
            config = AGENT_CONFIGS[layer_name]
            output_model = OUTPUT_MODELS.get(layer_name)
            task = asyncio.create_task(self.run_agent(layer_name, config['system'], config.get('user_template', ''), output_model))
            tasks.append((layer_name, task))

        # Paralel çalıştır
        results = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)

        results_dict = {}
        for (name, _), result in zip([(n, None) for n in LAYER_ORDER], results):
            if isinstance(result, Exception):
                self.results[name] = {"success": False, "data": None, "error": str(result)}
            else:
                self.results[name] = result
                status = "OK" if result.get("success") else "HATA"
                print(f"   {status} {result.get('execution_time_ms', 0)}ms - {result.get('error', '')}")

        return self.results

    def get_results(self) -> Dict[str, Any]:
        return self.results


# ============================================================
# AGENT SYSTEM PROMPTS - Structured Output için güncellenmiş
# ============================================================

AGENT_PROMPTS = {
    'hendek-ajani': {
        'name': 'hendek-ajani',
        'desc': 'Hendek (Moat) Analizi',
        'system': """Sen BIST hendek (moat) analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "components": [
    {"component": "Fiyatlama Gücü", "score": 65, "evidence": "..."},
    {"component": "Maliyet Avantajı", "score": 70, "evidence": "..."},
    {"component": "Kapasite/Ölçek", "score": 80, "evidence": "..."},
    {"component": "Geçiş Maliyeti", "score": 85, "evidence": "..."},
    {"component": "Düzenleyici Bariyer", "score": 70, "evidence": "..."}
  ],
  "total_score": 59,
  "classification": "DAR",
  "differentiation": "SDTTR, uzay/aviyonik IP ve SSB entegrasyonu ile ayrışır...",
  "risks": ["Tek müşteri (SSB) riski", "FCF volatilitesi"]
}""",
        'user_template': """VERI:
{finansal}
{sektor_rakip}
{kap_dipnotlar}

Yukarıdaki verilerle hendek analizi yap. CIKTI: SADECE JSON.""",
    },

    'hikaye-ajani': {
        'name': 'hikaye-ajani',
        'desc': 'Hikaye & Sektör Analizi',
        'system': """Sen şirket hikayesi analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "sector_name": "Savunma/Uzay Teknolojileri",
  "sector_outlook": "Büyüme - Türkiye savunma ihracatı ve uzay programı...",
  "investment_map": [
    {"name": "Kapasite Genişletme", "timeline": "2025-2026", "capex": "~1.5 Mrd TL", "roic_target": "%10-15", "description": "Yeni üretim hatları..."}
  ],
  "catalysts": [
    {"name": "Sermaye Artırımı", "impact": "Pozitif", "timeline": "0-6 ay", "description": "11 kat hisse artışı..."}
  ],
  "moat": {
    "type": "Devlet destekli yarı-tekel + değişim maliyeti + teknoloji/birikim + lisans/sertifikasyon bariyerleri",
    "strength": 4.5,
    "evidence": "platformlara gömülü sistemler (müşteri değişimi pratikte yok), TSKGV sahipliği ana müşteriyle çıkar uyumu yaratıyor; fiili iç-tekel; 50 yıllık mühendislik birikimi, yeni nesil platformlarda (KAAN ≈) tedarikçi konumu kilitlenecek."
  },
  "maturity": "Olgun — ama büyüme karakterini koruyor: 50 yıllık, 1990'lardan beri borsada; gelir +%20-30 bandında ≈, rekor ihracat, yeni programlar (KAAN, hava savunma) nedeniyle bilançosu hâlâ 'büyüme evresi' davranışı sergiliyor; seyreltici sermaye artırımı yok ≈ olgunluk + öz-finansman göstergesi"
}""",
        'user_template': """VERI:
{finansal}
{sektor_rakip}
{kap_dipnotlar}

Yukarıdaki verilerle hikaye analizi yap. CIKTI: SADECE JSON.""",
    },

    'bilanco-ajani': {
        'name': 'bilanco-ajani',
        'desc': 'Bilanco derin okuma - 5/10 yl tablolar, marjlar, borç, cari oran, KAP dip notları, kâr kalitesi',
        'system': """Sen bir bilanco analistisin (temel analiz uzmanı). Görevin sana verilen BIST şirketinin FİNANSAL GÜCÜNÜ ölçmek.

YÖNTEM:
1. Finansal veri kaynakları: İş Yatırım (webfetch ile isyatirim.com.tr şirket sayfası), KAP finansal raporlar (webfetch), mümkünse Python `isyatirimhisse` paketi (Python kurulu).
2. HESAPLA (mümkün olan en uzun seriyle, ideal 5-10 yıl):
   - Net kâr marjı, FAVÖK marjı, faaliyet marjı
   - Büyüme: satış ve kârın yıllık değişimi
   - Borç yapısı: borç/öz kaynak, borç/FAVÖK, borcu ödeyebilme kapasitesi
   - Cari oran (dönen varlık / kısa vadeli borç)
3. **KAP DİP NOTLARI:** Bilanço dip notlarında çoğu kişinin gözden kaçırdığı şeyleri araştır: teminatlar, davalar, taahhütler, müşteri/tedarikçi yoğunluğu, kambiyo/kur farkları, birikmiş zarar, özkaynak içinde özel kâr/zarar kalemleri.
4. **KÂR KALİTESİ:** Piotroski F-Skoru mantığıyla değerlendir (kâr pozitif mi, faaliyet nakit akışı kârı karşılıyor mu, borçluluk düşüyor mu, cari oran iyileşiyor mu...). Kâr makyajlı mı gerçek mi?
5. Finansal güç özeti: net cümleler.

ÇIKTI:
- Metin tablolarıyla metrikler (yıl sütunlarıyla seriler)
- **FİNANSAL GÜÇ:** güçlü / orta / zayıf + 3-5 cümle neden
- **"SENİN KAÇIRDIĞIN"** bölümü — dip not bulguları (en değerli kısım)
- **KÂR KALİTESİ:** gerçek/makyajlı değerlendirmesi + gerekçe
- Kaynak belirt; verisi bulunamayan metrik için tahmin uydurma, "bulunamadı" de.

ÇIKTI FORMATI (markdown tablolar + anlatım)""",
        'user_template': """VERI:
{finansal}
{haberler}
{kap_dipnotlar}

Yukarıdaki verilerle bilanco derinlemesine analiz et. CIKTI: SADECE JSON.""",
    },

    'rakip-ajani': {
        'name': 'rakip-ajani',
        'desc': 'Rakip ve sektör karşılaştırma analisti — şirketin benzerlerine göre konumu',
        'system': """Sen bir sektör analistisin. Görevin sana verilen şirketi aynı/benzer sektördeki rakipleriyle kıyaslamak.

YÖNTEM:
1. Sana verilen şirketin sektörünü belirle. Aynı veya benzer sektördeki BIST şirketlerini listele (websearch/webfetch; örn. savunma: ASELS, OTOKAR, PAMEL, NUHL...; gıda perakende: BİM, ŞOK, MİGROS... — güncel listeyi doğrula).
2. KIYASLA (her metrikte, veri nereden geliyorsa kaynağını yaz):
   - Satış büyüklüğü ve büyüme
   - Net kâr ve kârlılık (marjlar)
   - F/K, PD/DD (mümkünse)
   - Ölçek, pazar payı sinyalleri
3. KONUMLANDIR: Şirket rakiplerine göre önde mi geride mi? Daha çok mu kazanıyor? Neden (ölçek mi, verimlilik mi, marka mı)?
3. Sektörün rüzgârı: sektör geneli büyüyor mu, sıkışıyor mu?

ÇIKTI:
- **KARŞILAŞTIRMA TABLOSU** (metin tablosu: şirket × metrik, "≈" işaretli tahminler)
- **RAKİPLERE GÖRE KONUM:** önde/geride + 3-5 cümle neden
- **SEKTÖR RÜZGÂRI:** 2-3 cümle
- Kaynaklar; veri bulunamayan hücreye uydurma değer yazma.

ÇIKTI FORMATI:
```json
{
  "rows": [
    {"metric": "FAVOK Marji (5Y ort)", "target": 16.17, "peers": {"ASELS": 22.5, "HAVELSAN": 18.0}, "sector_median": 18.3, "winner": "TURKSAT"}
  ],
  "summary": "ASELS sektöründe önde...",
  "watch_items": ["ASELS marjı", "HAVELSAN ROIC"]
}
""",
        'user_template': """VERI:
{finansal}
{sektor_rakip}
{kap_dipnotlar}

SADECE JSON. Sirket hikayesi, sektör, katalizörler, hendek, makro cerceve, olgunluk seviyesi. Bilgi tabanina dayan ama emin olmadiklarini acikca isaretle. Sistem formatinda rapor sun.""",
    },

    'teknik-ajani': {
        'name': 'teknik-ajani',
        'desc': 'Teknik Pozisyon Analizi',
        'system': """Sen teknik analistsin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "trend": "YUKARI|ASAGI|YATAY",
  "rsi": 45.2,
  "rsi_signal": "NORMAL|ASIRI_ALIM|ASIRI_SATIM",
  "macd": 0.45,
  "macd_signal": 0.12,
  "macd_histogram": 0.05,
  "macd_signal_name": "AL|SAT|NOTR",
  "adx": 25.5,
  "adx_strength": "ZAYIF|NORMAL|GUCLU|COK_GUCLU",
  "volume_avg_20": 12500000,
  "sma20": 15.45,
  "sma50": 14.80,
  "sma200": 18.50,
  "ema20": 15.20,
  "ema50": 14.90,
  "atr": 1.25,
  "atr_pct": 2.5,
  "bb_upper": 16.50,
  "bb_middle": 15.00,
  "bb_lower": 13.50,
  "bb_position": 0.65,
  "trend": "YUKARI",
  "support": 12.50,
  "resistance": 18.50,
  "stop_loss": 11.50,
  "target": 18.50,
  "risk_reward": "1:2.5",
  "volume_trend": "ARTAN|AZALAN|STABIL",
  "macd_signal_name": "AL",
  "bb_squeeze": false
}""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Asagidaki hesaplamalari TA-Lib ile yap ve sonuclari JSON formatinda ver:

HESAPLANACAK GOSTERGELER:
1. RSI(14) - from close prices
2. MACD(12,26,9) - MACD line, Signal line, Histogram
3. ADX(14) - Trend guclu
4. SMA(20), SMA(50), SMA(200) - Hareketli ortalamalar
5. EMA(20), EMA(50) - Uzamsal hareketli ortalamalar
5. ATR(14) - Average True Range
6. Bollinger Bands(20,2) - Upper, Middle, Lower, Position
7. Support/Resistance - Son 52 hafta high/low ve SMA kesisimleri
7. MACD Signal - MACD vs Signal line kesisimi
8. Volume trend - Son 20 gun ort hacim vs onceki 20 gun
9. Stop Loss - ATR tabanli (2x ATR altinda) veya support altinda
10. Target - Resistance ustunde veya risk/odul 1:2 minimum
10. Risk/Reward orani

VERI:
{fiyat_teknik}

CIKTI: SADECE JSON (yukaridaki formatta). Hesaplamalari TA-Lib (talib) ile yap.
Eger veri yetersizse ilgili alan icin null yaz.""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Yukaridaki hesaplamalari TA-Lib ile yapip sonuclari JSON formatinda ver.
Eger veri yetersizse ilgili alan icin null yaz.
""",
    },

    'sektor-ajani': {
        'name': 'sektor-ajani',
        'desc': 'Katman 1: Sektor Makro Analizi',
        'system': """Sen BIST sektor makro analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "sektor_skoru": 65,
  "marj_trendi": "DARALMA|GENISLEME|STABIL",
  "marj_daralama_pp": 2.5,
  "sok_dayanikliligi": "YUKSEK|ORTA|DUSUK",
  "ciro_cagr_5y": 8.5,
  "sektor_onerisi": "...",
  "riskler": ["..."]
}""",
        'user_template': """VERI:
{sektor_veri}
{makro_veri}

Sektor makro analizi yap. KURALLAR.md'deki sektor makro esiklerini kullan. CIKTI: SADECE JSON.""",
    },

    'yonetim-ajani': {
        'name': 'yonetim-ajani',
        'desc': 'Katman 5: Yonetim / Hakim Ortak Guvenilirligi',
        'system': """Sen yonetim kalitesi analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "soz_tutarliligi": 75,
  "yk_bagimsizlik_orani": 0.45,
  "hakim_ortak_net_islem": "ALIM|SATIM|NOTR",
  "hakim_ortak_net_tutar_mn": 15.0,
  "cikar_catismasi": false,
  "yk_degisikligi_son_2yil": 1,
  "ceo_suresi_yil": 5.0,
  "yonetim_skoru": 72,
  "yonetim_degerlendirmesi": "...",
  "riskler": ["..."]
}""",
        'user_template': """VERI:
{yonetim_veri}

Yonetim ve hakim ortak guvenilirligi analizi yap. KURALLAR.md'deki yonetim esiklerini kullan. CIKTI: SADECE JSON.""",
    },

    'sektor-karsilastirma-ajani': {
        'name': 'sektor-karsilastirma-ajani',
        'desc': 'Katman 6: Sektor Ortalamasi vs Sirket',
        'system': """Sen sektor karsilastirma analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "favok_marj_farki_vs_sektor_pp": 1.5,
  "roe_farki_vs_sektor_pp": 2.0,
  "roic_farki_vs_sektor_pp": 1.0,
  "net_borc_favok_vs_sektor": 0.8,
  "pazar_payi_trend": "KAZANIYOR|KAYBEDIYOR|STABIL",
  "degerleme_percentil_vs_sektor": 1.2,
  "karsilastirma_sonucu": "USTUNDE|ALTI|ESIT",
  "detaylar": "...",
  "riskler": ["..."]
}""",
        'user_template': """VERI:
{sektor_karsilastirma_veri}
{finansal}

Sirketi sektor medyan ile karsilastir. KURALLAR.md'deki sektor karsilastirma esiklerini kullan. CIKTI: SADECE JSON.""",
    },

    'risk-ajani': {
        'name': 'risk-ajani',
        'desc': 'Risk ve duyarlilik analizi',
        'system': """Sen risk analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "overall_risk": "DUSUK|ORTA|YUKSEK|KRITIK",
  "key_risks": ["..."],
  "breaking_points": [{"metric": "...", "current": "...", "red_line": "...", "distance": "...", "consequence": "..."}]
}""",
        'user_template': """VERI:
{finansal}
{kap_dipnotlar}

Risk analizi yap. KURALLAR.md'deki risk esiklerini kullan. CIKTI: SADECE JSON.""",
    },

    'degerleme-ajani': {
        'name': 'degerleme-ajani',
        'desc': 'Degerleme analizi',
        'system': """Sen degerleme analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "current_price": 0,
  "market_cap_mn": 0,
  "net_cash_mn": 0,
  "enterprise_value_mn": 0,
  "fair_value_range": "...",
  "discount_pct": 0,
  "moat_impact": "...",
  "rows": []
}""",
        'user_template': """VERI:
{finansal}
{fiyat_teknik}
{sektor_rakip}

Degerleme analizi yap. KURALLAR.md'deki degerleme esiklerini kullan. CIKTI: SADECE JSON.""",
    },
}

AGENT_CONFIGS = {
    'hendek-ajani': {'system': AGENT_PROMPTS['hendek-ajani']['system'], 'user_template': AGENT_PROMPTS['hendek-ajani']['user_template'], 'output_key': 'hendek'},
    'hikaye-ajani': {'system': AGENT_PROMPTS['hikaye-ajani']['system'], 'user_template': AGENT_PROMPTS['hikaye-ajani']['user_template'], 'output_key': 'hikaye'},
    'bilanco-ajani': {'system': AGENT_PROMPTS['bilanco-ajani']['system'], 'user_template': AGENT_PROMPTS['bilanco-ajani']['user_template'], 'output_key': 'bilanco'},
    'rakip-ajani': {'system': AGENT_PROMPTS['rakip-ajani']['system'], 'user_template': AGENT_PROMPTS['rakip-ajani']['user_template'], 'output_key': 'rakip'},
    'temel-ajani': {'system': AGENT_PROMPTS['bilanco-ajani']['system'], 'user_template': AGENT_PROMPTS['bilanco-ajani']['user_template'], 'output_key': 'bilanco'},
    'risk-ajani': {'system': AGENT_PROMPTS['risk-ajani']['system'], 'user_template': AGENT_PROMPTS['risk-ajani']['user_template'], 'output_key': 'risk'},
    'degerleme-ajani': {'system': AGENT_PROMPTS['degerleme-ajani']['system'], 'user_template': AGENT_PROMPTS['degerleme-ajani']['user_template'], 'output_key': 'degerleme'},
    'teknik-ajani': {'system': AGENT_PROMPTS['teknik-ajani']['system'], 'user_template': AGENT_PROMPTS['teknik-ajani']['user_template'], 'output_key': 'teknik'},
    'sektor-ajani': {'system': AGENT_PROMPTS['sektor-ajani']['system'], 'user_template': AGENT_PROMPTS['sektor-ajani']['user_template'], 'output_key': 'sektor'},
    'yonetim-ajani': {'system': AGENT_PROMPTS['yonetim-ajani']['system'], 'user_template': AGENT_PROMPTS['yonetim-ajani']['user_template'], 'output_key': 'yonetim'},
    'sektor-karsilastirma-ajani': {'system': AGENT_PROMPTS['sektor-karsilastirma-ajani']['system'], 'user_template': AGENT_PROMPTS['sektor-karsilastirma-ajani']['user_template'], 'output_key': 'sektor_karsilastirma'},
}

# Layer sıralaması (paralel çalışacak)
LAYER_ORDER = [
    'sektor-ajani',
    'hendek-ajani',
    'hikaye-ajani', 
    'temel-ajani',
    'rakip-ajani',
    'yonetim-ajani',
    'sektor-karsilastirma-ajani',
    'risk-ajani',
    'degerleme-ajani',
    'teknik-ajani'
]


# ============================================================
# PARALEL AGENT RUNNER
# ============================================================

class ParallelAgentRunner:
    """7 ajanı paralelleştirilmiş çalıştırıcı"""

    def __init__(self, veri_cache: dict):
        self.veri_cache = veri_cache
        self.results = {}

    def _build_user_prompt(self, template: str) -> str:
        return template.format(**{k: str(v) for k, v in self.data.items()})

    def set_data(self, data: dict):
        self.data = data

    def _get_veri_cache(self) -> dict:
        return {
            'finansal': self.veri_cache.get('finansal', ''),
            'sektor_rakip': self.veri_cache.get('sektor_rakip', ''),
            'kap_dipnotlar': self.veri_cache.get('kap_dipnotlar', ''),
            'haberler': self.veri_cache.get('haberler', ''),
            'fiyat_teknik': self.veri_cache.get('fiyat_teknik', ''),
        }

    async def run_agent(self, layer_name: str, system_prompt: str, user_template: str, output_model: type = None) -> dict:
        """Tek ajanı çalıştır - Structured Output ile"""
        import time, json, re
        start = time.time()

        try:
            # Tek seferde formatla
            user_prompt = user_template.format(**self._get_veri_cache())

            # JSON Schema prompt'u ekle (Pydantic modelden)
            schema_prompt = ""
            if output_model:
                schema_prompt = f"\n\nCIKTI FORMATI (JSON Schema):\n{json.dumps(output_model.model_json_schema(), indent=2, ensure_ascii=False)}\n\nSADECE BU FORMATTA GEÇERLİ JSON ÜRET."

            enhanced_system = system_prompt + schema_prompt + "\n\nKURAL: SADECE GEÇERLİ JSON OBJESİ. HİÇBİR METİN, AÇIKLAMA, DÜŞÜNCE, MARKDOWN KOD BLOĞU YOK."

            # Use already imported call_nvidia from nvidia_client
            raw_output = await call_nvidia(enhanced_system, user_prompt)

            # GÜVENLİK: call_nvidia None döndürürse (timeout/retry sonrası implicit return)
            if raw_output is None:
                raw_output = "API_ERROR: call_nvidia returned None (timeout/retry exhausted)"

            # NVIDIA/API hata ön ekleri kontrolü - bunlar JSON değil, doğrudan hata döndür
            if isinstance(raw_output, str):
                error_prefixes = ("RATE_LIMIT", "API HATA", "TIMEOUT_ERROR", "CONNECTION_ERROR", "UNEXPECTED_ERROR", "MAX_RETRIES")
                if raw_output.startswith(error_prefixes):
                    return {
                        "success": False,
                        "data": None,
                        "error": raw_output,
                        "execution_time_ms": int((time.time() - start) * 1000)
                    }

            # Parse JSON
            raw = str(raw_output).strip()
            if not raw:
                raise ValueError("API returned empty response")

            # Markdown kod bloklarını güvenli şekilde temizle (IndexError riski yok)
            if raw.startswith('```json'):
                parts = raw.split('```json', 1)
                if len(parts) > 1:
                    raw = parts[1].rsplit('```', 1)[0]
            elif raw.startswith('```'):
                parts = raw.split('```', 1)
                if len(parts) > 1:
                    raw = parts[1].rsplit('```', 1)[0]

            raw = raw.strip()

            # İlk { ve son } arası JSON'u çıkar
            start_idx = raw.find('{')
            end_idx = raw.rfind('}')
            if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
                raise ValueError(f"No valid JSON object found in response. Preview: {raw[:200]}")

            json_str = raw[start_idx:end_idx + 1]
            parsed = json.loads(json_str)

            return {
                "success": True,
                "data": parsed,
                "error": None,
                "execution_time_ms": int((time.time() - start) * 1000)
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": f"JSON Parse Hatası: {str(e)}",
                "execution_time_ms": int((time.time() - start) * 1000)
            }

    async def run_all_parallel(self) -> Dict[str, dict]:
        """7 ajanı paralelleştir"""
        print(f"\n{'='*50}")
        print("7 AJAN PARALEL CALISIYOR")
        print(f"{'='*50}")

        from structured_output import (
            MoatAnalysis, StorySector, FundamentalTable, PeerComparison,
            RiskAnalysis, ValuationAnalysis, TechnicalPosition
        )

        OUTPUT_MODELS = {
            'sektor-ajani': None,
            'hendek-ajani': MoatAnalysis,
            'hikaye-ajani': StorySector,
            'temel-ajani': FundamentalTable,
            'rakip-ajani': PeerComparison,
            'yonetim-ajani': None,
            'sektor-karsilastirma-ajani': None,
            'risk-ajani': RiskAnalysis,
            'degerleme-ajani': ValuationAnalysis,
            'teknik-ajani': TechnicalPosition,
        }

        tasks = []
        for layer_name in LAYER_ORDER:
            config = AGENT_CONFIGS[layer_name]
            output_model = OUTPUT_MODELS.get(layer_name)
            task = asyncio.create_task(self.run_agent(layer_name, config['system'], config.get('user_template', ''), output_model))
            tasks.append((layer_name, task))

        # Paralel çalıştır
        results = await asyncio.gather(*[t for _, t in tasks], return_exceptions=True)

        results_dict = {}
        for (name, _), result in zip([(n, None) for n in LAYER_ORDER], results):
            if isinstance(result, Exception):
                self.results[name] = {"success": False, "data": None, "error": str(result)}
            else:
                self.results[name] = result
                status = "OK" if result.get("success") else "HATA"
                print(f"   {status} {result.get('execution_time_ms', 0)}ms - {result.get('error', '')}")

        return self.results

    def get_results(self) -> Dict[str, Any]:
        return self.results


# ============================================================
# SENTEZ - JINJA2 TEMPLATE (LLMsiz)
# ============================================================

REPORT_TEMPLATE = """# {{ symbol }} ANALIZ RAPORU — {{ date }}

## KARAR KUTUSU: {{ verdict_emoji }} {{ verdict }}

---

## 1. HENDEK (MOAT) — 5/10 YIL

**SKOR: {{ moat.total_score }}/100 -> [{{ moat.classification }}]

| Bileşen | Skor (0-100) | Kanıt |
|---|---|---|
{% for c in moat.components %}
| {{ c.component }} | {{ c.score }} | {{ c.evidence }} |
{% endfor %}

**Ayrisma Nedeni:** {{ moat.differentiation }}

**Risk:** {% for r in moat.risks %}- {{ r }} {% endfor %}

---

## 2. HİKAYE & SEKTÖR — YATIRIM HARİTASI + KATALİZÖRLER

{{ story }}

---

## 3. TEMEL ANALİZ & KAP DİP NOTLARI

{{ fundamental }}

---

## 4. TEKNİK ANALİZ

{{ technical }}

---

## 5. RAKİP & SEKTÖR KIYASI

{{ peer }}

---

## 6. AYI / RİSK ANALİZİ

{{ risk }}

---

## 7. DEĞERLEME

```json
{{ valuation }}
```

---

## SENİN KAÇIRDIKLARIN (KAP Dip Notları)

{{ kap_notes }}

---

## 8. DELTA — SON 5 DÖNEM TEMEL KARŞILAŞTIRMA

{{ fundamental }}
---

## SENİN KAÇIRDIKLARIN (KAP Dip Notları)

{{ kap_notes }}

---

## RAKIP KARŞILAŞTIRMA — GÜÇLÜ / ZAYİF YÖNLER (KURALLAR.md Eşikleri)

| Metrik | Sen | Rakip Ortalama | Durum |
|--------|-----|----------------|-------|
| FAVOK Marjı % | {{ peer.favok_marj_vs_sektor|default('-') }} | {{ peer.sektor_ort_favok_marj|default('-') }} | {{ peer.favok_marj_durum|default('-') }} |
| ROIC % | {{ peer.roic_vs_sektor|default('-') }} | {{ peer.sektor_ort_roic|default('-') }} | {{ peer.roic_durum|default('-') }} |
| ROE % | {{ peer.roe_vs_sektor|default('-') }} | {{ peer.sektor_ort_roe|default('-') }} | {{ peer.roe_durum|default('-') }} |
| Net Borç/FAVOK | {{ peer.net_borc_favok_vs_sektor|default('-') }} | {{ peer.sektor_ort_net_borc_favok|default('-') }} | {{ peer.net_borc_favok_durum|default('-') }} |
| Cari Oran | {{ peer.cari_oran_vs_sektor|default('-') }} | {{ peer.sektor_ort_cari_oran|default('-') }} | {{ peer.cari_oran_durum|default('-') }} |

**Özet:** {{ peer.karsilastirma_ozet|default('Rakip karşılaştırma verisi yok.') }}

---

*Bu analiz bilgi amaclidir; yatirim tavsiyesi degildir.*"""

# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

class AnalysisOrchestrator:
    """Ana orkestratör - Paralel agent + Template rapor"""

    def __init__(self):
        self.data_layer = DataLayer()
        self.agent_runner = None

    async def run_analysis(self, symbol: str, skip_data: bool = False) -> str:
        """Ana analiz fonksiyonu"""
        print(f"\n{'#'*60}")
        print(f"# BIST ANALIZ: {symbol}")
        print(f"{'#'*60}")

        # 1. Veri toplama
        if not skip_data:
            print(f"\n{'='*50}")
            print("VERI TOPLAMA")
            print(f"{'='*50}")
            async with DataLayer() as dl:
                data = await dl.fetch_complete(symbol)
        else:
            async with DataLayer() as dl:
                data = await dl.fetch_complete(symbol)

        # Veriyi agent'lar için hazırla
        veri_cache = self._prepare_veri_cache(data)
        runner = ParallelAgentRunner(veri_cache)
        runner.set_data(veri_cache)
        agent_results = await runner.run_all_parallel()

        # 3. Sonuçları birleştir
        analysis = self._build_analysis(data, runner.results)

        # 3b. Rakip karşılaştırma özetini ekle (KURALLAR.md eşikleriyle)
        peer_raw = agent_results.get('rakip-ajani', {}).get('data', {}) or {}
        fundamental_raw = agent_results.get('bilanco-ajani', {}).get('data', {}) or {}
        periods = fundamental_raw.get('periods', []) or []
        latest = periods[0] if periods else {}

        # Rakip satırlarından sektör ortalamasını hesapla
        rows = peer_raw.get('rows', []) if isinstance(peer_raw, dict) else []
        def _row_val(metric_name, key='target'):
            for r in rows:
                if isinstance(r, dict) and r.get('metric') == metric_name:
                    return r.get(key)
            return None

        # Sektör ortalama = peer'ların ortalaması (basit)
        def _sektor_avg(metric_name):
            vals = []
            for r in rows:
                if isinstance(r, dict) and r.get('metric') == metric_name:
                    peers = r.get('peers', {}) or {}
                    for v in peers.values():
                        if v is not None:
                            try: vals.append(float(v))
                            except: pass
            return round(sum(vals)/len(vals), 2) if vals else None

        def _durum(sen, ort, iyi_yonuk='yuksek'):
            if sen is None or ort is None:
                return 'VERI YOK'
            if iyi_yonuk == 'yuksek':
                return 'GÜÇLÜ' if sen > ort else ('ZAYIF' if sen < ort else 'EŞIT')
            else:
                return 'GÜÇLÜ' if sen < ort else ('ZAYIF' if sen > ort else 'EŞIT')

        favok_sen = _row_val('FAVOK Marji (5Y ort)', 'target') or latest.get('favok_margin_pct')
        favok_ort = _sektor_avg('FAVOK Marji (5Y ort)')
        roic_sen = _row_val('ROIC (5Y ort)', 'target') or latest.get('roic_pct')
        roic_ort = _sektor_avg('ROIC (5Y ort)')
        roe_sen = _row_val('ROE (5Y ort)', 'target') or latest.get('roe_pct')
        roe_ort = _sektor_avg('ROE (5Y ort)')
        ndf_sen = _row_val('Net Borç/FAVOK', 'target') or latest.get('net_debt_favok')
        ndf_ort = _sektor_avg('Net Borç/FAVOK')
        cari_sen = _row_val('Cari Oran', 'target') or latest.get('current_ratio')
        cari_ort = _sektor_avg('Cari Oran')

        # Özet metni
        ozut_parcalari = []
        if favok_sen and favok_ort:
            ozut_parcalari.append(f"FAVÖK marjı {'+' if (favok_sen-favok_ort)>=0 else ''}{favok_sen-favok_ort:+.2f}pp sektöre göre")
        if roic_sen and roic_ort:
            ozut_parcalari.append(f"ROIC {'+' if (roic_sen-roic_ort)>=0 else ''}{roic_sen-roic_ort:+.2f}pp sektöre göre")
        if cari_sen and cari_ort:
            ozut_parcalari.append(f"Cari oran {'+' if (cari_sen-cari_ort)>=0 else ''}{cari_sen-cari_ort:+.2f}x sektöre göre")
        karsilastirma_ozet = '; '.join(ozut_parcalari) if ozut_parcalari else 'Karşılaştırma verisi yetersiz.'

        peer_raw.update({
            'favok_marj_vs_sektor': favok_sen,
            'sektor_ort_favok_marj': favok_ort,
            'favok_marj_durum': _durum(favok_sen, favok_ort),
            'roic_vs_sektor': roic_sen,
            'sektor_ort_roic': roic_ort,
            'roic_durum': _durum(roic_sen, roic_ort),
            'roe_vs_sektor': roe_sen,
            'sektor_ort_roe': roe_ort,
            'roe_durum': _durum(roe_sen, roe_ort),
            'net_borc_favok_vs_sektor': ndf_sen,
            'sektor_ort_net_borc_favok': ndf_ort,
            'net_borc_favok_durum': _durum(ndf_sen, ndf_ort, 'asagi'),
            'cari_oran_vs_sektor': cari_sen,
            'sektor_ort_cari_oran': cari_ort,
            'cari_oran_durum': _durum(cari_sen, cari_ort, 'yuksek'),
            'karsilastirma_ozet': karsilastirma_ozet,
        })
        analysis['peer'] = self._format_any_as_md(peer_raw, "RAKİP KARŞILAŞTIRMA")

        # 4. Template ile rapor üret - tek render
        from jinja2 import Template
        template = Template(REPORT_TEMPLATE)
        report = template.render(
            symbol=symbol,
            date=datetime.now().strftime("%d %B %Y"),
            verdict_emoji=analysis['verdict_emoji'],
            verdict=analysis['verdict'],
            rationale=analysis['rationale'],
            moat=analysis['moat'],
            story=analysis['story'],
            fundamental=analysis['fundamental'],
            technical=analysis['technical'],
            peer=analysis['peer'],
            risk=analysis['risk'],
            valuation=analysis['valuation'],
            kap_notes=analysis['kap_notes'],
        )

        # Raporu kaydet
        os.makedirs("analiz-arşivi", exist_ok=True)
        report_path = f"analiz-arşivi/{symbol.replace('.IS','')}-{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  [OK] Rapor kaydedildi: {report_path}")

        return report_path

    def _prepare_veri_cache(self, data: CompleteData) -> dict:
        """Veriyi agent'lar için hazırla"""
        return {
            'finansal': self._format_finansal(data.financial),
            'sektor_rakip': self._format_sektor_rakip(data.sector_peers),
            'kap_dipnotlar': data.kap_notifications,
            'haberler': self._format_haberler(data.news),
            'fiyat_teknik': self._format_fiyat_teknik(data.technical),
        }

    def _format_finansal(self, financial: FundamentalTable) -> str:
        if not financial.periods:
            return "Veri yok"
        parts = []
        for p in financial.periods:
            parts.append(f"Dönem: {p.period}, Satış: {p.sales or 'N/A'} Mn, FAVÖK Marj: {p.favok_margin or 'N/A'}%, Net Marj: {p.net_margin or 'N/A'}%, Net Borç/FAVÖK: {p.net_debt_favok or 'N/A'}x, Cari Oran: {p.current_ratio or 'N/A'}")
        return "\n".join(parts)

    def _format_sektor_rakip(self, peer_list: list) -> str:
        """Sektör peer listesi (string listesi)"""
        if not peer_list:
            return "Rakip verisi yok"
        return "Sektör rakipleri: " + ", ".join(peer_list)

    def _format_haberler(self, news: list) -> str:
        if not news:
            return "Haber yok"
        return "\n".join([f"- {n.title}: {n.summary[:100]}... ({n.source})" for n in news[:10]])

    def _format_fiyat_teknik(self, technical: TechnicalData) -> str:
        if not technical:
            return "Teknik veri yok"
        return f"Fiyat: {technical.price or 0:.2f} TL, RSI: {technical.rsi or 0:.1f}, Trend: {technical.trend or 'N/A'}, Destek: {technical.support or 0:.2f}, Direnç: {technical.resistance or 0:.2f}"

    def _format_any_as_md(self, data: Any, label: str = "") -> str:
        """Her türlü dict/list veriyi okunabilir markdown'a dönüştürür."""
        if not data:
            return f"{label}: Veri yok\n" if label else "Veri yok\n"

        # Dict ise anahtar-değer tablosu
        if isinstance(data, dict):
            lines = []
            if label:
                lines.append(f"### {label}\n")
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"- **{k}:** {self._format_any_as_md(v)}")
                elif v is None or v == "":
                    lines.append(f"- **{k}:** -")
                else:
                    lines.append(f"- **{k}:** {v}")
            return "\n".join(lines) + "\n"

        # Liste ise madde işaretli
        if isinstance(data, list):
            lines = []
            if label:
                lines.append(f"### {label}\n")
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    lines.append(f"{i}. {item.get('metric', item.get('name', str(item)))}")
                    for k, v in item.items():
                        if k not in ('metric', 'name'):
                            lines.append(f"   - {k}: {v}")
                else:
                    lines.append(f"{i}. {item}")
            return "\n".join(lines) + "\n"

        return str(data) + "\n"

    def _build_analysis(self, data: CompleteData, agent_results: Dict[str, dict]) -> dict:
        """Agent sonuçlarını birleştir - tüm veriyi okunabilir markdown'a dönüştürür"""
        moat = agent_results.get('hendek-ajani', {}).get('data', {}) or {}
        story = agent_results.get('hikaye-ajani', {}).get('data', {}) or {}
        fundamental = agent_results.get('bilanco-ajani', {}).get('data', {}) or {}
        technical = agent_results.get('teknik-ajani', {}).get('data', {}) or {}
        peer = agent_results.get('rakip-ajani', {}).get('data', {}) or {}
        risk = agent_results.get('risk-ajani', {}).get('data', {}) or {}
        valuation = agent_results.get('degerleme-ajani', {}).get('data', {}) or {}
        kap_notes = agent_results.get('risk-ajani', {}).get('data', {}) or {}

        return {
            'verdict_emoji': '🟢' if 'GUCLU' in str(moat).upper() else ('🟡' if 'ORTA' in str(moat).upper() else '🔴'),
            'verdict': 'GÜÇLÜ' if 'GUCLU' in str(moat).upper() else ('NÖTR' if 'ORTA' in str(moat).upper() else 'RİSKLİ'),
            'rationale': 'Hendek güçlü, temel sağlam, değerleme ucuz',
            'moat': self._format_any_as_md(moat, "HENDEK (MOAT)"),
            'story': self._format_any_as_md(story, "HİKAYE & SEKTÖR"),
            'fundamental': self._format_any_as_md(fundamental, "TEMEL ANALİZ"),
            'technical': self._format_any_as_md(technical, "TEKNİK ANALİZ"),
            'peer': self._format_any_as_md(peer, "RAKİP KARŞILAŞTIRMA"),
            'risk': self._format_any_as_md(risk, "AYI / RİSK ANALİZİ"),
            'valuation': self._format_any_as_md(valuation, "DEĞERLEME"),
            'kap_notes': self._format_any_as_md(kap_notes, "KAP DİP NOTLARI"),
        }

    def _extract_kap_notes(self) -> str:
        return "KAP dip notları analizi burada yer alacak"

    async def run_analysis(self, symbol: str, skip_data: bool = False) -> str:
        """Ana analiz fonksiyonu"""
        return await self._run_analysis_impl(symbol, skip_data)

    async def _run_analysis_impl(self, symbol: str, skip_data: bool = False) -> str:
        """Ana analiz fonksiyonu - gercek islem"""
        print(f"\n{'#'*60}")
        print(f"# BIST ANALIZ: {symbol}")
        print(f"{'#'*60}")

        # 1. Veri toplama
        if not skip_data:
            print(f"\n{'='*50}")
            print("VERI TOPLAMA")
            print(f"{'='*50}")
            async with DataLayer() as dl:
                data = await dl.fetch_complete(symbol)
        else:
            async with DataLayer() as dl:
                data = await dl.fetch_complete(symbol)

        # Veriyi agent'lar için hazırla
        veri_cache = self._prepare_veri_cache(data)
        runner = ParallelAgentRunner(veri_cache)
        runner.set_data(veri_cache)
        agent_results = await runner.run_all_parallel()

        # 3. Sonuçları birleştir
        analysis = self._build_analysis(data, runner.results)

        # 3b. Rakip karşılaştırma özetini ekle (KURALLAR.md eşikleriyle)
        peer_raw = agent_results.get('rakip-ajani', {}).get('data', {}) or {}
        fundamental_raw = agent_results.get('bilanco-ajani', {}).get('data', {}) or {}
        periods = fundamental_raw.get('periods', []) or []
        latest = periods[0] if periods else {}

        # Rakip satırlarından sektör ortalamasını hesapla
        rows = peer_raw.get('rows', []) if isinstance(peer_raw, dict) else []
        def _row_val(metric_name, key='target'):
            for r in rows:
                if isinstance(r, dict) and r.get('metric') == metric_name:
                    return r.get(key)
            return None

        def _sektor_avg(metric_name):
            vals = []
            for r in rows:
                if isinstance(r, dict) and r.get('metric') == metric_name:
                    peers = r.get('peers', {}) or {}
                    for v in peers.values():
                        if v is not None:
                            try: vals.append(float(v))
                            except: pass
            return round(sum(vals)/len(vals), 2) if vals else None

        def _durum(sen, ort, iyi_yonuk='yuksek'):
            if sen is None or ort is None:
                return 'VERI YOK'
            if iyi_yonuk == 'yuksek':
                return 'GÜÇLÜ' if sen > ort else ('ZAYIF' if sen < ort else 'EŞIT')
            else:
                return 'GÜÇLÜ' if sen < ort else ('ZAYIF' if sen > ort else 'EŞIT')

        favok_sen = _row_val('FAVOK Marji (5Y ort)', 'target') or latest.get('favok_margin_pct')
        favok_ort = _sektor_avg('FAVOK Marji (5Y ort)')
        roic_sen = _row_val('ROIC (5Y ort)', 'target') or latest.get('roic_pct')
        roic_ort = _sektor_avg('ROIC (5Y ort)')
        roe_sen = _row_val('ROE (5Y ort)', 'target') or latest.get('roe_pct')
        roe_ort = _sektor_avg('ROE (5Y ort)')
        ndf_sen = _row_val('Net Borç/FAVOK', 'target') or latest.get('net_debt_favok')
        ndf_ort = _sektor_avg('Net Borç/FAVOK')
        cari_sen = _row_val('Cari Oran', 'target') or latest.get('current_ratio')
        cari_ort = _sektor_avg('Cari Oran')

        # Özet metni
        ozut_parcalari = []
        if favok_sen and favok_ort:
            ozut_parcalari.append(f"FAVÖK marjı {'+' if (favok_sen-favok_ort)>=0 else ''}{favok_sen-favok_ort:+.2f}pp sektöre göre")
        if roic_sen and roic_ort:
            ozut_parcalari.append(f"ROIC {'+' if (roic_sen-roic_ort)>=0 else ''}{roic_sen-roic_ort:+.2f}pp sektöre göre")
        if cari_sen and cari_ort:
            ozut_parcalari.append(f"Cari oran {'+' if (cari_sen-cari_ort)>=0 else ''}{cari_sen-cari_ort:+.2f}x sektöre göre")
        karsilastirma_ozet = '; '.join(ozut_parcalari) if ozut_parcalari else 'Karşılaştırma verisi yetersiz.'

        peer_raw.update({
            'favok_marj_vs_sektor': favok_sen,
            'sektor_ort_favok_marj': favok_ort,
            'favok_marj_durum': _durum(favok_sen, favok_ort),
            'roic_vs_sektor': roic_sen,
            'sektor_ort_roic': roic_ort,
            'roic_durum': _durum(roic_sen, roic_ort),
            'roe_vs_sektor': roe_sen,
            'sektor_ort_roe': roe_ort,
            'roe_durum': _durum(roe_sen, roe_ort),
            'net_borc_favok_vs_sektor': ndf_sen,
            'sektor_ort_net_borc_favok': ndf_ort,
            'net_borc_favok_durum': _durum(ndf_sen, ndf_ort, 'asagi'),
            'cari_oran_vs_sektor': cari_sen,
            'sektor_ort_cari_oran': cari_ort,
            'cari_oran_durum': _durum(cari_sen, cari_ort, 'yuksek'),
            'karsilastirma_ozet': karsilastirma_ozet,
        })
        analysis['peer'] = self._format_any_as_md(peer_raw, "RAKİP KARŞILAŞTIRMA")

        # 4. Template ile rapor üret - tek render
        from jinja2 import Template
        template = Template(REPORT_TEMPLATE)
        report = template.render(
            symbol=symbol,
            date=datetime.now().strftime("%d %B %Y"),
            verdict_emoji=analysis['verdict_emoji'],
            verdict=analysis['verdict'],
            rationale=analysis['rationale'],
            moat=analysis['moat'],
            story=analysis['story'],
            fundamental=analysis['fundamental'],
            technical=analysis['technical'],
            peer=analysis['peer'],
            risk=analysis['risk'],
            valuation=analysis['valuation'],
            kap_notes=analysis['kap_notes'],
        )

        # Raporu kaydet
        os.makedirs("analiz-arşivi", exist_ok=True)
        report_path = f"analiz-arşivi/{symbol.replace('.IS','')}-{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  [OK] Rapor kaydedildi: {report_path}")

        return report_path


async def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="BIST Paralel Çoklu-Ajan Analiz")
    parser.add_argument("sembol", help="Hisse sembolu (orn: ASELS.IS)")
    parser.add_argument("--skip-veri", action="store_true", help="Veri toplama atla")
    args = parser.parse_args()

    orchestrator = AnalysisOrchestrator()
    path = await orchestrator.run_analysis(args.sembol, skip_data=args.skip_veri)
    print(f"\nRapor kaydedildi: {path}")


if __name__ == "__main__":
    asyncio.run(main())