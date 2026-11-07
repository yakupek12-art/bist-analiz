#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Değerleme Modülü (Hendeksiz Şirketler) — NC>0, CFO>NC, ROA artış, Borç/Özkaynak düşüş, Cari düşüş
"""

import sys, os, json, math
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def calculate_wacc(rf, erp, beta, special_risk, kd, tax_rate, d_v_ratio):
    ke = rf + beta * erp + special_risk
    wacc = (1 - d_v_ratio) * ke + d_v_ratio * kd * (1 - tax_rate)
    return wacc, ke

def dcf_valuation(fcf, wacc, g, years=5):
    if wacc <= g:
        return {'error': 'WACC <= g'}
    pv_fcf = sum(fcf * (1.05)**i / (1 + wacc)**i for i in range(1, years + 1))
    fcf_terminal = fcf * (1.05)**years * (1 + g)
    tv = fcf_terminal / (wacc - g)
    pv_tv = tv / (1 + wacc)**years
    ev = pv_fcf + pv_tv
    return {'ev': ev, 'pv_fcf': pv_fcf, 'pv_tv': pv_tv, 'fair_value_per_share': None}

def percentile_rank(values, current):
    if not values or current is None:
        return None
    sorted_v = sorted([v for v in values if v is not None])
    if not sorted_v: return None
    count = sum(1 for v in sorted_v if v <= current)
    return round((count / len(sorted_v)) * 100, 1)

def safety_margin(fair, current):
    if fair and current:
        return round((fair - current) / fair * 100, 1)
    return None

def reverse_dcf(market_cap, net_debt, fcf, wacc, years=10):
    ev = market_cap + net_debt
    best_g, best_diff = None, float('inf')
    for g_test in [i * 0.001 for i in range(0, 101)]:
        if g_test >= wacc: continue
        pv = sum(fcf * (1.03)**i / (1 + wacc)**i for i in range(1, 11))
        if wacc > g_test:
            fcf_10 = fcf * (1.03)**10
            tv = fcf_10 * (1 + g_test) / (wacc - g_test)
            pv_tv = tv / (1 + wacc)**10
            total_ev = pv + pv_tv
            diff = abs(total_ev - ev)
            if diff < best_diff:
                best_diff, best_g = diff, g_test
    return {'implied_growth': best_g, 'ev': ev} if best_g is not None else None

def moatsiz_kontrol(finansal_veri):
    """Hendeksiz şirket için kalite kontrol listesi"""
    kontroller = {}
    
    # NC > 0
    nc = finansal_veri.get('net_kar', 0)
    kontroller['nc_pozitif'] = {'esik': '> 0', 'mevcut': nc, 'sonuc': nc > 0}
    
    # CFO > Net Kar
    cfo = finansal_veri.get('cfo', 0)
    nc = finansal_veri.get('net_kar', 1)
    cfo_nc_oran = cfo / nc if nc != 0 else 0
    kontroller['cfo_gt_nc'] = {'esik': 'CFO/NC > 1.0', 'mevcut': round(cfo_nc_oran, 2), 'sonuc': cfo_nc_oran > 1.0}
    
    # ROA Artışı (son 5 yl trendi)
    roa_trend = finansal_veri.get('roa_trend', 'artan')  # 'artan', 'azalan', 'sabit'
    kontroller['roa_artis'] = {'esik': 'ROA trendi artan', 'mevcut': roa_trend, 'sonuc': roa_trend == 'artan'}
    
    # Borç/Özkaynak Azalması
    de_trend = finansal_veri.get('de_trend', 'azalan')  # 'artan', 'azalan', 'sabit'
    kontroller['de_azalma'] = {'esik': 'D/E trendi azalan', 'mevcut': de_trend, 'sonuc': de_trend == 'azalan'}
    
    # Cari Oran ≥ 1.0 veya Artan
    cari = finansal_veri.get('cari_oran', 1.0)
    cari_trend = finansal_veri.get('cari_trend', 'artan')
    kontroller['cari_iyi'] = {'esik': 'Cari ≥ 1.0 ve artan', 'mevcut': round(cari, 2), 'sonuc': cari >= 1.0 and cari_trend != 'azalan'}
    
    # Sermaye Artırımı Yok (5 yl)
    sermaye_artirimi = finansal_veri.get('sermaye_artirimi_yok', True)
    kontroller['sermaye_artirimi_yok'] = {'esik': '5 yl sermaye artırımı yok', 'mevcut': sermaye_artirimi, 'sonuc': sermaye_artirimi}
    
    # Brüt Marj Artışı
    brut_marj_trend = finansal_veri.get('brut_marj_trend', 'artan')
    kontroller['brut_marj_artis'] = {'esik': 'Brüt marj trendi artan', 'mevcut': brut_marj_trend, 'sonuc': brut_marj_trend == 'artan'}
    
    # Varlık Devir Hızı Artışı
    asset_turnover_trend = finansal_veri.get('asset_turnover_trend', 'artan')
    kontroller['asset_turnover_artis'] = {'esik': 'Asset turnover artan', 'mevcut': asset_turnover_trend, 'sonuc': asset_turnover_trend == 'artan'}
    
    # Sonuç
    tum_yes = all(k['sonuc'] for k in kontroller.values())
    
    return {
        'kontroller': kontroller,
        'tum_kriterler_karsilandi': tum_yes,
        'karsilanmayan_sayi': sum(1 for k in kontroller.values() if not k['sonuc']),
    }

def simple_valuation(finansal_veri, piyasa_degeri, hisse_adedi, sektor_medyanlari):
    """Hendeksiz için basit değerleme"""
    nc = finansal_veri.get('net_kar', 0)
    cfo = finansal_veri.get('cfo', 0)
    favok = finansal_veri.get('favok', 0)
    ozkaynak = finansal_veri.get('ozkaynak', 0)
    nakit = finansal_veri.get('nakit', 0)
    net_borc = finansal_veri.get('net_borc', 0)
    
    sonuclar = {}
    
    # P/E (Sektör medyanı)
    if sektor_medyanlari.get('p_e') and nc:
        sonuclar['pe_sektor'] = round(sektor_medyanlari['p_e'] * nc / hisse_adedi, 2) if hisse_adedi else None
    
    # EV/FAVÖK (Sektör medyanı)
    if sektor_medyanlari.get('ev_favok') and favok:
        ev = sektor_medyanlari['ev_favok'] * favok
        equity = ev - net_borc
        sonuclar['ev_favok_sektor'] = round(equity / hisse_adedi, 2) if hisse_adedi else None
    
    # P/B (Özkaynak bazlı)
    if ozkaynak and hisse_adedi:
        sonuclar['pb_ozkaynak'] = round(ozkaynak / hisse_adedi, 2)
    
    # Nakit Temelli (Nakit + 5 yl CFO ort.)
    cfo_5y_ort = finansal_veri.get('cfo_5y_ort', cfo)
    nakit_toplam = nakit + cfo_5y_ort * 5
    sonuclar['nakit_temelli'] = round(nakit_toplam / hisse_adedi, 2) if hisse_adedi else None
    
    # Fair Value Aralığı
    degerler = [v for v in sonuclar.values() if v is not None]
    if degerler:
        sonuclar['fair_aralik'] = {'min': min(degerler), 'max': max(degerler), 'ortalama': round(sum(degerler)/len(degerler), 2)}
    
    return sonuclar

def main():
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS'
    
    print(f"Moatsız değerleme başlatılıyor: {symbol}")
    
    # Mock finansal veri
    finansal_veri = {
        'net_kar': 5000,
        'cfo': 6500,
        'favok': 8000,
        'ozkaynak': 25000,
        'nakit': 3000,
        'net_borc': 12000,
        'roa_trend': 'artan',
        'de_trend': 'azalan',
        'cari_oran': 1.35,
        'cari_trend': 'artan',
        'sermaye_artirimi_yok': True,
        'brut_marj_trend': 'artan',
        'asset_turnover_trend': 'artan',
        'cfo_5y_ort': 6200,
    }
    
    sektor_medyanlari = {'p_e': 6.5, 'ev_favok': 7.0}
    piyasa_degeri = 45000
    hisse_adedi = 2500
    
    # Hendeksiz kontrol
    moatsiz = moatsiz_kontrol(finansal_veri)
    
    # Basit değerleme
    degerleme = simple_valuation(finansal_veri, piyasa_degeri, hisse_adedi, sektor_medyanlari)
    
    # Fair value aralığı
    if 'fair_aralik' in degerleme:
        fair_min = degerleme['fair_aralik']['min']
        fair_max = degerleme['fair_aralik']['max']
        fair_ort = degerleme['fair_aralik']['ortalama']
    else:
        fair_min = fair_max = fair_ort = None
    
    data = {
        'symbol': symbol if len(sys.argv) > 1 else 'TUPRS',
        'hendeksiz_kontrol': moatsiz,
        'degerleme': degerleme,
        'fair_value_aralik': {'min': fair_min, 'max': fair_max, 'ortalama': fair_ort},
        'mevcut_fiyat': 180.0,  # Mock
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
    }
    
    os.makedirs('veri', exist_ok=True)
    save_json(data, f'veri/degerleme_moatsiz.json')
    
    print("Moatsız değerleme tamamlandı: veri/degerleme_moatsiz.json")
    print(f"Tüm kriterler karşılandı mı? {moatsiz['tum_kriterler_karsilandi']}")
    print(f"Fair Value Aralığı: {fair_min} - {fair_max}")

if __name__ == '__main__':
    main()