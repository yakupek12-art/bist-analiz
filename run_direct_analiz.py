# -*- coding: utf-8 -*-
"""
BIST Coklu-Ajan Analiz Sistemi -- Master Koordinator (10 Katman)
Veri toplama -> 10 Uzman Ajan -> Sentez -> Arsiv + Delta

Kullanim:
    python run_direct_analiz.py TUPRS.IS
    python run_direct_analiz.py THYAO.IS
"""

import sys
import os
import json
import subprocess
import argparse
import glob
from datetime import datetime

# Proje kok dizini
PROJE_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJE_KOK)
sys.path.insert(0, os.path.join(PROJE_KOK, 'analiz-calisma'))

def run_cmd(cmd, description, capture=True, timeout=300):
    """Komut calistir, hata olsa bile devam et."""
    print("\n" + "="*60)
    print(">> " + description)
    print("="*60)
    print("$ " + cmd)
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=PROJE_KOK)
            if result.stdout:
                print(result.stdout[-2000:])
            if result.stderr:
                print("STDERR:", result.stderr[-1000:])
            return result.returncode == 0
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout, cwd=PROJE_KOK)
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("TIMEOUT: " + description)
        return False
    except Exception as e:
        print("HATA: " + str(e))
        return False

def run_python_script(script_name, args="", description=""):
    """Python scripti calistir"""
    cmd = "python analiz-calisma/" + script_name + " " + args
    return run_cmd(cmd, description or (script_name + " " + args))

def run_veri_cekici(sembol, description="Veri toplama (tum moduller)"):
    """Yeni veri_cekici.py modülünü kullanarak tüm veriyi çek"""
    cmd = "python analiz-calisma/veri_cekici.py " + sembol
    return run_cmd(cmd, description)

def read_file(path):
    """Dosya oku"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

def call_nvidia_api(system_prompt, user_prompt, temperature=0.3, max_tokens=4000):
    """NVIDIA API'yi dogrudan cagir"""
    import requests
    NVIDIA_API_KEY = "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"
    NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

    headers = {
        "Authorization": "Bearer " + NVIDIA_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) finans-analiz/1.0",
    }

    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    try:
        resp = requests.post(NVIDIA_URL, headers=headers, json=body, timeout=300)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return "API HATA: " + str(resp.status_code) + " - " + resp.text
    except Exception as e:
        return "BAGLANTI HATASI: " + str(e)

def read_files(file_list):
    """Dosyalari oku ve birlestir"""
    content = ""
    for f in file_list.split():
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                content += "\n--- " + f + " ---\n" + fp.read() + "\n"
        except:
            pass
    return content

# Import layers
from layers import layers

def run_layers(sembol_clean, today):
    """10 katman analizi calistir"""

    def call_nvidia_api(system_prompt, user_prompt, temperature=0.3, max_tokens=4000):
        """NVIDIA API'yi dogrudan cagir - Retry ve fallback ile"""
        import requests
        import time
        NVIDIA_API_KEY = "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"
        NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
        MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

        headers = {
            "Authorization": "Bearer " + NVIDIA_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) finans-analiz/1.0",
        }

        body = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        # Retry mekanizmasi: 3 deneme
        for attempt in range(3):
            try:
                resp = requests.post(NVIDIA_URL, headers=headers, json=body, timeout=600)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                else:
                    print("   API HATA (deneme {attempt+1}/3): {resp.status_code} - {resp.text[:200]}".format(attempt=attempt, resp=resp))
                    if attempt < 2:
                        time.sleep(5 * (attempt + 1))
                        continue
                    return "API HATA: " + str(resp.status_code) + " - " + resp.text[:500]
            except Exception as e:
                print("   BAGLANTI HATASI (deneme {attempt+1}/3): {e}".format(attempt=attempt, e=e))
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                return "BAGLANTI HATASI (3 deneme basarisiz): " + str(e)
        
        # Tum denemeler basarisiz -> Fallback basit rapor
        return "[FALLBACK] API cagrilari basarisiz oldu. Veri setleri hazir, manuel analiz gerekli. Veri dosyalari: veri/ klasorunde mevcut."

    def read_files(file_list):
        """Dosyalari oku ve birlestir"""
        content = ""
        for f in file_list.split():
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    content += "\n--- " + f + " ---\n" + fp.read() + "\n"
            except:
                pass
        return content

    print("\n" + "="*60)
    print("ADIM 2: 10 KATMAN ANALIZI (NVIDIA API Direct)")
    print("="*60)

    for layer in layers:
        print("\n>> " + layer['desc'] + " (" + layer['name'] + ")")
        file_content = read_files(layer['files'])
        user_prompt = layer['user_template'].format(**{
            'sektor_veri': read_files('veri/sektor_veri.json'),
            'sektor_peerler': read_files('veri/sektor_peerler.txt'),
            'makro_veri': read_files('veri/makro_veri.json'),
            'hikaye_veri': read_files('veri/hikaye_veri.json'),
            'bilanco_ozet': read_files('veri/bilanco.csv')[:5000],
            'kap_yatirim_planlari': read_files('veri/kap_yatirim_planlari.txt'),
            'hendek_veri': read_files('veri/hendek_veri.json'),
            'rakip_giris_bariyerleri': read_files('veri/rakip_giris_bariyerleri.txt'),
            'kriz_performans': read_files('veri/kriz_performans.txt'),
            'rakip_veri': read_files('veri/rakip_veri.json'),
            'rakip_karsilastirma': read_files('veri/rakip_karsilastirma.json'),
            'sektor_veri': read_files('veri/sektor_veri.json'),
            'yonetim_veri': read_files('veri/yonetim_veri.json'),
            'sektor_karsilastirma': read_files('veri/sektor_karsilastirma.json'),
            'sektor_veri': read_files('veri/sektor_veri.json'),
            'finansal_derinlik': read_files('veri/finansal_derinlik.json'),
            'yonetim_veri': read_files('veri/yonetim_veri.json'),
            'duyarlilik_veri': read_files('veri/duyarlilik_veri.json'),
            'makro_veri': read_files('veri/makro_veri.json'),
            'ihale_bagimliligi': read_files('veri/ihale_bagimliligi.txt'),
            'kredi_kosullari': read_files('veri/kredi_kosullari.txt'),
            'degerleme_girdi': read_files('veri/degerleme_girdi.json'),
            'finansal_derinlik': read_files('veri/finansal_derinlik.json'),
            'hendek_skor': read_files('veri/hendek_skor.json'),
            'bilanco_csv': read_files('veri/bilanco.csv')[:8000],
            'finansal_derinlik': read_files('veri/finansal_derinlik.json'),
            'kap_dip_notlari': read_files('veri/kap_dip_notlari.txt'),
            'teknik_veri': read_files('veri/teknik.json'),
            'fiyat_veri': read_files('veri/fiyat.json'),
            'hacim_profili': read_files('veri/hacim_profili.json'),
            'hendek_skor': read_files('veri/hendek_skor.json'),
        })
        
        report = call_nvidia_api(layer['system'], user_prompt)
        
        with open("raporlar/" + layer['name'] + "-raporu.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        print("   " + layer['desc'] + " tamamlandi")

    print("\n10 Katman analizi tamamlandi - raporlar/ klasorune yazildi")


def run_sentez(sembol_clean, today):
    """Sentez islemi calistir"""
    import os, json, re, glob
    from datetime import datetime

    sembol = "TUPRS"

    # Raporlari oku
    reports = {}
    for name in ['sektor-ajani', 'hikaye-ajani', 'hendek-ajani', 'rakip-ajani', 'yonetim-ajani', 
                 'sektor-karsilastirma-ajani', 'risk-ajani', 'degerleme-ajani', 'bilanco-ajani', 'teknik-ajani']:
        path = 'raporlar/{name}-raporu.md'.format(name=name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                reports[name] = f.read()
        else:
            reports[name] = 'RAPOR YOK'

    # KARAR KUTUSU MANTIGI (10 Katman agirlikli)
    layer_weights = {
        'sektor-ajani': 5,
        'hikaye-ajani': 10,
        'hendek-ajani': 20,
        'rakip-ajani': 10,
        'yonetim-ajani': 10,
        'sektor-karsilastirma-ajani': 10,
        'risk-ajani': 15,
        'degerleme-ajani': 10,
        'bilanco-ajani': 5,
        'teknik-ajani': 5,
    }

    risk_signals = 0
    positive_signals = 0
    total_weight = 0
    positive_weight = 0

    for name, content in reports.items():
        weight = layer_weights.get(name, 5)
        total_weight += weight
        c = content.upper()
        if any(w in c for w in ['KRITIK', 'RISKLI', 'ZAYIF', 'SORUN', 'UYARI', 'DUSUS', 'AZALMA', 'KIRILMA', 'TUZAK']):
            risk_signals += 1
        if any(w in c for w in ['GUCLU', 'OLUMLU', 'LIDER', 'ARTIS', 'IYILESME', 'YUKSEK', 'KARLI', 'GENISLEME', 'AVANTAJ', 'GUVENILIR']):
            positive_signals += 1
            positive_weight += weight

    if risk_signals >= 4 or (total_weight > 0 and (total_weight - positive_weight) / total_weight > 0.4):
        karar = 'ZAYIF'
    elif risk_signals <= 1 and positive_weight / total_weight > 0.7:
        karar = 'GUCLU'
    else:
        karar = 'ORTA'

    # KACIRDIKLARIN (bilanco raporundan)
    kacirdiklar = ''
    if 'bilanco-ajani' in reports:
        lines = reports['bilanco-ajani'].split('\n')
        in_section = False
        for line in lines:
            if 'KACIRABILECEGIN' in line.upper() or 'DIP NOT' in line.upper():
                in_section = True
            if in_section and line.strip().startswith('##') and 'KACIR' not in line.upper():
                in_section = False
            if in_section:
                kacirdiklar += line + '\n'

    # DELTA
    archive_files = sorted(glob.glob('analiz-arşivi/TUPRS-*.md'))
    delta = ''
    if len(archive_files) >= 2:
        prev = archive_files[-2]
        with open(prev, 'r', encoding='utf-8') as f:
            prev_content = f.read()
        curr_lines = set(str(reports).split('\n'))
        prev_lines = set(prev_content.split('\n'))
        added = curr_lines - prev_lines
        removed = prev_lines - curr_lines
        if added or removed:
            delta = '### Degisenler:\n'
            for a in sorted(added)[:15]:
                delta += '+ {a}\n'.format(a=a)
            for r in sorted(removed)[:8]:
                delta += '- {r}\n'.format(r=r)
    elif len(archive_files) == 1:
        delta = 'Ilk analiz -- delta yok.'
    else:
        delta = 'Ilk analiz -- delta yok.'

    # DEGERLEME
    deg = ''
    if os.path.exists('veri/degerleme.json'):
        with open('veri/degerleme.json', 'r', encoding='utf-8') as f:
            d = json.load(f)
        v = d.get('valuation', {})
        p_e = v.get('p_e', '-')
        ev_favok = v.get('ev_favok', '-')
        p_s = v.get('p_s', '-')
        favok_margin = v.get('favok_margin', '-')
        net_margin = v.get('net_margin', '-')
        net_borc_favok = v.get('net_borc_favok', '-')
        deg = '- P/E: {p_e} | EV/FAVOK: {ev_favok} | P/S: {p_s}\n'.format(p_e=p_e, ev_favok=ev_favok, p_s=p_s)
        deg += '- FAVOK Marji: {favok_margin}% | Net Marj: {net_margin}%\n'.format(favok_margin=favok_margin, net_margin=net_margin)
        deg += '- Net Borc/FAVOK: {net_borc_favok}x\n'.format(net_borc_favok=net_borc_favok)
        if 'fair_price_pe' in v:
            fair_price_pe = v['fair_price_pe']
            safety_margin_pe = v.get('safety_margin_pe', '-')
            deg += '- Fair Price (P/E): {fair_price_pe:.2f} TL | Guvenlik Marji: {safety_margin_pe}%\n'.format(fair_price_pe=fair_price_pe, safety_margin_pe=safety_margin_pe)

    # MOATSIZ DEGERLEME
    moatsiz = ''
    if os.path.exists('veri/degerleme_moatsiz.json'):
        with open('veri/degerleme_moatsiz.json', 'r', encoding='utf-8') as f:
            d = json.load(f)
        hendeksiz_kontrol = d.get('hendeksiz_kontrol', {}).get('tum_kriterler_karsilandi', 'N/A')
        moatsiz = '- Hendeksiz Kontrol: {hendeksiz_kontrol}\n'.format(hendeksiz_kontrol=hendeksiz_kontrol)
        if 'fair_value_aralik' in d:
            fv_min = d['fair_value_aralik'].get('min', 'N/A')
            fv_max = d['fair_value_aralik'].get('max', 'N/A')
            moatsiz += '- Fair Value Araligi: {fv_min} - {fv_max} TL\n'.format(fv_min=fv_min, fv_max=fv_max)

    # TEKNIK POZISYON
    teknik_ozet = ''
    if os.path.exists('veri/teknik_pozisyon.json'):
        with open('veri/teknik_pozisyon.json', 'r', encoding='utf-8') as f:
            d = json.load(f)
        ana_trend = d.get('ana_trend', 'N/A')
        rsi = d.get('indikatorler', {}).get('rsi', 'N/A')
        risk_odul = d.get('risk_odul', 'N/A')
        stop_loss = d.get('stop_loss', 'N/A')
        entry = d.get('entry', 'N/A')
        target1 = d.get('target1', 'N/A')
        teknik_ozet = '- Trend: {ana_trend} | RSI: {rsi} | R/R: {risk_odul}\n'.format(ana_trend=ana_trend, rsi=rsi, risk_odul=risk_odul)
        teknik_ozet += '- Stop: {stop_loss} | Giris: {entry} | Hedef: {target1}\n'.format(stop_loss=stop_loss, entry=entry, target1=target1)

    # HENDEK SKORU
    hendek_ozet = ''
    if os.path.exists('veri/hendek_skor.json'):
        with open('veri/hendek_skor.json', 'r', encoding='utf-8') as f:
            d = json.load(f)
        skor = d.get('skor', 'N/A')
        hendek_durum = 'HENDEKLI' if d.get('skor', 0) >= 50 else 'HENDEKSIZ'
        hendek_ozet = '- Hendek Skoru: {skor}/100 -> {durum}\n'.format(skor=skor, durum=hendek_durum)

    # Ensure variables are defined even if files don't exist
    moatsiz = moatsiz or ''
    teknik_ozet = teknik_ozet or ''
    hendek_ozet = hendek_ozet or ''

    # KACIRDIKLARIN (bilanco raporundan)
    kacirdiklar = ''
    if 'bilanco-ajani' in reports:
        lines = reports['bilanco-ajani'].split('\n')
        in_section = False
        for line in lines:
            if 'KACIRABILECEGIN' in line.upper() or 'DIP NOT' in line.upper():
                in_section = True
            if in_section and line.strip().startswith('##') and 'KACIR' not in line.upper():
                in_section = False
            if in_section:
                kacirdiklar += line + '\n'

    # DELTA
    archive_files = sorted(glob.glob('analiz-arşivi/TUPRS-*.md'))
    delta = ''
    if len(archive_files) >= 2:
        prev = archive_files[-2]
        with open(prev, 'r', encoding='utf-8') as f:
            prev_content = f.read()
        curr_lines = set(str(reports).split('\n'))
        prev_lines = set(prev_content.split('\n'))
        added = curr_lines - prev_lines
        removed = prev_lines - curr_lines
        if added or removed:
            delta = '### Degisenler:\n'
            for a in sorted(added)[:15]:
                delta += '+ {a}\n'.format(a=a)
            for r in sorted(removed)[:8]:
                delta += '- {r}\n'.format(r=r)
    elif len(archive_files) == 1:
        delta = 'Ilk analiz -- delta yok.'
    else:
        delta = 'Ilk analiz -- delta yok.'

    # CIKTI - TUMLER BU PROCESS'TE
    r = reports
    output = '# TUPRS ANALIZ RAPORU -- 2026-10-31\n\n## KARAR KUTUSU: ' + karar + '\n\n---\n\n## 1. SEKTOR MAKRO (Katman 1)\n' + r.get('sektor-ajani', 'RAPOR YOK') + '\n\n---\n\n## 2. HIKAYE VE STRATEJI (Katman 2)\n' + r.get('hikaye-ajani', 'RAPOR YOK') + '\n\n---\n\n## 3. HENDEK (MOAT) -- 5/10 YIL (Katman 3)\n' + r.get('hendek-ajani', 'RAPOR YOK') + '\n\n---\n\n## 4. RAKIP DERIN ANALIZI (Katman 4)\n' + r.get('rakip-ajani', 'RAPOR YOK') + '\n\n---\n\n## 5. YONETIM / HAKIM ORTAK (Katman 5)\n' + r.get('yonetim-ajani', 'RAPOR YOK') + '\n\n---\n\n## 6. SEKTOR vs SIRKET KARSILASTIRMASI (Katman 6)\n' + r.get('sektor-karsilastirma-ajani', 'RAPOR YOK') + '\n\n---\n\n## 7. DUYARLILIK VE RISK (Katman 7)\n' + r.get('risk-ajani', 'RAPOR YOK') + '\n\n---\n\n## 8. DEGERLEME (Katman 8)\n' + r.get('degerleme-ajani', 'RAPOR YOK') + '\n\n' + moatsiz + '\n' + teknik_ozet + '\n' + hendek_ozet + '\n\n---\n\n## 9. BILANCO DERIN OKUMA (Katman 9)\n' + r.get('bilanco-ajani', 'RAPOR YOK') + '\n\n---\n\n## 10. TEKNIK ANALIZ VE POZISYON (Katman 10)\n' + r.get('teknik-ajani', 'RAPOR YOK') + '\n\n---\n\n## SENIN KACIRDIKLARIN (KAP Dip Notlari)\n' + (kacirdiklar if kacirdiklar else 'Bilanco raporunda dip not bolumu bulunamadi.') + '\n\n---\n\n## DELTA (Onceki Rapora Gore)\n' + delta + '\n\n---\n\n*Bu analiz bilgi amaclidir; yatirim tavsiyesi degildir.*'

    archive_path = 'analiz-arşivi/TUPRS-2026-10-31.md'
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(output)

    print('SENTEZ TAMAM: ' + archive_path)
    print('KARAR: ' + karar)


def main():
    parser = argparse.ArgumentParser(description="BIST 10 Katmanli Coklu-Ajan Finansal Analiz")
    parser.add_argument("sembol", help="Hisse sembolu (orn: TUPRS.IS, THYAO.IS)")
    parser.add_argument("--skip-veri", action="store_true", help="Veri toplama atla (varsa kullan)")
    parser.add_argument("--skip-ajan", action="store_true", help="Ajanlari atla (sadece sentez)")
    parser.add_argument("--sadece-haber", action="store_true", help="Sadece haber analizi")
    args = parser.parse_args()

    sembol = args.sembol.upper()
    sembol_clean = sembol.replace(".IS", "")
    today = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "#"*60)
    print("# BIST 10 KATMANLI ANALIZ: " + sembol + " (" + today + ")")
    print("#" + "#"*60)
    print("Calisma dizini: " + PROJE_KOK)

    # Klasorleri hazirla
    for d in ["veri", "raporlar", "analiz-arşivi"]:
        os.makedirs(d, exist_ok=True)

    # ============================================================
    # ADIM 1: VERI TOPLAMA (KOORDINATOR -- AI'SIZ, MAKINE KODU)
    # ============================================================
    if not args.skip_veri and not args.sadece_haber:
        print("\n" + "="*60)
        print("ADIM 1: VERI TOPLAMA (10 Ajan icin)")
        print("="*60)

        # Tek modül ile tüm veriyi çek (fiyat, bilanco, haber, kap, sektor, rakip, duyarlilik, degerleme, teknik)
        run_veri_cekici(sembol, "Veri toplama (tum moduller: fiyat, bilanco, haber, kap, sektor, rakip, duyarlilik, degerleme, teknik)")

        print("Veri toplama TAMAM - veri/ klasoru dolu")

    # ============================================================
    # ADIM 2: 10 KATMAN ANALIZI (NVIDIA API Direct)
    # ============================================================
    if not args.skip_ajan and not args.sadece_haber:
        run_layers(sembol_clean, today)

    elif args.sadece_haber:
        print("\nSADECE HABER MODU")
        run_cmd("opencode run --agent haber-ajani -f veri/haberler.txt -f veri/kap_bildirim.txt \"Analiz et ve rapor yaz\"", "Haber Ajanı")

    # ============================================================
    # ADIM 3: SENTEZ (KOORDINATOR -- 10 RAPOR GELDIGTEN SONRA)
    # ============================================================
    if not args.sadece_haber:
        run_sentez(sembol_clean, today)

    print("\n" + "#"*60)
    print("# ANALIZ TAMAMLANDI: " + sembol)
    print("# Rapor: analiz-arşivi/" + sembol_clean + "-" + today + ".md")
    print("# Ham veriler: veri/")
    print("# Ajan raporlari: raporlar/")
    print("#"*60)

if __name__ == "__main__":
    main()