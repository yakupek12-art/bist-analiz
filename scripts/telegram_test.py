#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telegram Bildirim Gönderici - ASCII versiyon"""
import os, sys, json, urllib.request, urllib.parse
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

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[HATA] TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID yok")
        return

    msg = "<b>Sistem Testi</b>\n{0} - Sistem calisiyor!".format(datetime.now().strftime('%H:%M:%S'))
    result = send_telegram(msg, os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))
    if result.get("ok"):
        print("[OK] Test mesaji gonderildi")
    else:
        print("[HATA] {0}".format(result.get('error')))

if __name__ == "__main__":
    import os, sys, json, datetime
    main()