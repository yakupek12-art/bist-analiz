path = r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\parallel_agents.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the end of AGENT_PROMPTS - look for the last agent block closing
anchor = "Eger veri yetersizse ilgili alan icin null yaz.\"\"\",\n    },\n\n}"

new_agents = ''',

    'sektor-ajani': {
        'name': 'sektor-ajani',
        'desc': 'Katman 1: Sektor Makro Analizi',
        'system': '''Sen BIST sektor makro analistisin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "sektor_skoru": 65,
  "marj_trendi": "DARALMA|GENISLEME|STABIL",
  "marj_daralama_pp": 2.5,
  "sok_dayanikliligi": "YUKSEK|ORTA|DUSUK",
  "ciro_cagr_5y": 8.5,
  "sektor_onerisi": "...",
  "riskler": ["..."]
}''',
        'user_template': '''VERI:
{sektor_veri}
{makro_veri}

Sektor makro analizi yap. KURALLAR.md'deki sektor makro esiklerini kullan. CIKTI: SADECE JSON.''',
    },

    'yonetim-ajani': {
        'name': 'yonetim-ajani',
        'desc': 'Katman 5: Yonetim / Hakim Ortak Guvenilirligi',
        'system': '''Sen yonetim kalitesi analistisin. CIKTI: SADECE JSON.

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
}''',
        'user_template': '''VERI:
{yonetim_veri}

Yonetim ve hakim ortak guvenilirligi analizi yap. KURALLAR.md'deki yonetim esiklerini kullan. CIKTI: SADECE JSON.''',
    },

    'sektor-karsilastirma-ajani': {
        'name': 'sektor-karsilastirma-ajani',
        'desc': 'Katman 6: Sektor Ortalamasi vs Sirket',
        'system': '''Sen sektor karsilastirma analistisin. CIKTI: SADECE JSON.

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
}''',
        'user_template': '''VERI:
{sektor_karsilastirma_veri}
{finansal}

Sirketi sektor medyan ile karsilastir. KURALLAR.md'deki sektor karsilastirma esiklerini kullan. CIKTI: SADECE JSON.''',
    },
}'''

if anchor not in content:
    print("HATA: AGENT_PROMPTS sonu bulunamadi")
else:
    content = content.replace(anchor, anchor.replace("}", new_agents + "}", 1))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("AGENT_PROMPTS guncellendi - 3 yeni agent eklendi")
