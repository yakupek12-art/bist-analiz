"""
NVIDIA API Client - Separated to avoid circular imports
"""
import asyncio
import json
import time
import os
import sys
import traceback
import httpx

# Proje kök dizini
PROJE_KOK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJE_KOK)

# API Key'i environment variable'dan al (güvenlik için)
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
if not NVIDIA_API_KEY:
    # Fallback: .env dosyasından okumaya çalış
    env_path = os.path.join(PROJE_KOK, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("NVIDIA_API_KEY="):
                    NVIDIA_API_KEY = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    break

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

async def call_nvidia(system_prompt: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
    """NVIDIA API'yi çağır - Structured Output zorunlu, Rate limit dayanıklı"""
    
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
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

    max_retries = 5
    base_delay = 2.0  # seconds
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(NVIDIA_URL, headers=headers, json=body)
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                
                # Rate limit handling
                if response.status_code in (429, 503):
                    # Retry-After header varsa kullan
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                        except ValueError:
                            # HTTP-date format olabilir
                            import email.utils
                            try:
                                wait_time = max(0, int(email.utils.mktime_tz(email.utils.parsedate_tz(retry_after)) - time.time()))
                            except:
                                wait_time = base_delay * (2 ** attempt)
                    else:
                        wait_time = base_delay * (2 ** attempt)
                    
                    # Jitter ekle (±25%)
                    import random
                    jitter = wait_time * 0.25 * (2 * random.random() - 1)
                    wait_time = max(1, wait_time + jitter)
                    
                    print(f"  RATE LIMIT {attempt+1}/{max_retries}: {response.status_code} - {wait_time:.1f}s bekle")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # Son deneme - hata döndür ama fallback'e itme
                    return f"RATE_LIMIT_EXCEEDED: {response.status_code} after {max_retries} retries"
                
                # Diğer hatalar
                print(f"  API HATA {attempt+1}/{max_retries}: {response.status_code}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
                    continue
                return f"API HATA: {response.status_code} - {response.text[:500]}"
                
        except httpx.TimeoutException:
            print(f"  TIMEOUT {attempt+1}/{max_retries}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
            return "TIMEOUT_ERROR: API 600s içinde cevap vermedi"
            
        except httpx.ConnectError as e:
            print(f"  CONNECTION ERROR {attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
            return f"CONNECTION_ERROR: {str(e)}"
            
        except Exception as e:
            print(f"  BEKLENMEDİK HATA {attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))
                continue
            return f"UNEXPECTED_ERROR: {str(e)}"
    
    return "MAX_RETRIES_EXCEEDED: Tüm denemeler başarısız"


async def call_nvidia_sync(system_prompt: str, user_prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
    """Sync wrapper for backwards compatibility"""
    return await call_nvidia(system_prompt, user_prompt, temperature, max_tokens)


if __name__ == "__main__":
    # Test
    async def test():
        result = await call_nvidia("Test", "Merhaba", max_tokens=50)
        print(result)
    
    asyncio.run(test())