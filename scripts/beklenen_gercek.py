#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beklenen vs Gerçek Karşılaştırma Modülü
İş Yatırım ve diğer aracı kurumların beklenti bilançolarını gerçek verilerle karşılaştırır.
"""
import json, os, re
from datetime import datetime


def bekleme_karsilastir(symbol: str, beklenen_veri: dict, gerçek_veri: dict) -> dict:
    """
    Beklenen ve gerçek finansal verileri karşılaştırır.
    
    Parametreler:
        symbol: Hisse senedi sembolü (örn: AKSA.IS)
        beklenen_veri: Aracı kurumun tahmin ettiği veriler (dict)
        gerçek_veri: Gerçekleşen bilanço verileri (dict)
    
    Döndürür:
        dict: Karşılaştırma sonuçları (farklar, yüzde farklar, durum)
    """
    sonuc = {
        "symbol": symbol,
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "karsilastirma": [],
        "ozet": ""
    }

    # Karşılaştırılacak anahtarlar (beklenen, gerçek, birim, açıklama)
    anahtarlar = [
        ("satis", "Satış Gelirleri", "Mn TL"),
        ("favok", "FAVÖK", "Mn TL"),
        ("net_kar", "Net Kar", "Mn TL"),
        ("favok_marj", "FAVÖK Marjı", "%"),
        ("net_marj", "Net Marj", "%"),
    ]

    for key, ad, birim in anahtarlar:
        beklenen = beklenen_veri.get(key)
        gerçek = gerçek_veri.get(key)

        if beklenen is None or gerçek is None:
            continue

        try:
            beklenen_f = float(beklenen)
            gerçek_f = float(gerçek)
            fark = gerçek_f - beklenen_f
            yuzde_fark = (fark / beklenen_f * 100) if beklenen_f != 0 else 0

            if abs(yuzde_fark) < 2:
                durum = "BEKLENIĞE UYGUN"
            elif yuzde_fark > 10:
                durum = "ÇOK İYİ"
            elif yuzde_fark > 2:
                durum = "İYİ"
            elif yuzde_fark < -10:
                durum = "ÇOK KÖTÜ"
            elif yuzde_fark < -2:
                durum = "KÖTÜ"
            else:
                durum = "NORMAL"

            sonuc["karsilastirma"].append({
                "metrik": ad,
                "beklenen": round(beklenen_f, 2),
                "gercek": round(gerçek_f, 2),
                "fark": round(fark, 2),
                "yuzde_fark": round(yuzde_fark, 2),
                "birim": birim,
                "durum": durum
            })
        except (ValueError, TypeError):
            continue

    # Özet metin
    iyi = [k for k in sonuc["karsilastirma"] if k["durum"] in ("ÇOK İYİ", "İYİ")]
    kotu = [k for k in sonuc["karsilastirma"] if k["durum"] in ("ÇOK KÖTÜ", "KÖTÜ")]

    if len(iyi) > len(kotu):
        sonuc["ozet"] = f"{symbol}: Genel olarak beklentiyi {len(iyi)} metrikte aştı, {len(kotu)} metrikte tamamladı."
    elif len(kotu) > len(iyi):
        sonuc["ozet"] = f"{symbol}: Genel olarak beklentinin altında. {len(kotu)} metrikte beklemeyen sonuç."
    else:
        sonuc["ozet"] = f"{symbol}: Beklenenle neredeyse paralel. {len(iyi)} iyi, {len(kotu)} kötü metrik."

    return sonuc


def dosyadan_yukle(symbol: str, klasor: str = "veri") -> tuple:
    """
    Belirtilen klasörden beklenen ve gerçek veri dosyalarını yükler.
    Dosya adları: {symbol}_beklenen.json, {symbol}_gercek.json
    """
    beklenen_path = os.path.join(klasor, f"{symbol.replace('.IS','')}_beklenen.json")
    gercek_path = os.path.join(klasor, f"{symbol.replace('.IS','')}_gercek.json")

    beklenen = {}
    gerçek = {}

    if os.path.exists(beklenen_path):
        with open(beklenen_path, "r", encoding="utf-8") as f:
            beklenen = json.load(f)

    if os.path.exists(gercek_path):
        with open(gercek_path, "r", encoding="utf-8") as f:
            gerçek = json.load(f)

    return beklenen, gerçek


def kaydet_sonuc(sonuc: dict, klasor: str = "veri"):
    """Karşılaştırma sonucunu JSON dosyasına kaydeder."""
    os.makedirs(klasor, exist_ok=True)
    symbol_clean = sonuc["symbol"].replace(".IS", "")
    dosya = os.path.join(klasor, f"{symbol_clean}_beklenen_gercek.json")
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)
    print(f"[BEKLENEN/GERÇEK] Kaydedildi: {dosya}")


if __name__ == "__main__":
    # Test
    test_beklenen = {
        "satis": 1000,
        "favok": 200,
        "net_kar": 100,
        "favok_marj": 20.0,
        "net_marj": 10.0
    }
    test_gercek = {
        "satis": 1050,
        "favok": 180,
        "net_kar": 90,
        "favok_marj": 17.1,
        "net_marj": 8.6
    }

    sonuc = bekleme_karsilastir("TEST.IS", test_beklenen, test_gercek)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    kaydet_sonuc(sonuc)
