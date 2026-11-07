#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sektör Analizi Modülü — Sektör para akışı, peer medyanları, trendler
"""

import sys, os, json, csv, math
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def load_bilanco_csv(symbol, csv_dir='veri'):
    """Bilanço CSV'den sektör peer verilerini çıkar"""
    pass  # Gerçek implementasyonda borsapy/isyatirimhisse kullanılacak

def get_sector_peers(symbol):
    """Sektör peer listesini al (borsapy ile)"""
    # Basit mapping - gerçekte borsapy.get_sector_stocks() kullanılacak
    sector_mapping = {
        'TUPRS': ['TUPRS', 'PETKM', 'THYAO', 'PGSUS'],  # Rafineri + Ulaşım
        'THYAO': ['THYAO', 'PGSUS', 'AIRPORT', 'HAVA'],  # Havacılık
        'SISE': ['SISE', 'KCHOL', 'ECILC', 'AGHOL'],  # Cam/Kimya
        'EREGL': ['EREGL', 'ISDMR', 'KRDMD', 'KCAER'],  # Demir/Çelik
        'ASELS': ['ASELS', 'OTOKAR', 'PNKRT', 'TKFEN'],  # Savunma
        'AKBNK': ['AKBNK', 'GARAN', 'ISCTR', 'YKBNK', 'VAKBN'],  # Bankacılık
        'GARAN': ['GARAN', 'AKBNK', 'ISCTR', 'YKBNK', 'VAKBN'],
    }
    return sector_mapping.get(symbol.replace('.IS', ''), [symbol])

def calculate_sector_medians(peer_data):
    """Peer grubu medyanlarını hesapla"""
    metrics = ['cagr_ciro', 'cagr_net_kar', 'favok_marj', 'net_marj', 
               'roe', 'roic', 'net_borc_favok', 'cari_oran', 'p_e', 'ev_favok']
    
    medians = {}
    for m in metrics:
        values = [d.get(m) for d in peer_data if d.get(m) is not None]
        if values:
            sorted_v = sorted(values)
            n = len(sorted_v)
            medians[m] = sorted_v[n//2] if n % 2 == 1 else (sorted_v[n//2-1] + sorted_v[n//2]) / 2
        else:
            medians[m] = None
    return medians

def analyze_sector_trends(peer_data, years=5):
    """Sektör trendlerini analiz et"""
    trends = {}
    for peer in peer_data:
        symbol = peer.get('symbol')
        if not symbol: continue
        # Her peer için 5 yl trendi hesapla
        pass
    return trends

def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS'
    
    print(f"Sektör analizi başlatılıyor: {symbol}")
    
    # 1. Peer listesi al
    peers = get_sector_peers(symbol)
    print(f"Peer grubu: {peers}")
    
    # 2. Her peer için veri topla (basit mock veri - gerçekte isyatirimhisse/borsapy)
    peer_data = []
    for p in peers:
        peer_data.append({
            'symbol': p,
            'cagr_ciro': 0.15,
            'cagr_net_kar': 0.20,
            'favok_marj': 0.22,
            'net_marj': 0.12,
            'roe': 0.25,
            'roic': 0.18,
            'net_borc_favok': 2.5,
            'cari_oran': 1.5,
            'p_e': 6.5,
            'ev_favok': 7.0,
        })
    
    # 3. Sektör medyanları
    medians = calculate_sector_medians(peer_data)
    
    # 4. Sektör analizi çıktısı
    output = {
        'symbol': symbol,
        'sector': 'Rafineri/Petrol',  # Gerçekte BIST sektör indeksinden alınacak
        'peers': peers,
        'peer_data': peer_data,
        'medians': medians,
        'sector_score': 75,  # 0-100 arası
        'trend': 'Pozitif',
        'shock_resilience': 'Orta',
        'analysis_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    os.makedirs('veri', exist_ok=True)
    save_json(output, f'veri/sektor_veri.json')
    
    # Peer karşılaştırma dosyası
    save_json({
        'symbol': symbol,
        'peers': peers,
        'medians': medians,
        'peer_data': peer_data
    }, 'veri/sektor_karsilastirma.json')
    
    # Peer listesi txt
    with open('veri/sektor_peerler.txt', 'w', encoding='utf-8') as f:
        for p in peers:
            f.write(f"{p}\n")
    
    print("Sektör analizi tamamlandı: veri/sektor_veri.json, veri/sektor_karsilastirma.json")
    print(f"Sektör Medyanlar: {medians}")

if __name__ == '__main__':
    main()