#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram'a ESCOM raporu gonder - ASCII guvenli"""
import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime

def send_telegram(message, token, chat_id):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except Exception as e:
        return {"ok": False, "error": str(e)}

def format_report_for_telegram(report_path, max_len=4000):
    """Raporu Telegram icin formatla"""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # HTML formatinda gonder
        if len(content) > max_len:
            content = content[:max_len] + "\n\n... (Devamı dosyada)"
        
        # Markdown'i basit HTML'e cevir
        content = content.replace("## ", "<b>").replace("### ", "<b>").replace("**", "<b>").replace("*", "-")
        content = content.replace("---", "<hr>")
        content = content.replace("\n", "\n")
        
        return content
    except Exception as e:
        return "<b>Rapor okuma hatasi:</b> " + str(e)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "8638039828:AAH3RGIyMCx9jnxIAPdRmT5dRXaK0oLnA1E")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "6705235259")
    
    report_path = "analiz-arşivi/ESCOM-2026-11-03.md"
    
    if not os.path.exists(report_path):
        print("Rapor dosyasi bulunamadi: " + report_path)
        return
    
    print("[" + str(datetime.now()) + "] ESCOM raporu Telegram'a gonderiliyor...")
    
    message = format_report_for_telegram("analiz-arşivi/ESCOM-2026-11-03.md")
    
    # Mesaj cok uzunsa parcala
    max_len = 4000
    if len(message) > max_len:
        parts = [message[i:i+max_len] for i in range(0, len(message), max_len)]
        for i, part in enumerate(parts):
            header = "<b>ESCOM Analiz Raporu - Bolum {}/{}<b>\n\n".format(i+1, len(parts))
            message_part = header + part
            result = send_telegram(message_part, token, chat_id)
            if result.get("ok"):
                print("  [OK] Bolum {}/{} gonderildi".format(i+1, len(parts)))
            else:
                print("  [HATA] " + str(result.get("error")))
    else:
        header = "<b>ESCOM Analiz Raporu - 2026-11-03</b>\n\n"
        message = header + message
        result = send_telegram(message, token, chat_id)
        if result.get("ok"):
            print("[OK] Telegram'a basariyla gonderildi!")
        else:
            print("[HATA] " + str(result.get("error")))

if __name__ == "__main__":
    import os, sys, json, urllib.request, urllib.parse
    from datetime import datetime
    main()