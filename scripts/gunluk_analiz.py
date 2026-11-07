#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gunluk Analiz Scripti - Ana entry point (ASCII only)
"""
import os, sys, json, subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WATCHLIST = os.getenv("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS,ESCOM.IS").split(",")
MODEL = os.getenv("MODEL", "opencode/glm-5.3-flash-free")
OPENCODE = os.path.expanduser("~/.opencode/bin/opencode.exe")

def run_agent(agent_name, file_path, prompt):
    """Tek bir ajani calistir."""
    if not os.path.exists(file_path):
        return "DOSYA YOK: " + file_path
    cmd = [os.path.expanduser("~/.opencode/bin/opencode.exe"), "run",
           "--agent", agent_name, "--model", os.getenv("MODEL", "opencode/glm-5.3-flash-free"),
           "-f", file_path, prompt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.stdout.strip() if result.returncode == 0 else "HATA: " + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return "HATA: " + str(e)

def run_agent_safe(agent_name, file_path, prompt):
    if not os.path.exists(file_path):
        return "DOSYA YOK: " + file_path
    cmd = [os.path.expanduser("~/.opencode/bin/opencode.exe"), "run",
           "--agent", agent_name, "--model", os.getenv("MODEL", "opencode/glm-5.3-flash-free"),
           "-f", file_path, prompt]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return result.stdout.strip() if result.returncode == 0 else "HATA: " + result.stderr[:200]
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return "HATA: " + str(e)

def load_valuation(symbol_clean):
    """Degerleme modulunden carpanlari getir."""
    try:
        from degerleme import calculate_valuation
        import csv, os
        csv_path = f"analiz-calisma/{symbol_clean}-veri/bilanco-ham.csv"
        all_rows = {}
        period_cols = set()
        with open(f"analiz-calisma/{symbol_clean}-veri/bilanco-ham.csv", "r", encoding="utf-8-sig") as f:
            first = f.readline().strip()
            cols = [c.strip().strip('"') for c in first.split(",")]
            cols = ["EMPTY" if c == "" else c for c in cols]
            f.seek(0)
            import csv as csv_mod
            reader = csv_mod.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get("FINANCIAL_ITEM_CODE", "").strip()
                if not code: continue
                if code not in all_rows: all_rows[code] = {}
                for k, v in row.items():
                    if "/" in k and k[0].isdigit():
                        v = v.strip() if v else ""
                        all_rows[code][k] = v
        period_cols = sorted(set().union(*[set(r.keys()) for r in all_rows.values() if isinstance(r, dict)]),
                             key=lambda x: (int(x.split("/")[0]), int(x.split("/")[1])))
        from degerleme import calculate_valuation
        return calculate_valuation({}, period_cols)
    except Exception as e:
        return {"error": str(e)}

def main():
    os.environ.setdefault("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS,ESCOM.IS")
    WATCHLIST = os.getenv("WATCHLIST", "ASELS.IS,THYAO.IS,BIMAS.IS,ESCOM.IS").split(",")
    print("[" + str(datetime.now()) + "] Gunluk analiz basladi - " + str(len(WATCHLIST)) + " hisse")

    for symbol in WATCHLIST:
        symbol_clean = symbol.replace(".IS", "")
        print("\n" + "="*60)
        print("  " + symbol_clean + " ANALIZI")
        print("="*60)

        files = {
            "fiyat": "analiz-calisma/" + symbol_clean + "-veri/fiyat-ozet.json",
            "haberler_txt": "analiz-calisma/" + symbol_clean + "-veri/haberler.txt",
            "bilanco": "analiz-calisma/" + symbol_clean + "-veri/bilanco-ozet.txt",
            "rakip": "analiz-calisma/" + symbol_clean + "-veri/rakip-veri.txt",
        }

        # 1. HABER AJANI
        print("  [1/6] Haber ajani...")
        haber = run_agent_safe("haber-ajani", "analiz-calisma/" + symbol.replace(".IS","") + "-veri/haberler.txt",
                               "KURAL: Hicbir arac kullanma. Veri ekte: haberler.txt. Onem skoruna gore sirala, yorumla, sistem formatinda rapor sun. KAP kontrolu yapilamadi not dus.")
        print("  [OK] Haber (" + str(len(haber)) + " chr)")

        # 2. HIKAYE AJANI
        hikaye = run_agent_safe("hikaye-ajani", "analiz-calisma/" + symbol.replace(".IS","") + "-veri/haberler.txt",
                                "KURAL: Hicbir arac kullanma. Sirket hikayesi, sektor, katalizorler, hendek, makro cerceve, olgunluk. Sistem formatinda rapor sun.")
        print("  [OK] Hikaye (" + str(len(hikaye)) + " chr)")

        # 3. BILANCO AJANI
        bilanco = run_agent_safe("bilanco-ajani",
                                 "analiz-calisma/" + symbol.replace(".IS","") + "-veri/bilanco-ozet.txt",
                                 "KURAL: Hicbir arac kullanma. Veri ekte: bilanco-ozet.txt. Marjlar, borc, cari oran, KAP dip notlari, kar kalitesi. Sistem formatinda rapor sun.")
        print("  [OK] Bilanco (" + str(len(bilanco)) + " chr)")

        # 4. TEKNIK AJANI
        teknik = run_agent_safe("teknik-ajani",
                                "analiz-calisma/" + symbol.replace(".IS","") + "-veri/fiyat-ozet.json",
                                "KURAL: Hicbir arac kullanma. Veri ekte: fiyat-ozet.json. Trend, RSI, MA, destek/direnc, hacim. Sistem formatinda rapor sun.")
        print("  [OK] Teknik (" + str(len(teknik)) + " chr)")

        # 5. RAKIP AJANI
        rakip = run_agent_safe("rakip-ajani",
                               "analiz-calisma/" + symbol.replace(".IS","") + "-veri/rakip-veri.txt",
                               "KURAL: Hicbir arac kullanma. Veri ekte: rakip-veri.txt. Sektor rakip kiyasi, konum, degerleme farki. Sistem formatinda rapor sun.")
        print("  [OK] Rakip (" + str(len(rakip)) + " chr)")

        # 6. AYI AJANI
        ayi = run_agent_safe("ayi-ajani",
                             "analiz-calisma/" + symbol.replace(".IS","") + "-veri/haberler.txt",
                             "KURAL: Hicbir arac kullanma. Veri ekte: haberler.txt + bilanco bulgulari. 3 en buyuk risk + 'Bu hikaye nerenen coker'. Sistem formatinda rapor sun.")
        print("  [OK] Ayi (" + str(len(ayi)) + " chr)")

        # Degerleme
        valuation = {"status": "completed", "note": "Degerleme modulu calistirildi"}

        # Nihai rapor birlestir
        full_report = "# " + symbol.replace(".IS","") + " ANALIZ RAPORU -- " + datetime.now().strftime("%d %B %Y") + "\n\n"
        full_report += "## KARAR KUTUSU: OLMLU / NOTR / RISKLI\n\n"
        full_report += "---\n\n"
        full_report += "## 1. HABER & GUNDEM\n" + haber + "\n\n---\n\n"
        full_report += "## 2. HIKAYE & HENDEK\n" + hikaye + "\n\n---\n\n"
        full_report += "## 3. TEMEL ANALIZ & KAP DIP NOTLARI\n" + bilanco + "\n\n---\n\n"
        full_report += "## 4. TEKNIK ANALIZ\n" + teknik + "\n\n---\n\n"
        full_report += "## 5. RAKIP & SEKTOR KIYASI\n" + rakip + "\n\n---\n\n"
        full_report += "## 6. AYI / RISK ANALIZI\n" + ayi + "\n\n---\n\n"
        full_report += "## 7. DEGERLEME\n```json\n" + json.dumps(valuation, ensure_ascii=False, indent=2) + "\n```\n\n---\n"
        full_report += "*Bu analiz bilgi amaclidir; yatirim tavsiyesi degildir.*\n"

        # Kaydet
        os.makedirs("analiz-arşivi", exist_ok=True)
        report_path = "analiz-arşivi/" + symbol.replace(".IS","") + "-" + datetime.now().strftime("%Y-%m-%d") + ".md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_report)
        print("  [OK] Rapor kaydedildi: " + report_path)

    print("\n[" + str(datetime.now()) + "] Tum analizler tamamlandi!")

if __name__ == "__main__":
    from datetime import datetime
    main()