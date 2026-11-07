#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kural Motoru - Basit versiyon"""
import os, sys, json, re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_symbol(symbol):
    """Tek hisse için kural kontrolü - KURALLAR.md'deki tüm eşikleri kontrol eder."""
    symbol_clean = symbol.replace(".IS", "")
    alerts = []

    # ===== KAP DIP NOTLARI =====
    kap_path = f"analiz-calisma/{symbol_clean}-veri/kap-dip-notlar/kap-dip-notlar.json"
    if os.path.exists(kap_path):
        with open(kap_path, "r", encoding="utf-8") as f:
            kap = json.load(f)
        for disc in kap.get("disclosures", []):
            findings = disc.get("findings", {})
            for kw in ["teminat", "rehin", "ipotek", "dava", "ilgili_taraf", "kambiyo", "hedge", "musteri_yogunlugu", "tedarikci", "ertelenmis_vergi", "taahhut", "sermaye_artirimi"]:
                if kw in findings and findings[kw] > 0:
                    alerts.append({
                        "type": "kap_dip_not",
                        "severity": "warning",
                        "symbol": symbol,
                        "message": f"KAP dip notu: {kw} ({findings[kw]} kez geciyor) - {disc.get('title','')[:60]}"
                    })

    # ===== BILANÇO / FINANSAL =====
    bilanco_path = f"analiz-calisma/{symbol_clean}-veri/bilanco-ham.csv"
    if os.path.exists(bilanco_path):
        import csv
        with open(bilanco_path, "r", encoding="utf-8-sig") as f:
            first = f.readline().strip()
            cols = [c.strip().strip('"') for c in first.split(",")]
            reader = csv.DictReader(f, fieldnames=cols)
            rows = list(reader)
        if rows:
            latest = rows[0]
            def get_val(code):
                for r in rows:
                    if r.get("FINANCIAL_ITEM_CODE") == code:
                        v = r.get(list(cols)[-1], "0") if len(cols) > 1 else "0"
                        try: return float(str(v).replace(",", "").strip())
                        except: return 0
                return 0

            # Cari Oran < 1.0 kirmizi, < 1.2 sari
            cari = get_val("1AA") / max(get_val("2AA"), 1)
            if cari < 1.0:
                alerts.append({"type": "cari_oran", "severity": "kritik", "symbol": symbol, "message": f"Cari oran {cari:.2f} < 1.0 (kritik)"})
            elif cari < 1.2:
                alerts.append({"type": "cari_oran", "severity": "uyari", "symbol": symbol, "message": f"Cari oran {cari:.2f} < 1.2 (uyari)"})

            # Net Borc/FAVOK > 5 kirmizi, > 3 sari
            favok = get_val("3DF")
            if favok > 0:
                nb_favok = (get_val("2AA") + get_val("2BA") - get_val("1AA")) / favok
                if nb_favok > 5.0:
                    alerts.append({"type": "net_borc_favok", "severity": "kritik", "symbol": symbol, "message": f"Net Borc/FAVOK {nb_favok:.2f}x > 5x (kritik)"})
                elif nb_favok > 3.0:
                    alerts.append({"type": "net_borc_favok", "severity": "uyari", "symbol": symbol, "message": f"Net Borc/FAVOK {nb_favok:.2f}x > 3x (uyari)"})

            # Nakit/Kisa vadeli borc < 0.3 kirmizi, < 0.5 sari
            nk = get_val("1AA") / max(get_val("2AA"), 1)
            if nk < 0.3:
                alerts.append({"type": "nakit_kisa", "severity": "kritik", "symbol": symbol, "message": f"Nakit/KisaVadeBorc {nk:.2f} < 0.3 (kritik)"})
            elif nk < 0.5:
                alerts.append({"type": "nakit_kisa", "severity": "uyari", "symbol": symbol, "message": f"Nakit/KisaVadeBorc {nk:.2f} < 0.5 (uyari)"})

            # Ertelenmis vergi payi > 30% sari, > 50% kirmizi
            ni = get_val("3Z")
            ev = get_val("1BJ") or 0
            if ni > 0 and ev / ni > 0.30:
                sev = "kritik" if ev / ni > 0.50 else "uyari"
                alerts.append({"type": "ertelenmis_vergi", "severity": sev, "symbol": symbol, "message": f"Ertelenmis vergi/nk {ev/ni:.2f}"})

    # ===== DEĞERLEME =====
    degerleme_path = f"analiz-calisma/{symbol_clean}-veri/degerleme.json"
    if os.path.exists(degerleme_path):
        with open(degerleme_path, "r", encoding="utf-8") as f:
            deg = json.load(f)
        v = deg.get("valuation", {})
        # Guvenlik marji < 10 kritik, < 20 sari
        sm = v.get("guvenlik_marji", 100)
        if sm < 10:
            alerts.append({"type": "guvenlik_marji", "severity": "kritik", "symbol": symbol, "message": f"Guvenlik marji %{sm:.1f} < 10 (kritik)"})
        elif sm < 20:
            alerts.append({"type": "guvenlik_marji", "severity": "uyari", "symbol": symbol, "message": f"Guvenlik marji %{sm:.1f} < 20 (uyari)"})
        # Carpan percentile > 80 kritik, > 60 sari
        cp = v.get("carpan_percentil", 0)
        if cp > 80:
            alerts.append({"type": "carpan_percentil", "severity": "kritik", "symbol": symbol, "message": f"Carpan percentil %{cp:.1f} > 80 (kritik)"})
        elif cp > 60:
            alerts.append({"type": "carpan_percentil", "severity": "uyari", "symbol": symbol, "message": f"Carpan percentil %{cp:.1f} > 60 (uyari)"})

    # ===== TEKNIK =====
    fiyat_path = f"analiz-calisma/{symbol_clean}-veri/fiyat-ozet.json"
    if os.path.exists(fiyat_path):
        with open(fiyat_path, "r", encoding="utf-8") as f:
            fiyat = json.load(f)
        change = fiyat.get("change_pct", 0)
        if change >= 5:
            alerts.append({"type": "fiyat_yukselis", "severity": "info", "symbol": symbol, "message": f"{symbol} +%{change:.1f} yukselis"})
        elif change <= -5:
            alerts.append({"type": "fiyat_dusus", "severity": "warning", "symbol": symbol, "message": f"{symbol} %{abs(change):.1f} dusus"})

        # RSI > 70 asi alim, < 30 asi satim (uyari)
        rsi = fiyat.get("rsi")
        if rsi:
            if rsi > 70:
                alerts.append({"type": "rsi", "severity": "uyari", "symbol": symbol, "message": f"RSI {rsi:.1f} > 70 (asi alim)"})
            elif rsi < 30:
                alerts.append({"type": "rsi", "severity": "uyari", "symbol": symbol, "message": f"RSI {rsi:.1f} < 30 (asi satim)"})

    # ===== HENDEK SKORU =====
    hendek_path = f"analiz-calisma/{symbol_clean}-veri/hendek_skor.json"
    if os.path.exists(hendek_path):
        with open(hendek_path, "r", encoding="utf-8") as f:
            hendek = json.load(f)
        skor = hendek.get("skor", 0)
        if skor < 30:
            alerts.append({"type": "hendek_skoru", "severity": "kritik", "symbol": symbol, "message": f"Hendek skoru {skor}/100 < 30 (kritik)"})
        elif skor < 50:
            alerts.append({"type": "hendek_skoru", "severity": "uyari", "symbol": symbol, "message": f"Hendek skoru {skor}/100 < 50 (uyari)"})

    # ===== FAIZ ORTUSME (FAVOK/Faiz) =====
    if os.path.exists(bilanco_path):
        favok = get_val("3DF")
        faiz = get_val("3HB") or 0
        if favok > 0 and faiz > 0:
            oran = favok / faiz
            if oran < 1.5:
                alerts.append({"type": "faiz_ortusme", "severity": "kritik", "symbol": symbol, "message": f"FAVOK/Faiz {oran:.2f}x < 1.5x (kritik)"})
            elif oran < 2.0:
                alerts.append({"type": "faiz_ortusme", "severity": "uyari", "symbol": symbol, "message": f"FAVOK/Faiz {oran:.2f}x < 2.0x (uyari)"})

    # ===== IHALE PAYI =====
    ihale_path = f"analiz-calisma/{symbol_clean}-veri/ihale_bagimliligi.txt"
    if os.path.exists(ihale_path):
        try:
            with open(ihale_path, "r", encoding="utf-8") as f:
                ihale_txt = f.read()
            import re as _re
            m = _re.search(r"(\d+(?:\.\d+)?)\s*%", ihale_txt)
            if m:
                ihale = float(m.group(1))
                if ihale > 40:
                    alerts.append({"type": "ihale_payi", "severity": "kritik", "symbol": symbol, "message": f"Ihale payi %{ihale:.1f} > 40 (kritik)"})
                elif ihale > 20:
                    alerts.append({"type": "ihale_payi", "severity": "uyari", "symbol": symbol, "message": f"Ihale payi %{ihale:.1f} > 20 (uyari)"})
        except Exception:
            pass

    # ===== RR_MIN ve MAX_Pozisyon (degerleme/pozisyon) =====
    deg_path = f"analiz-calisma/{symbol_clean}-veri/degerleme.json"
    if os.path.exists(deg_path):
        with open(deg_path, "r", encoding="utf-8") as f:
            deg = json.load(f)
        v = deg.get("valuation", {})
        rr = v.get("rr_min")
        if rr is not None and rr < 1.5:
            alerts.append({"type": "rr_min", "severity": "uyari", "symbol": symbol, "message": f"Risk/Odül {rr} < 1.5 (uyari)"})

    return alerts

def main():
    WATCHLIST = os.getenv("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS").split(",")
    print(f"[{datetime.now()}] Kural motoru başladı")

    all_alerts = []
    for symbol in WATCHLIST:
        print(f"\n--- {symbol} kural kontrolü ---")
        alerts = check_symbol(symbol)
        if alerts:
            for a in alerts:
                print(f"  ⚠️ [{a['severity']}] {a['message']}")
                all_alerts.append(a)
        else:
            print("  ✓ Eşik ihlali yok")

    with open("analiz-calisma/kural_uyarilari.json", "w", encoding="utf-8") as f:
        json.dump({"checked_at": datetime.now().isoformat(), "alerts": all_alerts}, f, ensure_ascii=False, indent=2)

    print(f"\n[{datetime.now()}] Kural motoru tamamlandı - {len(all_alerts)} uyarı")

if __name__ == "__main__":
    import os, sys, json, datetime
    main()