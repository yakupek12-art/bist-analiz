#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kısa Pozisyon & Kurumsal Sahiplik Takibi
KAP'tan %5 üzeri kurumsal sahiplik değişiklikleri ve kısa pozisyon verilerini çeker.
"""
import json, os, re
from datetime import datetime


def kisa_pozisyon_kontrol(symbol: str, veri_klasoru: str = "veri") -> dict:
    """
    Kısa pozisyon verisini kontrol eder.
    Dosya: veri/{symbol}_kisapozisyon.json
    İçerik: {"kisa_pozisyon_orani": 2.5, "degisim": +0.5}
    """
    dosya = os.path.join(veri_klasoru, f"{symbol.replace('.IS','')}_kisapozisyon.json")
    sonuc = {
        "symbol": symbol,
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "kisa_pozisyon_orani": None,
        "degisim": None,
        "uyari": None
    }

    if os.path.exists(dosya):
        with open(dosya, "r", encoding="utf-8") as f:
            veri = json.load(f)
        sonuc["kisa_pozisyon_orani"] = veri.get("kisa_pozisyon_orani")
        sonuc["degisim"] = veri.get("degisim")

        oran = veri.get("kisa_pozisyon_orani")
        degisim = veri.get("degisim")

        if oran is not None and oran > 5:
            sonuc["uyari"] = f"Kısa pozisyon oranı %{oran:.2f} — yükseklik riski"
        if degisim is not None and degisim > 1:
            sonuc["uyari"] = f"Kısa pozisyon %{degisim:+.2f} pp artış — dikkat"

    return sonuc


def kurumsal_sahiplik_kontrol(symbol: str, veri_klasoru: str = "veri") -> dict:
    """
    Kurumsal sahiplik değişikliğini kontrol eder (%5 üzeri bildirimler).
    Dosya: veri/{symbol}_sahiplik.json
    İçerik: [{"sahibi": "...", "orani": 7.2, "degisim": "+1.5", "tarih": "..."}, ...]
    """
    dosya = os.path.join(veri_klasoru, f"{symbol.replace('.IS','')}_sahiplik.json")
    sonuc = {
        "symbol": symbol,
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "bildirimler": [],
        "uyari": None
    }

    if os.path.exists(dosya):
        with open(dosya, "r", encoding="utf-8") as f:
            bildirimler = json.load(f)
        sonuc["bildirimler"] = bildirimler

        buyuk_degisimler = [
            b for b in bildirimler
            if isinstance(b, dict) and abs(float(str(b.get("degisim", "0")).replace("+", ""))) >= 1.0
        ]
        if buyuk_degisimler:
            sonuc["uyari"] = f"{len(buyuk_degisimler)} kurumsal sahilikte %1 üzeri değişiklik var"

    return sonuc


def birlestir_rapor(symbol: str, veri_klasoru: str = "veri") -> dict:
    """
    Kısa pozisyon ve kurumsal sahiplik verilerini birleştirip rapor döner.
    """
    kisa = kisa_pozisyon_kontrol(symbol, veri_klasoru)
    sahiplik = kurumsal_sahiplik_kontrol(symbol, veri_klasoru)

    return {
        "symbol": symbol,
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "kisa_pozisyon": kisa,
        "kurumsal_sahiplik": sahiplik,
        "toplam_uyari": sum(1 for x in [kisa, sahiplik] if x.get("uyari"))
    }


def kaydet_sonuc(sonuc: dict, klasor: str = "veri"):
    os.makedirs(klasor, exist_ok=True)
    symbol_clean = sonuc["symbol"].replace(".IS", "")
    dosya = os.path.join(klasor, f"{symbol_clean}_sahiplik_kisapozisyon.json")
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)
    print(f"[SAHİPLİK/KISA POZİSYON] Kaydedildi: {dosya}")


if __name__ == "__main__":
    # Test
    test_kisa = {
        "kisa_pozisyon_orani": 6.3,
        "degisim": 1.2
    }
    test_sahiplik = [
        {"sahibi": "ABC Kurumsal", "orani": 8.1, "degisim": "+2.5", "tarih": "2026-10-20"},
        {"sahibi": "DEF Yatırım", "orani": 5.4, "degisim": "-0.3", "tarih": "2026-10-18"}
    ]

    # Test dosyalarını yaz
    os.makedirs("veri", exist_ok=True)
    with open("veri/TEST_kisapozisyon.json", "w", encoding="utf-8") as f:
        json.dump(test_kisa, f, ensure_ascii=False, indent=2)
    with open("veri/TEST_sahiplik.json", "w", encoding="utf-8") as f:
        json.dump(test_sahiplik, f, ensure_ascii=False, indent=2)

    sonuc = birlestir_rapor("TEST.IS", "veri")
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    kaydet_sonuc(sonuc, "veri")
