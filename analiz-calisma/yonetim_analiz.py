#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yönetim Analizi Modülü — KAP'tan CV, genel kurul tutanakları, hakim ortak bildirimleri
"""

import sys, os, json, re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def parse_kap_cv(company):
    """KAP'tan YK/YİK üyeleri CV'lerini çek"""
    pass  # pykap ile KAP'tan çekilecek

def parse_genel_kurul_tutanaklari(company):
    """Genel kurul tutanaklarını çek ve özetle"""
    pass

def parse_hakim_ortak_bildirimleri(company):
    """Hakim ortak bildirimlerini çek"""
    pass

def parse_yonetim_degisiklikleri(company):
    """Son 10 yl YK/YİK değişimlerini çek"""
    pass

def analyze_management():
    """Ana analiz fonksiyonu"""
    # Mock veri - gerçekte pykap ile çekilecek
    data = {
        'hukum_ortak': {
            'ad_soyad': 'Mehmet Yılmaz',
            'unvan': 'YK Başkanı & CEO',
            'hisse_payi': 0.12,
            'sektor_deneyimi_yil': 25,
            'egitim': 'İTÜ Makine Mühendisliği, MBA',
            'gecmis_roller': ['Genel Müdür', 'Operasyon Direktörü', 'Proje Yöneticisi']
        },
        'yk_uyeleri': [
            {'ad': 'Ahmet Demir', 'rol': 'Başkan', 'bagli': False, 'sektor_deneyimi': 20, 'cikar_catismasi': False},
            {'ad': 'Ayşe Kaya', 'rol': 'Üye', 'bagli': True, 'sektor_deneyimi': 15, 'cikar_catismasi': False},
            {'ad': 'Mehmet Öz', 'rol': 'Bağımsız Üye', 'bagli': False, 'sektor_deneyimi': 18, 'cikar_catismasi': False},
            {'ad': 'Fatma Şahin', 'rol': 'Bağımsız Üye', 'bagli': False, 'sektor_deneyimi': 22, 'cikar_catismasi': False},
        ],
        'hedefler_gerceklesme': [
            {'yil': 2020, 'hedef': 'Yılın %15 büyüme', 'gerceklesme': 'Tam', 'tutarlilik': 'Tutarlı'},
            {'yil': 2021, 'hedef': 'Yeni tesis açılımı', 'gerceklesme': 'Kısmi', 'tutarlilik': 'Kısmi'},
            {'yil': 2022, 'hedef': 'Borç/FAVOK 3x altına', 'gerceklesme': 'Hayır', 'tutarlilik': 'Kırdı'},
            {'yil': 2023, 'hedef': 'Temettü ödeme', 'gerceklesme': 'Tam', 'tutarlilik': 'Tutarlı'},
        ],
        'hisse_alim_satim': [
            {'tarih': '2023-Q1', 'islem': 'Alım', 'adet': 100000, 'fiyat': 125.50, 'deger': 12550000},
            {'tarih': '2023-Q3', 'islem': 'Alım', 'adet': 50000, 'fiyat': 138.20, 'deger': 6910000},
        ],
        'cikar_catismalari': {
            'iliski_taraf_islemleri': {'var_mi': True, 'hacim_mn_tl': 45, 'aciklama': 'Aile şirketleriyle lojistik hizmetleri'},
            'sermaye_yapisi_catismasi': {'var_mi': False, 'aciklama': ''},
            'sermaye_artirimi_dilalmesi': {'var_mi': False, 'aciklama': ''},
            'yonetim_ucreti_performans_bagi': {'var_mi': True, 'performans_bazli_oran': 0.35},
        },
        'yonetim_degisiklikleri': [
            {'yil': 2021, 'tur': 'CEO Değişikliği', 'eski': 'Ali Veli', 'yeni': 'Mehmet Yılmaz', 'neden': 'Emeklilik', 'etki': 'Pozitif'},
            {'yil': 2019, 'tur': 'YK Üyesi Ayrılığı', 'kisi': 'Can Duman', 'neden': 'İstifa', 'etki': 'Nötr'},
        ],
        'skor': {
            'hukum_ortak_deneyim': 18,
            'yk_bagimsizlik': 18,
            'soz_tutarliligi': 14,
            'hisse_alim_sinyali': 12,
            'cikar_catismasi_yoklugu': 12,
            'yonetim_kararliligi': 8,
            'toplam': 82
        }
    }
    
    return data

def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS'
    
    print(f"Yönetim analizi başlatılıyor: {symbol}")
    
    data = analyze_management()
    data['symbol'] = symbol
    data['analysis_date'] = datetime.now().strftime('%Y-%m-%d')
    
    os.makedirs('veri', exist_ok=True)
    save_json(data, f'veri/yonetim_veri.json')
    
    print("Yönetim analizi tamamlandı: veri/yonetim_veri.json")
    print(f"Yönetim Skoru: {data['skor']['toplam']}/100")

if __name__ == '__main__':
    main()