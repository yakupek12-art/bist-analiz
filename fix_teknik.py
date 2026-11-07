# Fix the syntax error in parallel_agents.py by rewriting the problematic section
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the problematic section and rewrite it cleanly
# The issue is likely a missing comma or invalid character around line 444

# Find the teknik-ajani entry in AGENT_PROMPTS
old_section = '''    },
    
    'teknik-ajani': {
        'name': 'teknik-ajani',
        'desc': 'Teknik Pozisyon Analizi',
        'system': """Sen teknik analistsin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "trend": "YUKARI|ASAGI|YATAY",
  "rsi": 45.2,
  "rsi_signal": "NORMAL|ASIRI_ALIM|ASIRI_SATIM",
  "macd": 0.45,
  "macd_signal": 0.12,
  "macd_histogram": 0.05,
  "macd_signal_name": "AL|SAT|NOTR",
  "adx": 25.5,
  "adx_strength": "ZAYIF|NORMAL|GUCLU|COK_GUCLU",
  "volume_avg_20": 12500000,
  "sma20": 15.45,
  "sma50": 14.80,
  "sma200": 18.50,
  "ema20": 15.20,
  "ema50": 14.90,
  "atr": 1.25,
  "atr_pct": 2.5,
  "bb_upper": 16.50,
  "bb_middle": 15.00,
  "bb_lower": 13.50,
  "bb_position": 0.65,
  "trend": "YUKARI",
  "support": 12.50,
  "resistance": 18.50,
  "stop_loss": 11.50,
  "target": 18.50,
  "risk_reward": "1:2.5",
  "volume_trend": "ARTAN|AZALAN|STABIL",
  "macd_signal_name": "AL",
  "bb_squeeze": false
}""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Asagidaki hesaplamalari TA-Lib ile yap ve sonuclari JSON formatinda ver:

HESAPLANACAK GOSTERGELER:
1. RSI(14) - from close prices
2. MACD(12,26,9) - MACD line, Signal line, Histogram
3. ADX(14) - Trend guclu
4. SMA(20), SMA(50), SMA(200) - Hareketli ortalamalar
5. EMA(20), EMA(50) - Uzamsal hareketli ortalamalar
5. ATR(14) - Average True Range
6. Bollinger Bands(20,2) - Upper, Middle, Lower, Position
7. Support/Resistance - Son 52 hafta high/low ve SMA kesisimleri
7. MACD Signal - MACD vs Signal line kesisimi
8. Volume trend - Son 20 gun ort hacim vs onceki 20 gun
9. Stop Loss - ATR tabanli (2x ATR altinda) veya support altinda
10. Target - Resistance ustunde veya risk/odul 1:2 minimum
10. Risk/Reward orani

VERI:
{fiyat_teknik}

CIKTI: SADECE JSON (yukaridaki formatta). Hesaplamalari TA-Lib (talib) ile yap.
Eger veri yetersizse ilgili alan icin null yaz.""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Yukaridaki hesaplamalari TA-Lib ile yapip sonuclari JSON formatinda ver.
Eger veri yetersizse ilgili alan icin null yaz.""",
    },

# Read the file
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the problematic section
old_section = '''    },
    
    'teknik-ajani': {
        'name': 'teknik-ajani',
        'desc': 'Teknik Pozisyon Analizi',
        'system': """Sen teknik analistsin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "trend": "YUKARI|ASAGI|YATAY",
  "rsi": 45.2,
  "rsi_signal": "NORMAL|ASIRI_ALIM|ASIRI_SATIM",
  "macd": 0.45,
  "macd_signal": 0.12,
  "macd_histogram": 0.05,
  "macd_signal_name": "AL|SAT|NOTR",
  "adx": 25.5,
  "adx_strength": "ZAYIF|NORMAL|GUCLU|COK_GUCLU",
  "volume_avg_20": 12500000,
  "sma20": 15.45,
  "sma50": 14.80,
  "sma200": 18.50,
  "ema20": 15.20,
  "ema50": 14.90,
  "atr": 1.25,
  "atr_pct": 2.5,
  "bb_upper": 16.50,
  "bb_middle": 15.00,
  "bb_lower": 13.50,
  "bb_position": 0.65,
  "trend": "YUKARI",
  "support": 12.50,
  "resistance": 18.50,
  "stop_loss": 11.50,
  "target": 18.50,
  "risk_reward": "1:2.5",
  "volume_trend": "ARTAN|AZALAN|STABIL",
  "macd_signal_name": "AL",
  "bb_squeeze": false
}""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Asagidaki hesaplamalari TA-Lib ile yap ve sonuclari JSON formatinda ver.

HESAPLANACAK GOSTERGELER:
1. RSI(14) - from close prices
2. MACD(12,26,9) - MACD line, Signal line, Histogram
3. ADX(14) - Trend guclu
4. SMA(20), SMA(50), SMA(200) - Hareketli ortalamalar
5. EMA(20), EMA(50) - Uzamsal hareketli ortalamalar
5. ATR(14) - Average True Range
6. Bollinger Bands(20,2) - Upper, Middle, Lower, Position
7. Support/Resistance - Son 52 hafta high/low ve SMA kesisimleri
7. MACD Signal - MACD vs Signal line kesisimi
8. Volume trend - Son 20 gun ort hacim vs onceki 20 gun
9. Stop Loss - ATR tabanli (2x ATR altinda) veya support altinda
10. Target - Resistance ustunde veya risk/odul 1:2 minimum
10. Risk/Reward orani

VERI:
{fiyat_teknik}

CIKTI: SADECE JSON (yukaridaki formatta). Hesaplamalari TA-Lib (talib) ile yap.
Eger veri yetersizse ilgili alan icin null yaz.""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Yukaridaki hesaplamalari TA-Lib ile yapip sonuclari JSON formatinda ver.
Eger veri yetersizse ilgili alan icin null yaz.""",
    },

new_section = '''    },
    
    'teknik-ajani': {
        'name': 'teknik-ajani',
        'desc': 'Teknik Pozisyon Analizi',
        'system': """Sen teknik analistsin. CIKTI: SADECE JSON.

CIKTI FORMATI (JSON):
{
  "trend": "YUKARI|ASAGI|YATAY",
  "rsi": 45.2,
  "rsi_signal": "NORMAL|ASIRI_ALIM|ASIRI_SATIM",
  "macd": 0.45,
  "macd_signal": 0.12,
  "macd_histogram": 0.05,
  "macd_signal_name": "AL|SAT|NOTR",
  "adx": 25.5,
  "adx_strength": "ZAYIF|NORMAL|GUCLU|COK_GUCLU",
  "volume_avg_20": 12500000,
  "sma20": 15.45,
  "sma50": 14.80,
  "sma200": 18.50,
  "ema20": 15.20,
  "ema50": 14.90,
  "atr": 1.25,
  "atr_pct": 2.5,
  "bb_upper": 16.50,
  "bb_middle": 15.00,
  "bb_lower": 13.50,
  "bb_position": 0.65,
  "trend": "YUKARI",
  "support": 12.50,
  "resistance": 18.50,
  "stop_loss": 11.50,
  "target": 18.50,
  "risk_reward": "1:2.5",
  "volume_trend": "ARTAN|AZALAN|STABIL",
  "macd_signal_name": "AL",
  "bb_squeeze": false
}""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Asagidaki hesaplamalari TA-Lib ile yap ve sonuclari JSON formatinda ver.

HESAPLANACAK GOSTERGELER:
1. RSI(14) - from close prices
2. MACD(12,26,9) - MACD line, Signal line, Histogram
3. ADX(14) - Trend guclu
4. SMA(20), SMA(50), SMA(200) - Hareketli ortalamalar
5. EMA(20), EMA(50) - Uzamsal hareketli ortalamalar
5. ATR(14) - Average True Range
6. Bollinger Bands(20,2) - Upper, Middle, Lower, Position
7. Support/Resistance - Son 52 hafta high/low ve SMA kesisimleri
7. MACD Signal - MACD vs Signal line kesisimi
8. Volume trend - Son 20 gun ort hacim vs onceki 20 gun
9. Stop Loss - ATR tabanli (2x ATR altinda) veya support altinda
10. Target - Resistance ustunde veya risk/odul 1:2 minimum
10. Risk/Reward orani

VERI:
{fiyat_teknik}

CIKTI: SADECE JSON (yukaridaki formatta). Hesaplamalari TA-Lib (talib) ile yap.
Eger veri yetersizse ilgili alan icin null yaz.""",
        'user_template': """VERI:
{fiyat_teknik}

SADECE JSON CIKTI URET. Yukaridaki hesaplamalari TA-Lib ile yapip sonuclari JSON formatinda ver.
Eger veri yetersizse ilgili alan icin null yaz.""",
    }

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'teknik-ajani' in content:
    # Find and replace the teknik-ajani section
    old_start = content.find("'teknik-ajani': {")
    if old_start != -1:
        # Find the end of this entry (next agent or end of AGENT_PROMPTS)
        next_agent = content.find("'risk-ajani':", old_start)
        if next_agent == -1:
            next_agent = content.find("AGENT_CONFIGS", old_start)
        
        # Replace from 'teknik-ajani': { to the next agent or AGENT_CONFIGS
        end_idx = content.find("}", old_start)
        # Find the matching closing brace for the teknik-ajani dict
        brace_count = 0
        end_idx = -1
        for i in range(old_start, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx != -1:
            new_content = content[:old_start] + new_section + content[end_idx:]
            with open('parallel_agents.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Fixed!")
        else:
            print("Could not find end of teknik-ajani dict")
    else:
        print("teknik-ajani not found")