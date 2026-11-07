#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram'a ESCOM raporu gonder - Basit"""
import os, json, urllib.request, urllib.parse
from datetime import datetime

def send_telegram(msg, token, chat_id):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    token = "8638039828:AAH3RGIyMCx9jnxIAPdRmT5dRXaK0oLnA1E"
    chat_id = "6705235259"
    
    with open("analiz-arşivi/ESCOM-2026-11-03.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    # HTML escape
    content = content.replace("&", "&").replace("<", "<").replace(">", ">")
    
    # Parcalara bol
    parts = []
    current = ""
    for line in content.split("\n"):
        if len(current) + len(line) + 1 > 3500:
            parts.append(current)
            current = line + "\n"
        else:
            current += line + "\n"
    if current: parts.append(current)
    
    print("Toplam {} parca gonderilecek".format(len(parts)))
    
    for i, part in enumerate(parts):
        if i == 0:
            msg = "<b>ESCOM Analiz Raporu - 2026-11-03</b>\n\n" + part
        else:
            msg = "<b>Devam {}/{}</b>\n{}".format(i+1, len(parts), part)
        
        result = send_telegram(msg, "8638039828:AAH3RGIyMCx9jnxIAPdRmT5dRXaK0oLnA1E", "6705235259")
        if result.get("ok"):
            print("  [OK] Bolum {}/{} gonderildi".format(i+1, len(parts)))
        else:
            print("  [HATA] " + str(result.get("error")))
            if len(msg) > 2000:
                short = msg[:2000] + "\n\n... (kisa)"
                result = send_telegram(short, "8638039828:AAH3RGIyMCx9jnxIAPdRmT5dRXaK0oLnA1E", "6705235259")
                if result.get("ok"):
                    print("  [OK] Kisa versiyon gonderildi")
                else:
                    print("  [HATA] Yine basarisiz: " + str(result.get("error")))

    print("\n[OK] Tum bolumler gonderildi!")

if __name__ == "__main__":
    import os, sys, json, urllib.request, urllib.parse
    from datetime import datetime
    main()