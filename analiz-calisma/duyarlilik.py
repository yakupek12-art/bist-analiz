#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duyarlılık / Risk Analizi Modülü — FX, faiz, petrol, ihale, kredi, makro şoklar
"""

import sys, os, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def calculate_sensitivities():
    """Duyarlılık katsayılarını hesapla (mock)"""
    return {
        'usd_try_elastisite': 0.15,  # %1 TL değerlenmesinde ciro %0.15 değişir
        'eur_try_elastisite': 0.05,
        'petrol_elastisite': -0.08,  # $1 petrol artışında FAVÖK %0.08 düşer
        'faiz_tl_elastisite': -0.03,  # 100bp faiz artışında FAVÖK %0.03 düşer
        'faiz_usd_elastisite': -0.01,
        'enflasyon_maliyet_yansitma': 0.6,  # Enflasyonun %60'ı maliyete yansır
        'ihale_bagimliligi': 0.35,  # Cironun %35'i devlet ihalesi
    }

def hedge_analysis():
    """Hedge programı analizi"""
    return {
        'petrol': {'oran': 0.75, 'arac': 'Swap/Futures', 'vade_ay': 18, 'etkinlik': 0.85, 'acik_pozisyon_mn_usd': 120},
        'usd_try': {'oran': 0.60, 'arac': 'Forward/Option', 'vade_ay': 12, 'etkinlik': 0.70, 'acik_pozisyon_mn_usd': 80},
        'eur_try': {'oran': 0.40, 'arac': 'Forward', 'vade_ay': 12, 'etkinlik': 0.60, 'acik_pozisyon_mn_usd': 30},
        'faiz': {'oran': 0.50, 'arac': 'IRS', 'vade_ay': 24, 'etkinlik': 0.75, 'acik_pozisyon_mn_usd': 50},
    }

def macro_shock_scenarios():
    """Makro şok senaryoları"""
    return {
        'tl_20_deger_kaybi': {'ciro_etkisi': 0.12, 'favok_etkisi': -0.08, 'net_kar_etkisi': -0.15, 'cari_etkisi_pp': -0.15},
        'petrol_95_plus': {'ciro_etkisi': -0.05, 'favok_etkisi': -0.12, 'net_kar_etkisi': -0.20, 'cari_etkisi_pp': -0.10},
        'faiz_300bp_tl': {'ciro_etkisi': 0.0, 'favok_etkisi': -0.09, 'net_kar_etkisi': -0.12, 'cari_etkisi_pp': -0.05},
        'petrol_95_tl_20': {'ciro_etkisi': -0.08, 'favok_etkisi': -0.25, 'net_kar_etkisi': -0.35, 'cari_etkisi_pp': -0.25},
        'ihale_50_kaybi': {'ciro_etkisi': -0.18, 'favok_etkisi': -0.30, 'net_kar_etkisi': -0.40, 'cari_etkisi_pp': -0.20},
        'resesyon_talp_20': {'ciro_etkisi': -0.20, 'favok_etkisi': -0.25, 'net_kar_etkisi': -0.35, 'cari_etkisi_pp': -0.15},
    }

def breaking_points():
    """Kırılma noktaları"""
    return {
        'cari_oran_alt_1': {'esik': 1.0, 'mevcut': 1.25, 'mesafe': 0.25, 'olasilik': 'Orta'},
        'net_borc_favok_ust_5': {'esik': 5.0, 'mevcut': 3.2, 'mesafe': 1.8, 'olasilik': 'Düşük'},
        'faiz_ortusme_alt_1_5': {'esik': 1.5, 'mevcut': 4.5, 'mesafe': 3.0, 'olasilik': 'Düşük'},
        'nakit_kisa_borc_alt_0_3': {'esik': 0.3, 'mevcut': 0.45, 'mesafe': 0.15, 'olasilik': 'Orta'},
        'ihale_payi_alt_20': {'esik': 0.20, 'mevcut': 0.35, 'mesafe': 0.15, 'olasilik': 'Orta'},
    }

def ihale_bagimliligi():
    return [
        {'tur': 'Rafineri İhalesi', 'yillik_hacim_mn_tl': 1200, 'ciro_payi': 0.25, 'kazanma_orani': 0.80, 'teklif_kazanan': 8},
        {'tur': 'Petrol Ürünleri Dağıtım', 'yillik_hacim_mn_tl': 450, 'ciro_payi': 0.10, 'kazanma_orani': 0.65, 'teklif_kazanan': 5},
    ]

def kredi_kosullari():
    return {
        'kisa_vadeli_borc_orani': 0.35,
        'doviz_cinsinden_borc_orani': 0.65,
        'sabit_degisken_faiz_orani': 0.60,  # Sabit %60
        'ortalama_vade_yil': 4.5,
        'kredi_notu_ulusal': 'AAA(tr)',
        'kredi_notu_uluslararasi': 'BBB-',
    }

def main():
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS'
    
    print(f"Duyarlılık analizi başlatılıyor: {symbol}")
    
    data = {
        'symbol': symbol,
        'elastisiteler': calculate_sensitivities(),
        'hedge': hedge_analysis(),
        'senaryolar': macro_shock_scenarios(),
        'kirilma_noktalari': breaking_points(),
        'ihale_bagimliligi': ihale_bagimliligi(),
        'kredi_kosullari': kredi_kosullari(),
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
    }
    
    os.makedirs('veri', exist_ok=True)
    save_json(data, f'veri/duyarlilik_veri.json')
    
    print("Duyarlılık analizi tamamlandı: veri/duyarlilik_veri.json")
    print(f"Elastisite: {data['elastisiteler']}")

if __name__ == '__main__':
    main()