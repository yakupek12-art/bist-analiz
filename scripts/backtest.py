#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Modülü
Geçmiş analiz raporlarını (analiz-arşivi/) gerçek fiyat hareketleriyle karşılaştırır.
Karar kutusu (🟢🟡🔴) ile X gün sonrasındaki fiyat değişimini karşılaştırır.
"""
import json, os, re, glob
from datetime import datetime, timedelta


def kararlari_oku(klasor: str = "analiz-arşivi") -> list:
    """
    Arşivdeki tüm raporlardan karar kutusu ve tarihi çıkarır.
    Döndür: [{"symbol": "...", "tarih": "YYYY-MM-DD", "karar": "🟢/🟡/🔴"}, ...]
    """
    raporlar = []
    if not os.path.exists(klasor):
        return raporlar

    dosyalar = glob.glob(os.path.join(klasor, "*.md"))
    for dosya in dosyalar:
        try:
            with open(dosya, "r", encoding="utf-8") as f:
                icerik = f.read()

            # Dosya adından sembol ve tarih çıkar: HISSE-YYYY-MM-DD.md
            dosya_adi = os.path.basename(dosya)
            parcalar = dosya_adi.replace(".md", "").split("-")
            if len(parcalar) < 3:
                continue
            simbol = parcalar[0] + ".IS"
            tarih_str = "-".join(parcalar[1:4])  # YYYY-MM-DD

            # Karar kutusu ara: ## KARAR KUTUSU: 🟢 GÜÇLÜ
            karar_bul = re.search(r"KARAR KUTUSU:\s*([🟢🟡🔴])\s*(\w+)", icerik)
            if karar_bul:
                emoji = karar_bul.group(1)
                metin = karar_bul.group(2)
                raporlar.append({
                    "symbol": simbol,
                    "tarih": tarih_str,
                    "karar_emoji": emoji,
                    "karar_metin": metin,
                    "dosya": dosya
                })
        except Exception as e:
            print(f"[BACKTEST] Dosya okuma hatası ({dosya}): {e}")

    return raporlar


def fiyat_degisimini_al(symbol: str, baslangic_tarihi: str, gun_sayisi: int = 30) -> dict:
    """
    Belirli bir tarihten itibaren X gün sonrasındaki fiyat değişimini hesaplar.
    Yahoo Finance kullanır. Eğer veri yoksa None döner.
    """
    try:
        import yfinance as yf
        from datetime import datetime, timedelta

        baslangic = datetime.strptime(baslangic_tarihi, "%Y-%m-%d")
        bitis = baslangic + timedelta(days=gun_sayisi + 10)  # Hafta sonu.buffer

        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=baslangic_tarihi, end=bitis.strftime("%Y-%m-%d"))

        if hist.empty or len(hist) < 2:
            return {"baslangic_fiyat": None, "bitis_fiyat": None, "yuzde_degisim": None, "hata": "Veri yok"}

        baslangic_fiyat = float(hist["Close"].iloc[0])
        # En yakın günü bul (gun_sayisi sonra)
        hedef_tarih = baslangic + timedelta(days=gun_sayisi)
        uygun_gunler = [idx for idx in hist.index if idx >= hedef_tarih]
        if not uygun_gunler:
            return {"baslangic_fiyat": baslangic_fiyat, "bitis_fiyat": None, "yuzde_degisim": None, "hata": "Hedef tarih verisi yok"}

        bitis_fiyat = float(hist.loc[uygun_gunler[0], "Close"])
        yuzde = round(((bitis_fiyat - baslangic_fiyat) / baslangic_fiyat) * 100, 2)

        return {
            "baslangic_fiyat": round(baslangic_fiyat, 2),
            "bitis_fiyat": round(bitis_fiyat, 2),
            "yuzde_degisim": yuzde,
            "hata": None
        }
    except Exception as e:
        return {"baslangic_fiyat": None, "bitis_fiyat": None, "yuzde_degisim": None, "hata": str(e)}


def karari_degerle(karar_emoji: str, yuzde_degisim: float) -> str:
    """
    Karar ile gerçek sonuç karşılaştırılır.
    🟢 (Güçlü) → beklenti: artış
    🟡 (Nötr) → beklenti: yatay/az değişim
    🔴 (Riskli) → beklenti: düşüş
    """
    if yuzde_degisim is None:
        return "DEĞERLENEMEDİ"

    if karar_emoji == "🟢":
        if yuzde_degisim > 5:
            return "DOĞRU (Güçlü → Artış)"
        elif yuzde_degisim > -5:
            return "KISMI (Güçlü → Yatay)"
        else:
            return "YANLIŞ (Güçlü → Düşüş)"
    elif karar_emoji == "🟡":
        if abs(yuzde_degisim) <= 5:
            return "DOĞRU (Nötr → Yatay)"
        elif yuzde_degisim > 5:
            return "KISMI (Nötr → Artış)"
        else:
            return "KISMI (Nötr → Düşüş)"
    elif karar_emoji == "🔴":
        if yuzde_degisim < -5:
            return "DOĞRU (Riskli → Düşüş)"
        elif yuzde_degisim < 5:
            return "KISMI (Riskli → Yatay)"
        else:
            return "YANLIŞ (Riskli → Artış)"
    return "BİLINMIYOR"


def backtest_calistir(klasor: str = "analiz-arşivi", gun_sayisi: int = 30) -> dict:
    """
    Tüm arşiv raporları üzerinde backtest çalıştırır.
    """
    raporlar = kararlari_oku(klasor)
    sonuclar = []

    print(f"[BACKTEST] {len(raporlar)} rapor bulundu, {gun_sayisi} günlük dönüş analiz edilecek.\n")

    for rapor in raporlar:
        simbol = rapor["symbol"]
        tarih = rapor["tarih"]
        karar = rapor["karar_emoji"]

        fiyat_sonuc = fiyat_degisimini_al(simbol, tarih, gun_sayisi)
        degerleme = karari_degerle(karar, fiyat_sonuc.get("yuzde_degisim"))

        sonuclar.append({
            "symbol": simbol,
            "tarih": tarih,
            "karar": karar,
            "gun_sayisi": gun_sayisi,
            "baslangic_fiyat": fiyat_sonuc.get("baslangic_fiyat"),
            "bitis_fiyat": fiyat_sonuc.get("bitis_fiyat"),
            "yuzde_degisim": fiyat_sonuc.get("yuzde_degisim"),
            "sonuc": degerleme,
            "hata": fiyat_sonuc.get("hata")
        })

        print(f"  {simbol} | {tarih} | {karar} | {fiyat_sonuc.get('yuzde_degisim')}% | {degerleme}")

    # Özet
    dogru = sum(1 for s in sonuclar if s["sonuc"] and s["sonuc"].startswith("DOĞRU"))
    kismi = sum(1 for s in sonuclar if s["sonuc"] and s["sonuc"].startswith("KISMI"))
    yanlis = sum(1 for s in sonuclar if s["sonuc"] and s["sonuc"].startswith("YANLIŞ"))
    degerlenemedi = sum(1 for s in sonuclar if s["sonuc"] == "DEĞERLENEMEDİ")
    toplam = len(sonuclar)

    ozet = {
        "toplam_rapor": toplam,
        "dogru": dogru,
        "kismi": kismi,
        "yanlis": yanlis,
        "degerlenemedi": degerlenemedi,
        "dogru_orani": round(dogru / toplam * 100, 2) if toplam > 0 else 0,
        "gun_sayisi": gun_sayisi,
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    print("\n" + "=" * 60)
    print("BACKTEST ÖZETİ")
    print("=" * 60)
    print(f"Toplam rapor: {toplam}")
    print(f"Doğru: {dogru} ({ozet['dogru_orani']}%)")
    print(f":" + f" Kısmi: {kismi}")
    print(f"Yanlış: {yanlis}")
    print(f"Değerlenemedi: {degerlenemedi}")
    print("=" * 60)

    return {"ozet": ozet, "detaylar": sonuclar}


def kaydet_sonuc(sonuc: dict, dosya: str = "veri/backtest_sonuc.json"):
    os.makedirs(os.path.dirname(dosya), exist_ok=True)
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)
    print(f"\n[BACKTEST] Sonuç kaydedildi: {dosya}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backtest çalıştır")
    parser.add_argument("--klasor", default="analiz-arşivi", help="Arşiv klasörü")
    parser.add_argument("--gun", type=int, default=30, help="Gün sayısı")
    parser.add_argument("--kaydet", action="store_true", help="Sonucu dosyaya kaydet")
    args = parser.parse_args()

    sonuc = backtest_calistir(args.klasor, args.gun)
    if args.kaydet:
        kaydet_sonuc(sonuc)
