"""
KURALLAR.md'deki eşikleri kodla karşılaştırır.
Hangi eşikler implementasyonunda var, hangileri eksik raporlar.
"""
import re

KURALLAR_PATH = r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\KURALLAR.md"
CODE_PATHS = [
    r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\parallel_agents.py",
    r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\data_layer.py",
    r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\scripts\kural_motoru.py",
    r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\run_valuation.py",
    r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\degerleme.py",
]

all_code = ""
for p in CODE_PATHS:
    try:
        with open(p, "r", encoding="utf-8") as f:
            all_code += f.read() + "\n"
    except Exception:
        pass

with open(KURALLAR_PATH, "r", encoding="utf-8") as f:
    kurallar = f.read()

anahtar_kelimeler = [
    "sektor_skoru", "marj_daralama", "ciro_cagr", "soz_tutarliligi",
    "yk_bagimsizlik", "hakim_ortak", "cikar_catismasi", "yonetim_skoru",
    "hendek_skoru", "fiyatlama_gucu", "gecis_maliyeti", "pazar_payi",
    "roic_farki", "roe_farki", "cari_oran", "net_borc_favok",
    "faiz_ortusme", "nakit_kisa", "ihale_payi", "guvenlik_marji",
    "carpan_percentil", "piotroski", "beneish", "ertelenmis_vergi",
    "rsi", "macd", "adx", "rr_min", "max_pozisyon", "kap_dip_notlari",
]

print("KURALLAR.md EŞİK AUDIT RAPORU")
print("=" * 60)

bulunan = []
eksik = []
for ak in anahtar_kelimeler:
    if ak.lower() in all_code.lower():
        bulunan.append(ak)
    else:
        eksik.append(ak)

print("\nKODDA BULUNAN ({}):".format(len(bulunan)))
for b in bulunan:
    print("  - {}".format(b))

print("\nKODDA EKSIK ({}):".format(len(eksik)))
for e in eksik:
    print("  - {}".format(e))

print("\n" + "=" * 60)
print("NOT: Bu audit sadece anahtar kelime tabanlıdır.")
print("     Gerçek eşik değerlerinin kodda %100 aynı olup olmadığını")
print("     manuel doğrulamak gerekir.")
print("=" * 60)
