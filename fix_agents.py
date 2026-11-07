path = r"C:\Users\PC\OneDrive\Belgeler\Varsayilan Proje\parallel_agents.py"
with open(path, "rb") as f:
    raw = f.read()
content = raw.decode("utf-8").replace("\r\n", "\n")

# 1. AGENT_PROMPTS'a 3 yeni agent ekle
new_agents = ''',

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

Sektor makro analizi yap. KURALLAR.md'deki sektor makro esiklerini (sektor_skoru <40 kriti, <60 uyarı; marj daralama 2pp+; ciro CAGR <5% dusuk, >15% yuksek) kullan. CIKTI: SADECE JSON.""",
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

Yonetim ve hakim ortak guvenilirligi analizi yap. KURALLAR.md'deki yonetim esiklerini (soz tutarliligi <50% kriti, <70% uyarı; YK bagimsizligi <33% kriti, <40% uyarı; net satim >10Mn TL kirmizi; cikar catismasi >10% kirmizi, >5% uyarı; yonetim skoru >=70 yesil, <40 kirmizi) kullan. CIKTI: SADECE JSON.""",
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

Sirketi sektor medyan ile karsilastir. KURALLAR.md'deki sektor karsilastirma esiklerini (FAVOK marj -2pp+, ROE -3pp+, ROIC -2pp+, Net Borc/FAVOK 1.5x+ kirmizi; pazar payi: sektor kazanirken sirket kaybederse kirmizi) kullan. CIKTI: SADECE JSON.""",
    },
'''

bulgu = '''        'user_template': """VERI:
        {fiyat_teknik}

        SADECE JSON CIKTI URET. Yukaridaki hesaplamalari TA-Lib ile yapip sonuclari JSON formatinda ver.
        Eger veri yetersizse ilgili alan icin null yaz.""",
    },

}'''

if bulgu not in content:
    print("HATA: AGENT_PROMPTS sonu bulunamadi")
    # Alternatif: tek basamakli '}' oncesine ekle
    alt = content.rfind("\n}\n")
    print("Son tek basamakli kapanis parantezi konumu:", alt)
else:
    content = content.replace(bulgu, bulgu.replace("}", new_agents + "}", 1))
    print("AGENT_PROMPTS guncellendi")

# 2. AGENT_CONFIGS'a 3 yeni girdi ekle
bulgu2 = "    'teknik-ajani': {'system': AGENT_PROMPTS['teknik-ajani']['system'], 'user_template': AGENT_PROMPTS['teknik-ajani']['user_template'], 'output_key': 'teknik'},\n},"
yeni2 = """    'teknik-ajani': {'system': AGENT_PROMPTS['teknik-ajani']['system'], 'user_template': AGENT_PROMPTS['teknik-ajani']['user_template'], 'output_key': 'teknik'},
    'sektor-ajani': {'system': AGENT_PROMPTS['sektor-ajani']['system'], 'user_template': AGENT_PROMPTS['sektor-ajani']['user_template'], 'output_key': 'sektor'},
    'yonetim-ajani': {'system': AGENT_PROMPTS['yonetim-ajani']['system'], 'user_template': AGENT_PROMPTS['yonetim-ajani']['user_template'], 'output_key': 'yonetim'},
    'sektor-karsilastirma-ajani': {'system': AGENT_PROMPTS['sektor-karsilastirma-ajani']['system'], 'user_template': AGENT_PROMPTS['sektor-karsilastirma-ajani']['user_template'], 'output_key': 'sektor_karsilastirma'},
},"""

if bulgu2 not in content:
    print("HATA: AGENT_CONFIGS sonu bulunamadi")
else:
    content = content.replace(bulgu2, yeni2, 1)
    print("AGENT_CONFIGS guncellendi")

# 3. LAYER_ORDER guncelle
bulgu3 = """LAYER_ORDER = [
    'hendek-ajani',
    'hikaye-ajani', 
    'temel-ajani',
    'rakip-ajani',
    'risk-ajani',
    'degerleme-ajani',
    'teknik-ajani'
]"""
yeni3 = """LAYER_ORDER = [
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
]"""

if bulgu3 not in content:
    print("HATA: LAYER_ORDER bulunamadi")
else:
    content = content.replace(bulgu3, yeni3, 1)
    print("LAYER_ORDER guncellendi")

# 4. OUTPUT_MODELS guncelle
bulgu4 = """        OUTPUT_MODELS = {
            'hendek-ajani': MoatAnalysis,
            'hikaye-ajani': StorySector,
            'temel-ajani': FundamentalTable,
            'rakip-ajani': PeerComparison,
            'risk-ajani': RiskAnalysis,
            'degerleme-ajani': ValuationAnalysis,
            'teknik-ajani': TechnicalPosition,
        }"""
yeni4 = """        OUTPUT_MODELS = {
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
        }"""

if bulgu4 not in content:
    print("HATA: OUTPUT_MODELS bulunamadi")
else:
    content = content.replace(bulgu4, yeni4, 1)
    print("OUTPUT_MODELS guncellendi")

with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print("ISLEM TAMAMLANDI")
