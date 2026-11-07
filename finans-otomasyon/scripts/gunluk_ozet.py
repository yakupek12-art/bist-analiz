# -*- coding: utf-8 -*-
"""
Gunluk BIST ozeti: fiyat verisi ceker, GLM ile analiz eder, Telegram'a gonderir.
GitHub Actions uzerinde calisir (kullanicinin PC'si KAPALIYKEN de calisir).
Tum ayarlar ortam degiskenlerinden (GitHub Secrets) gelir.

Not: NVIDIA ucretsiz katmani bazen cok yavas olabiliyor (uzun kuyruk). Bu yuzden:
- Model zinciri vardir: once MODEL, sonra YEDEK_MODEL denenir.
- Hepsi basarisiz olursa kural tabanli (LLM'siz) otomatik ozet uretilir.
- Boylece kullanici her durumda gunluk mesajini alir.
"""
import json
import os
import sys
import urllib.request
import urllib.parse

NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
WATCHLIST = os.environ.get("WATCHLIST", "ASELS.IS").split(",")
MODEL = os.environ.get("MODEL", "z-ai/glm-5.3-flash")
YEDEK_MODEL = os.environ.get("YEDEK_MODEL", "deepseek-ai/deepseek-v4.1-flash")

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def http_json(url, headers=None, data=None, timeout=60):
    req = urllib.request.Request(url, headers=headers or {}, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_price_info(symbol):
    """Yahoo Finance'den son fiyat ve gunluk degisim."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.strip()}?range=5d&interval=1d"
    data = http_json(url, headers={"User-Agent": "Mozilla/5.0"})
    result = data["chart"]["result"][0]
    meta = result["meta"]
    last = meta["regularMarketPrice"]
    closes = [c for c in result["indicators"]["quote"][0]["close"] if c]
    prev = closes[-2] if len(closes) >= 2 else last
    change = (last - prev) / prev * 100
    name = symbol.strip().replace(".IS", "")
    return name, last, change


def summarize(text, per_model_timeout=360):
    """Fiyat verilerini model zinciriyle Turkce ozete cevirir.

    NVIDIA ucretsiz katmani yavasladiginda zincirdeki diger modele gecer.
    """
    models = [MODEL, YEDEK_MODEL]
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) finans-otomasyon/1.0",
    }
    for model_id in models:
        body = json.dumps({
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sen BIST takip asistanisin. Sadece sana verilen fiyatlara dayali, "
                        "kinayici olmayan, net ve kisa Turkce gunluk borsa ozetleri yazarsin. "
                        "Yatirim tavsiyesi vermezsin, sadece bilgi verirsin. En fazla 8 cumle."
                    ),
                },
                {
                    "role": "user",
                    "content": "Gunun fiyat verileri asagida. Takip listesi ozeti yaz:\n\n" + text,
                },
            ],
            "temperature": 0.4,
            "max_tokens": 400,
            "stream": False,
        }).encode("utf-8")
        try:
            r = http_json(NVIDIA_URL, headers=headers, data=body, timeout=per_model_timeout)
            print(f"Ozet sunu model ile hazirlandi: {model_id}")
            return r["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Ozet modeli basarisiz ({model_id}): {e}")
    raise RuntimeError("zincirdeki tum modeller basarisiz")


def kural_ozeti(data):
    """LLM hic calismazsa otomatik, kural tabanli ozet uretir."""
    parts = []
    for name, last, change in data:
        durum = "yukseldi" if change >= 0 else "geriledi"
        parts.append(f"{name} %{abs(change):.2f} oraninda {durum} (son fiyat {last:.2f} TL).")
    if parts:
        return "Ozet (otomatik hesaplandi): " + " ".join(parts)
    return "Fiyat verisi alinamadi."


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    ).encode("utf-8")
    return http_json(url, data=data, timeout=30)


def main():
    data = []
    lines = []
    for symbol in WATCHLIST:
        if not symbol.strip():
            continue
        try:
            name, last, change = get_price_info(symbol)
            data.append((name, last, change))
            arrow = "▲" if change >= 0 else "▼"
            lines.append(f"{name}: {last:.2f} TL ({change:+.2f}%) {arrow}")
        except Exception as e:
            lines.append(f"{symbol.strip()}: veri alinamadi ({type(e).__name__})")

    prices_text = "\n".join(lines)
    print("Fiyat verisi:\n" + prices_text)

    try:
        summary = summarize(prices_text)
    except Exception as e:
        print(f"Ozet hatasi: {e}")
        summary = kural_ozeti(data)

    message = "📈 GUNLUK BORSA OZETI\n\n" + summary + "\n\n" + prices_text
    result = send_telegram(message)
    print("Telegram sonuc: " + json.dumps(result, ensure_ascii=False)[:200])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
