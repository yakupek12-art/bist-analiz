#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Kural Motoru Bildirimi - GitHub Actions için
Kullanım: python scripts/telegram_bildirim.py "Mesaj içeriği"
Environment: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""
import os, sys, json, urllib.request, urllib.parse


def send_telegram(msg: str, token: str, chat_id: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    ).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("[HATA] TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID ayarlı değil")
        sys.exit(1)

    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = sys.stdin.read()

    if not msg.strip():
        print("[HATA] Boş mesaj")
        sys.exit(1)

    parts = []
    current = ""
    for line in msg.split("\n"):
        if len(current) + len(line) + 1 > 3500:
            parts.append(current)
            current = line + "\n"
        else:
            current += line + "\n"
    if current:
        parts.append(current)

    print(f"Toplam {len(parts)} parça gönderilecek")

    for i, part in enumerate(parts):
        if i == 0:
            text = f"<b>Kural Motoru Uyarısı</b>\n\n{part}"
        else:
            text = f"<b>Devam {i+1}/{len(parts)}</b>\n{part}"

        result = send_telegram(text, token, chat_id)
        if result.get("ok"):
            print(f"  [OK] Bölüm {i+1}/{len(parts)} gönderildi")
        else:
            print(f"  [HATA] {result.get('error')}")

    print("[OK] Tüm bölümler gönderildi!")


if __name__ == "__main__":
    main()
