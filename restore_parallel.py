#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restore parallel_agents.py from backup logic
"""

# Complete parallel_agents.py content
content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parallel Agent Runner - 7 ajan asyncio.gather ile paralelleştirilmiş
Structured Output (pydantic) zorunlu - monolog YOK
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

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
        self.veri_cache = data

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
        import time
        start = time.time()

        try:
            # Tek seferde formatla
            user_prompt = user_template.format(**self._get_veri_cache())

            # JSON Schema prompt'u ekle (Pydantic modelden)
            schema_prompt = ""
            if output_model:
                import json
                schema_prompt = f"\\n\\nCIKTI FORMATI (JSON Schema):\\n{json.dumps(output_model.model_json_schema(), indent=2, ensure_ascii=False)}\\n\\nSADECE BU FORMATTA GEÇERLİ JSON ÜRET."

            enhanced_system = system_prompt + schema_prompt + "\\n\\nKURAL: SADECE GEÇERLİ JSON OBJESİ. HİÇBİR METİN, AÇIKLAMA, DÜŞÜNCE, MARKDOWN KOD BLOĞU YOK."

            # Use already imported call_nvidia from nvidia_client
            raw_output = await call_nvidia(enhanced_system, user_prompt)

            # GÜVENLİK: call_nvidia None döndürürse (timeout/retry sonrası implicit return)
            if raw_output is None:
                raw_output = "API_ERROR: call_nvidia returned None (timeout/retry exhausted)"

            # Parse JSON
            raw = raw_output.strip()
            if raw.startswith('```json'):
                raw = raw.split('```json')[1].split('```')[0]
            elif raw.startswith('```'):
                raw = raw.split('```')[1].split('```')[0]

            # Remove any leading/trailing whitespace
            raw = raw.strip()

            # Try to find JSON object in the response (in case there's extra text)
            if not raw.startswith('{'):
                # Try to find first {
                start_idx = raw.find('{')
                if start_idx != -1:
                    raw = raw[start_idx:]
                else:
                    raise ValueError(f"No JSON object found in response: {raw[:200]}")

            # Also handle case where there's trailing text after the JSON
            # Find the last } and truncate there
            if raw.endswith('}'):
                pass  # Already ends with }
            else:
                # Try to find the last } and truncate
                last_brace = raw.rfind('}')
                if last_brace != -1:
                    raw = raw[:last_brace + 1]

            parsed = json.loads(raw)

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
                "error": str(e),
                "execution_time_ms": int((time.time() - start) * 1000)
            }

    async def run_all_parallel(self) -> Dict[str, dict]:
        """7 ajanı paralelleştir"""
        print(f"\\n{'='*50}")
        print("7 AJAN PARALEL CALISIYOR")
        print(f"{'='*50}")

        from structured_output import (
            MoatAnalysis, StorySector, FundamentalTable, PeerComparison,
            RiskAnalysis, ValuationAnalysis, TechnicalPosition
        )

        OUTPUT_MODELS = {
            'hendek-ajani': MoatAnalysis,
            'hikaye-ajani': StorySector,
            'temel-ajani': FundamentalTable,
            'rakip-ajani': PeerComparison,
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
    "evidence": "platformlara gömülü sistemler (müşteri değişimi pratikte yok), TSKGV sahipliği ana müşteriyle çıkar uyumu yaratıyor, fiili iç-tekel, 50 yıllık mühendislik birikimi, KAAN'da kilit tedarikçi ≈"
  },
  "macro_risks": ["Kur riski", "Enflasyon", "Faiz", "Jeopolitik"],
  "maturity": "Olgun - ama büyüme karakterli"
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
    "evidence": "platformlara gömülü sistemler (müşteri değişimi pratikte yok), TSKGV sahipliği ana müşteriyle çıkar uyumu yaratıyor, fiili iç-tekel, 50 yıllık mühendislik birikimi, yeni nesil platformlarda (KAAN ≈) tedarikçi konumu kilitlenecek."
  },
  "catalysts": [
    {"name": "Sermaye Artırımı", "impact": "Pozitif", "timeline": "0-6 ay", "description": "11 kat hisse artışı..."},
    {"name": "€523 milyonluk savunma sözleşmesi", "impact": "Pozitif", "timeline": "6-12 ay", "description": "İhracat kanalı ve gelir görünürlüğü"}
  ]
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
  ]
}""",
        'user_template': """VERI:
{finansal}
{sektor_rakip}
{kap_dipnotlar}

Yukarıdaki verilerle hikaye analizi yap. CIKTI: SADECE JSON.""",
    },

    'bilanco-ajani': {
        'name': 'bilanco-ajani',
        'desc': 'Bilanco analisti - marjlar, borç, cari oran, KAP dip notları, kâr kalitesi',
        'system': """Sen bir bilanco analistisin (temel analiz uzmanı). Görevin sana verilen BIST şirketinin FİNANSAL GÜCÜNÜ ölçmek.

YÖNTEM:
1. Finansal veri kaynakları: İş Yatırım (webfetch ile isyatirim.com.tr şirket sayfası), KAP finansal raporlar (webfetch), mümkünse Python `isyatirimhisse` paketi (Python kurulu).
2. HESAPLA (mümkün olan en uzun seriyle, ideal 5-10 yıl):
   - Net kâr marjı, FAVÖK marjı, faaliyet marjı
   - Büyüme: satış ve kârın yıllık değişimi
   - Borç yapısı: borç/öz kaynak, borç/FAVÖK, borcu ödeyebilme kapasitesi
   - Cari oran (dönen varlık / kısa vadeli borç)
3. **KAP DİP NOTLARI:** Bilanço dip notlarında çoğu kişinin gözden kaçırdığı şeyleri araştır: teminatlar, davalar, taahhütler, kambiyo/kur farkları, birikmiş zarar, özkaynak içinde özel kâr/zarar kalemleri.
4. **KÂR KALİTESİ:** Piotroski F-Skoru mantığıyla değerlendir (kâr pozitif mi, faaliyet nakit akışı kârı karşılıyor mu, borçluluk düşüyor mu, cari oran iyileşiyor mu...). Kâr makyajlı mı gerçek mi?
5. Finansal güç özeti: net cümleler.

ÇIKTI:
- Metin tablolarıyla metrikler (yıl sütunlarıyla seriler)
- **FİNANSAL GÜÇ:** güçlü / orta / zayıf + 3-5 cümle neden
- **"SENİN KAÇIRDIGIN"** bölümü — dip not bulguları (en değerli kısım)
- **KÂR KALİTESİ:** gerçek/makyajlı değerlendirmesi + gerekçe
- Kaynak belirt; verisi bulunamayan metrik için tahmin uydurma, "bulunamadı" de.

ÇIKTI:
```markdown
## KATMAN 9: BILANCO DERIN OKUMA (5-10 YIL)

### TABLO 1: CIRO -> NET KAR (5-10 YIL, Mn TL)
| Yil | Ciro | YoY D% | Net Kâr | YoY D% |
|-----|------|--------|---------|--------|
| 2019 | X | - | X | X% |
| 2020 | X | X% | X | X% |
...

### TABLO 2: MARJ TRENDİ (5 YIL)
| Yil | Brut Marj | Faaliyet Marjı | FAVÖK Marj | Net Marj | Yurtdışı Satış Payı |
|-----|-----------|----------------|------------|----------|---------------------|
| 2019 | X% | X% | X% | X% | X% |

### TABLO 3: BORÇLULUK VE ÖDEME KAPASİTESİ (5 YIL, Mn TL)
| Yil | Fin. Borç | Nakit | **Net Borç** | Net Borc/FAVOK (yıllaştırılmış) |
|-----|----------|-------|--------------|-------------------------------|

### TABLO 4: CARİ ORAN (temsili — alt sınır)
| Yil | Cari (temsili) | Asit-Test proxy |
|-----|----------------|-----------------|

### TABLO 5: İŞLETME SERMAYESİ / GÖRÜNÜRLÜK
| Yil | Stoklar | Ticari Alacak (kısa+uzun) | Ertelenmiş Gelir (K+U) |

## FİNANSAL GÜÇ: **ORTA–GÜÇLÜ** (kâr kalitesi güçlü, likidite sıkışık, yön riskli taraf)

1. Kârlılık kaliteli açıdan güçlü: gelir 3 yılda 2x, net kâr 3,3x; yıllık faaliyet nakit akışı kârı 1,14x–1,63x **aşan** oranla örtüyor; net borç/FAVÖK proxy 0,3–0,7x ile düşük.
2. Ama likidite yapısı gerilimli: temsili cari ~1,1, asit-test 0,5.
3. 2026 twin uyarısı: net borç 2x + faaliyet marjı gerilemesi. Tek başına kriz değil; kum saati işareti.
4. Reel büyüme durgunlaşmış (2025 ≈ sıfır, 2026 H1 muhtemelen negatif).

## "SENİN KAÇIRABİLECEĞİN" — Veri/deneyim bulguları

1. **Kârın önemli dilimi ertelenmiş vergi kaynaklı olabilir.** Vergi satırı avantajlı: 2023 Q1'de +764 mn pre-taxe kâra rağmen −1.921 ertelenmiş vergi gideriyle **zarar**; 2024 Q1 ve paketinde pre-taxe **negatif** (−736 mn) iken +2.447 vergi geliriyle kâr pozitif çıktı; 2025 Q1'de pre-taxe −2.795'e karşın +5.587 vergi geliri → +2.792 kâr. Yıllık bazda: 2024 FY vergi geliri +9.106 mn = **net kârın ~%45'i**; 2025 FY +4.153 mn = ~%12; 2026 H1 +1.800 mn = ~%12.5. 2024 kârı "vergi sanatıyla şişkin" değerlendirilebilir. (Ertelenmiş vergi kalıcılığı dip notlarla doğrulanmalı.)
2. **"Diğer Faaliyet Gelirleri" (3DD) marjı oynatan yumuşak kalem**: 2023 FY 48,4 mn (gelirin 45-fark-i!), 2024 22,9 mn, 2025 38,2 mn, 2026 H1 19,2 mn → karşılık gideri 3DE. ASELSAN yapısında bu tipik olarak ortaklık kâr payları + diğer faaliyet gelirleri karışımı — ama **yeniden sınıflandırma geçerli mi** (gider/kâr ayrımı) dip notları olmadan bilinemiyor. 2023 ile 2024 faaliyet marj farkının (%33,9→%22,7) büyük kısmı bu dakik.
3. **Kur çevrim farkı her çeyrek nakit yakıyor** (4CBG): 2023'te −5.213 mn FY, 2026 H1 −4.169 mn. Nakit ve nakit benzerleri USD/EUR pozisyonuna — kur direnci dip notla doğrulanmalı; net FX pozisyonu (netex) **bilinmiyor**.
4. **2025'in 9A–Q4 asimetrisi:** 9A 2025 +%12,3 → Q4 +59%. Teslim süresi/fatura uzunluğu ertelenmiş gelirde birikmiş (76,8 mn). Q4'e değil çeyreğe bağımlılık klasik ASELSAN profili ama büyüklüğünde artış var.
5. **Cari oran sıkışıklığı** (~1,1) ST borcun %70,4'ünü dönüyor — stokların %68'i kısa vade (KVK) tarafında; finansman ihtiyacı çeyreksel yükselebilir.
6. ⚠️ **Doğrulanmadı — KAP dip notu kontrol listesi:** müşteri yoğunluğu (İdariclik ve Türk Hava Yükleme limitleri), kambiyo HİB/YİB hibeleri, termal davalar, uluslararası satış taahhütleri, birikmiş zarar, özel kâr/zarar ile özkaynak invazif kalemler — **erisilemedi**. Özellikle **ihracat payı %17,2'ye çıkarken** (hedge/müsader riski artıyor) bu dip notlar kritik.

## KÂR KALİTESİ: **Nispeten gerçek — ama iki ufuk sorgulaması var**

| Piotroski kryterii (verilen veri) | Durum |
|---|---|
| Net kâr pozitif (ROA>0) | ✓ (her yıl; Q1 2026 dahil) |
| Faaliyet nakit > net kâr | ✓ (2023 1,14x; 2024 1,41x; 2025 1,63x; 2026 H1 1,05x) |
| ROA artışı (net marj trendi) | ✓ (10,0→12,7→16,6%) |
| Kalitesiz/nakit-öncesi kalemler | ✗ uyandırıcı: ertelenmiş vergi ağır |
| Borçluluk azalıyor mu | ✗ (2025→2026 finansal borç ↑ %44) |
| Cari oran iyileşiyor mu | ◐ (yıllık: 1,27→1,12 ✗; H1: 1,05→1,14 ✓) |
| Brüt marj artışı | ✓ (27,3→31,7%) |
| Varlık devir hızı / hisse adedi | **bilinmiyor** (veri eksik) |

- Bilinmeyen iki kriter hariç: ~6/9 → Piotroski 6 ≈ (hesap; kısmı).
- **Ana sinyal:** CFO kârı güvenilir aşan oranda destekliyor (yıllık ≥1,1x her yıl) — kâr büyük olasılıkla **nakde dönüşüyor**, makyajlı değil. İstisna: **H1 2023 CFO 27 mn** ve **H1 2024 CFO −2.565 mn** (pozitif kâr karşısında) → yıllık bazda kaliteli, ama **ilk 6 ay nakdi zayıf** (projeler H2'de nakit üretiyor). H1 2025 +18.0 mn ile değişmiş, 2026 H1 +15.2 mn sağlam kaldı.
- **Vergi ihtiyatlılığı:** yukarıda — 2024 kârının fin toplamca %40–45'i vergi kaynağı; 2025–26 için bu oran ~%12'ye gerilemiş → giderek daha temize yaklaşıyor.
- **Diğer faaliyet gelirleri** (3DD) kalite sorusu açıklı; yıllık dalgalanma ile marjı manipüle edebilir gibi — dip notlarla netleştirilmeli.
- **Hisse senedi seyrelmesi:** hisse başına kazanç kalemleri ekte 0,00 geliyor — birlikte değerlendirilemedi.

## Kaynak
- Tüm veriler: kullanıcı eki `bilanco-ozet.txt` (isyatirim.com.tr / `isyatirimhisse` çıkışı; 2023/3–2026/6, 14 çeyrek; mn TL).
- Enflasyon karşılaştırması: TCMB CPI (≈ tahmin, ek veri dışından tam seri yok — "≈" ile işaretli).
- **Erişilemeyen veri:** KAP dip notları, özkaynak serisi, amortisman/D&A, hisse adedi → ilgili metrikler "bulunamadı" olarak belirtildi, tahmin uydurulmadı.

*Bu analiz bilgilendirme amaçlıdır; yatırım tavsiyesi değildir.*''",
        'user_template': """VERI:
{finansal}
{haberler}
{kap_dipnotlar}

KURAL: Hicbir arac kullanma. Veri ekte: bilanco-ozet.txt. Marjlar, borç, cari oran, KAP dip notları, kâr kalitesi hesapla/degerlendir; sistem formatinda rapor sun. KAP dip notları bu turde erisilemedi — bunu not dus.""",
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
}

AGENT_CONFIGS = {
    'hendek-ajani': {'system': AGENT_PROMPTS['hendek-ajani']['system'], 'user_template': AGENT_PROMPTS['hendek-ajani']['user_template'], 'output_key': 'hendek'},
    'hikaye-ajani': {'system': AGENT_PROMPTS['hikaye-ajani']['system'], 'user_template': AGENT_PROMPTS['hikaye-ajani']['user_template'], 'output_key': 'hikaye'},
    'bilanco-ajani': {'system': AGENT_PROMPTS['bilanco-ajani']['system'], 'user_template': AGENT_PROMPTS['bilanco-ajani']['user_template'], 'output_key': 'bilanco'},
    'rakip-ajani': {'system': AGENT_PROMPTS['rakip-ajani']['system'], 'user_template': AGENT_PROMPTS['rakip-ajani']['user_template'], 'output_key': 'rakip'},
    'risk-ajani': {'system': AGENT_PROMPTS['risk-ajani']['system'], 'user_template': AGENT_PROMPTS['risk-ajani']['user_template'], 'output_key': 'risk'},
    'degerleme-ajani': {'system': AGENT_PROMPTS['degerleme-ajani']['system'], 'user_template': AGENT_PROMPTS['degerleme-ajani']['user_template'], 'output_key': 'degerleme'},
    'teknik-ajani': {'system': AGENT_PROMPTS['teknik-ajani']['system'], 'user_template': AGENT_PROMPTS['teknik-ajani']['user_template'], 'output_key': 'teknik'},
}

# Layer sıralaması (paralel çalışacak)
LAYER_ORDER = [
    'hendek-ajani',
    'hikaye-ajani', 
    'temel-ajani',
    'rakip-ajani',
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
        import time
        start = time.time()

        try:
            # Tek seferde formatla
            user_prompt = user_template.format(**self._get_veri_cache())

            # JSON Schema prompt'u ekle (Pydantic modelden)
            schema_prompt = ""
            if output_model:
                import json
                schema_prompt = f"\n\nCIKTI FORMATI (JSON Schema):\n{json.dumps(output_model.model_json_schema(), indent=2, ensure_ascii=False)}\n\nSADECE BU FORMATTA GEÇERLİ JSON ÜRET."

            enhanced_system = system_prompt + schema_prompt + "\n\nKURAL: SADECE GEÇERLİ JSON OBJESİ. HİÇBİR METİN, AÇIKLAMA, DÜŞÜNCE, MARKDOWN KOD BLOĞU YOK."

            # Use already imported call_nvidia from nvidia_client
            raw_output = await call_nvidia(enhanced_system, user_prompt)

            # GÜVENLİK: call_nvidia None döndürürse (timeout/retry sonrası implicit return)
            if raw_output is None:
                raw_output = "API_ERROR: call_nvidia returned None (timeout/retry exhausted)"

            # Parse JSON
            raw = raw_output.strip()
            if raw.startswith('```json'):
                raw = raw.split('```json')[1].split('```')[0]
            elif raw.startswith('```'):
                raw = raw.split('```')[1].split('```')[0]

            # Remove any leading/trailing whitespace
            raw = raw.strip()

            # Try to find JSON object in the response (in case there's extra text)
            if not raw.startswith('{'):
                # Try to find first {
                start_idx = raw.find('{')
                if start_idx != -1:
                    raw = raw[start_idx:]
                else:
                    raise ValueError(f"No JSON object found in response: {raw[:200]}")

            # Also handle case where there's trailing text after the JSON
            # Find the last } and truncate there
            if raw.endswith('}'):
                pass  # Already ends with }
            else:
                # Try to find the last } and truncate
                last_brace = raw.rfind('}')
                if last_brace != -1:
                    raw = raw[:last_brace + 1]

            parsed = json.loads(raw)

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
                "error": str(e),
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
            'hendek-ajani': MoatAnalysis,
            'hikaye-ajani': StorySector,
            'temel-ajani': FundamentalTable,
            'rakip-ajani': PeerComparison,
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

| Metrik | 2026/6 | 2025/12 | 2024/12 | 2023/12 | 2022/12 | 5P Trend |
|---|---:|---:|---:|---:|---:|---|
| FAVOK Marji % | {{ fundamental.periods[0].favok_margin_pct|default('-') }} | {{ fundamental.periods[1].favok_margin_pct|default('-') }} | {{ fundamental.periods[2].favok_margin_pct|default('-') }} | {{ fundamental.periods[3].favok_margin_pct|default('-') }} | {{ fundamental.periods[4].favok_margin_pct|default('-') }} | {{ fundamental.periods[0].trend|default('-') }} |
| Net Borç/FAVOK | {{ fundamental.periods[0].net_debt_favok|default('-') }} | {{ fundamental.periods[1].net_debt_favok|default('-') }} | {{ fundamental.periods[2].net_debt_favok|default('-') }} | {{ fundamental.periods[3].net_debt_favok|default('-') }} | {{ fundamental.periods[4].net_debt_favok|default('-') }} | {{ fundamental.periods[0].trend|default('-') }} |
| ROIC % | {{ fundamental.periods[0].roic_pct|default('-') }} | {{ fundamental.periods[1].roic_pct|default('-') }} | {{ fundamental.periods[2].roic_pct|default('-') }} | {{ fundamental.periods[3].roic_pct|default('-') }} | {{ fundamental.periods[4].roic_pct|default('-') }} | {{ fundamental.periods[0].trend|default('-') }} |
| Cari Oran | {{ fundamental.periods[0].current_ratio|default('-') }} | {{ fundamental.periods[1].current_ratio|default('-') }} | {{ fundamental.periods[2].current_ratio|default('-') }} | {{ fundamental.periods[3].current_ratio|default('-') }} | {{ fundamental.periods[4].current_ratio|default('-') }} | {{ fundamental.periods[0].trend|default('-') }} |
| FCF/Net Kar % | {{ fundamental.periods[0].fcf_net_income_pct|default('-') }} | {{ fundamental.periods[1].fcf_net_income_pct|default('-') }} | {{ fundamental.periods[2].fcf_net_income_pct|default('-') }} | {{ fundamental.periods[3].fcf_net_income_pct|default('-') }} | {{ fundamental.periods[4].fcf_net_income_pct|default('-') }} | {{ fundamental.periods[0].trend|default('-') }} |

---

## SENİN KAÇIRDIKLARIN (KAP Dip Notları)

{{ kap_notes }}

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

        # 2. Paralel Agent çalıştır
        self.agent_runner = ParallelAgentRunner(veri_cache)
        runner = self.agent_runner
        runner.set_data(veri_cache)
        agent_results = await runner.run_all_parallel()

        # 3. Sonuçları birleştir
        analysis = self._build_analysis(data, runner.results)

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
            fundamental=analysis['fundamental'],
        )

        # 5. Raporu kaydet
        os.makedirs("analiz-arşivi", exist_ok=True)
        report_path = f"analiz-arşivi/{symbol.replace('.IS','')}-{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  ✓ Rapor kaydedildi: {report_path}")

        return report_path

    def _prepare_veri_cache(self, data: CompleteData) -> dict:
        """Veriyi agent'lar için hazırla"""
        return {
            'finansal': self._format_finansal(data.financial),
            'sektor_rakip': self._format_sektor_rakip(data.peer),
            'kap_dipnotlar': data.kap_notes,
            'haberler': self._format_haberler(data.news),
            'fiyat_teknik': self._format_fiyat_teknik(data.technical),
        }

    def _format_finansal(self, financial: FundamentalTable) -> str:
        # Format financial data for agents
        if not financial.periods:
            return "Veri yok"
        parts = []
        for p in financial.periods:
            parts.append(f"Dönem: {p.period}, Satış: {p.sales or 'N/A'} Mn, FAVÖK Marj: {p.favok_margin_pct or 'N/A'}%, Net Marj: {p.net_margin_pct or 'N/A'}%, Net Borç/FAVÖK: {p.net_debt_favok or 'N/A'}x, Cari Oran: {p.current_ratio or 'N/A'}")
        return "\n".join(parts)

    def _format_sektor_rakip(self, peer: PeerComparison) -> str:
        if not peer.rows:
            return "Rakip verisi yok"
        rows = []
        for row in peer.rows:
            rows.append(f"{row.metric}: {row.target} vs {row.peers} | Sektör: {row.sector_median} | Kazanan: {row.winner}")
        return "\n".join(rows)

    def _format_haberler(self, news: list) -> str:
        if not news:
            return "Haber yok"
        return "\n".join([f"- {n.title}: {n.summary[:100]}... ({n.source})" for n in news[:10]])

    def _format_fiyat_teknik(self, technical: TechnicalPosition) -> str:
        if not technical:
            return "Teknik veri yok"
        return f"Fiyat: {technical.current_price:.2f} TL, RSI: {technical.rsi:.1f}, Trend: {technical.trend}, Destek: {technical.support:.2f}, Direnç: {technical.resistance:.2f}"

    def _build_analysis(self, data: CompleteData, agent_results: Dict[str, dict]) -> dict:
        """Agent sonuçlarını birleştir"""
        return {
            'verdict_emoji': '🟢' if 'GUCLU' in str(agent_results.get('hendek-ajani', {}).get('data', {})).upper() else ('🟡' if 'ORTA' in str(agent_results.get('hendek-ajani', {}).get('data', {})).upper() else '🔴'),
            'verdict': 'GÜÇLÜ' if 'GUCLU' in str(agent_results.get('hendek-ajani', {}).get('data', {})).upper() else ('NÖTR' if 'ORTA' in str(agent_results.get('hendek-ajani', {}).get('data', {})).upper() else 'RİSKLİ'),
            'rationale': 'Hendek güçlü, temel sağlam, değerleme ucuz',
            'moat': agent_results.get('hendek-ajani', {}).get('data', {}),
            'story': agent_results.get('hikaye-ajani', {}).get('data', {}),
            'fundamental': agent_results.get('bilanco-ajani', {}).get('data', {}),
            'technical': agent_results.get('teknik-ajani', {}).get('data', {}),
            'peer': agent_results.get('rakip-ajani', {}).get('data', {}),
            'risk': agent_results.get('risk-ajani', {}).get('data', {}),
            'valuation': agent_results.get('degerleme-ajani', {}).get('data', {}),
            'kap_notes': self._extract_kap_notes(),
        }

    def _extract_kap_notes(self) -> str:
        # KAP dip notlarını çıkar
        return "KAP dip notları analizi burada yer alacak"

    async def run_analysis(self, symbol: str, skip_data: bool = False) -> str:
        """Ana analiz fonksiyonu"""
        return await self.run_analysis(symbol, skip_data)


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