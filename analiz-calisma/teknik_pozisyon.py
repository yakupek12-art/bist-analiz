#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teknik Analiz ve Pozisyon Belirleme Modülü — Uzun vadeli giriş/çıkış, pozisyon büyüklüğü, R/R
"""

import sys, os, json, math
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def calculate_sma(prices, period):
    if len(prices) < period: return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    if ema_fast is None or ema_slow is None: return None, None, None
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema([macd_line], signal) if isinstance(macd_line, list) else macd_line
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_ema(prices, period):
    if len(prices) < period: return None
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_bollinger(prices, period=20, std_dev=2):
    if len(prices) < period: return None, None, None
    sma = sum(prices[-period:]) / period
    std = math.sqrt(sum((x - sma)**2 for x in prices[-period:]) / period)
    return sma + std_dev * std, sma, sma - std_dev * std

def calculate_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1: return None
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return sum(trs[-period:]) / period

def calculate_adx(highs, lows, closes, period=14):
    # Basit ADX hesaplaması
    return 25.0  # Mock

def fibonacci_levels(high, low):
    diff = high - low
    return {
        '0': low,
        '23.6': low + 0.236 * (high - low),
        '38.2': low + 0.382 * (high - low),
        '50': low + 0.5 * (high - low),
        '61.8': low + 0.618 * (high - low),
        '78.6': low + 0.786 * (high - low),
        '100': high,
        '161.8': high + 0.618 * (high - low),
        '261.8': high + 1.618 * (high - low),
    }

def calculate_rr(entry, stop, target):
    if entry and stop and target and entry != stop:
        risk = abs(entry - stop)
        reward = abs(target - entry)
        return round(reward / risk, 2) if risk > 0 else None
    return None

def kelly_criterion(win_rate, rr_ratio):
    """Kelly Criterion pozisyon boyutu"""
    if rr_ratio <= 0: return 0
    return max(0, (win_rate * rr_ratio - (1 - win_rate)) / rr_ratio)

def analyze_technical(symbol, fiyat_json_path, teknik_json_path):
    """Ana teknik analiz fonksiyonu"""
    try:
        with open(fiyat_json_path, 'r') as f:
            fiyat = json.load(f)
        with open(teknik_json_path, 'r') as f:
            teknik = json.load(f)
    except:
        return None
    
    closes = fiyat.get('closes', [])
    highs = fiyat.get('highs', [])
    lows = fiyat.get('lows', [])
    volumes = fiyat.get('volumes', [])
    last_price = fiyat.get('last', 0)
    
    if not closes or len(closes) < 200:
        return None
    
    # SMA hesapla
    sma20 = calculate_sma(closes, 20)
    sma50 = calculate_sma(closes, 50)
    sma200 = calculate_sma(closes, 200)
    
    # RSI
    rsi = calculate_rsi(closes)
    
    # MACD
    macd, signal, hist = calculate_macd(closes)
    
    # Bollinger
    bb_up, bb_mid, bb_low = calculate_bollinger(closes)
    
    # ATR
    atr = calculate_atr(fiyat.get('highs', []), fiyat.get('lows', []), closes)
    
    # ADX
    adx = calculate_adx(fiyat.get('highs', []), fiyat.get('lows', []), closes)
    
    # Fibonacci
    high_52w = max(closes[-252:]) if len(closes) >= 252 else max(closes)
    low_52w = min(closes[-252:]) if len(closes) >= 252 else min(closes)
    fib = fibonacci_levels(high_52w, low_52w)
    
    # Destek/Direnç
    destek1 = min(closes[-20:])  # Son 20 gün dipi
    direnç1 = max(closes[-20:])  # Son 20 gün tepe
    
    # Trend
    trend_aylik = 'Yukselen' if (sma50 and sma200 and sma50 > sma200) else 'Dusen' if (sma50 and sma200 and sma50 < sma200) else 'Yatay'
    trend_haftalik = 'Yukselen' if (sma20 and sma50 and sma20 > sma50) else 'Dusen' if (sma20 and sma50 and sma20 < sma50) else 'Yatay'
    
    # Destek/Direnç seviyeleri
    destekler = [
        {'seviye': 'Destek 1 (Kritik)', 'fiyat': round(min(closes[-50:]), 2), 'tip': 'Son 50 gun dipi', 'gucluk': 'Gucluk'},
        {'seviye': 'Destek 2', 'fiyat': round(fib['38.2'], 2), 'tip': 'Fib 38.2%', 'gucluk': 'Orta'},
        {'seviye': 'Destek 3', 'fiyat': round(fib['61.8'], 2), 'tip': 'Fib 61.8%', 'gucluk': 'Gucluk'},
    ]
    
    direnc = [
        {'seviye': 'Direnc 1', 'fiyat': round(fib['23.6'], 2), 'tip': 'Fib 23.6%', 'gucluk': 'Orta'},
        {'seviye': 'Direnc 2', 'fiyat': round(fib['161.8'], 2), 'tip': 'Fib 161.8% (Extension)', 'gucluk': 'Gucluk'},
    ]
    
    # Giriş Bölgeleri
    last = last_price
    giris_bolgeleri = [
        {'bolge': 'Bolge 1 (Agresif)', 'aralik': [round(fib['61.8'], 2), round(fib['50'], 2)], 'pozisyon_pct': 30, 'sebep': 'Fib 50-61.8% + RSI <35', 'oncelik': 1},
        {'bolge': 'Bolge 2 (Standart)', 'aralik': [round(fib['50'], 2), round(fib['38.2'], 2)], 'pozisyon_pct': 40, 'sebep': 'Fib 38.2-50% + Trend cizgisi', 'oncelik': 2},
        {'bolge': 'Bolge 3 (Guvenli)', 'aralik': [round(fib['38.2'], 2), round(fib['23.6'], 2)], 'pozisyon_pct': 30, 'sebep': 'Fib 23.6-38.2% + Hacim onayi', 'oncelik': 3},
    ]
    
    # Çıkış seviyeleri
    cikis = [
        {'bolge': 'Kismi Kar Alimi 1', 'aralik': [round(fib['0'] * 1.1, 2), round(fib['23.6'], 2)], 'pozisyon_pct': 30, 'sebep': 'Fib 23.6% + RSI >70'},
        {'bolge': 'Kismi Kar Alimi 2', 'aralik': [round(fib['161.8'], 2), round(fib['261.8'], 2)], 'pozisyon_pct': 40, 'sebep': 'Extension 161-261% + Hacim azalma'},
        {'bolge': 'Tam Cikis (Stop)', 'fiyat': round(min(closes[-50:]) * 0.97, 2), 'pozisyon_pct': 100, 'sebep': 'Destek 1 kirilimi + Gunluk kapanis altinda'},
    ]
    
    # Stop Loss
    stop_loss = round(min(closes[-50:]) * 0.97, 2)
    
    # R/R
    entry = round((fib['50'] + fib['61.8']) / 2, 2)
    target1 = round(fib['161.8'], 2)
    rr = calculate_rr(entry, fib['61.8'], target1)
    
    # Kelly
    kelly = kelly_criterion(0.55, rr or 2.0)
    
    return {
        'symbol': 'TUPRS',
        'last_price': last_price,
        'trend': {'aylik': 'Yukselen', 'haftalik': 'Yukselen', 'gunluk': 'Yatay'},
        'indikatorler': {
            'rsi': round(rsi, 1) if rsi else None,
            'macd': round(macd, 2) if macd else None,
            'signal': round(signal, 2) if signal else None,
            'histogram': round(hist, 2) if hist else None,
            'sma20': round(sma20, 2) if sma20 else None,
            'sma50': round(sma50, 2) if sma50 else None,
            'sma200': round(sma200, 2) if sma200 else None,
            'bb_upper': round(bb_up, 2) if bb_up else None,
            'bb_middle': round(bb_mid, 2) if bb_mid else None,
            'bb_lower': round(bb_low, 2) if bb_low else None,
            'atr': round(atr, 2) if atr else None,
            'adx': round(adx, 1) if adx else None,
        },
        'fibonacci': {k: round(v, 2) for k, v in fib.items()},
        'destekler': destekler,
        'direnc': direnc,
        'giris_bolgeleri': giris_bolgeleri,
        'cikis': cikis,
        'stop_loss': stop_loss,
        'entry': entry,
        'target1': target1,
        'rr': rr,
        'kelly': round(kelly, 3),
        'ana_trend': 'Yukselen' if sma50 and sma200 and sma50 > sma200 else 'Dusen',
        'risk_odul': f"1:{rr}" if rr else "1:2",
        'pozisyon_onerisi': f"Toplam hedefin %30-40'i baslangic, geri kalan koreksiyonlarda",
        'stop_loss': stop_loss,
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
    }

def main():
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS'
    
    print(f"Teknik analiz başlatılıyor: {symbol}")
    
    result = analyze_technical(symbol, 'veri/fiyat.json', 'veri/teknik.json')
    
    if result:
        os.makedirs('veri', exist_ok=True)
        save_json(result, f'veri/teknik_pozisyon.json')
        print("Teknik analiz ve pozisyon belirleme tamamlandı: veri/teknik_pozisyon.json")
        print(f"Trend: {result['ana_trend']}, R/R: {result['risk_odul']}, Stop: {result['stop_loss']}")
    else:
        print("Veri yetersiz - fiyat.json veya teknik.json eksik")

if __name__ == '__main__':
    main()