import httpx
import asyncio

async def test_kap():
    url = "https://www.kap.org.tr/tr"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            print(f"Status: {resp.status_code}")
            print(f"Boyut: {len(resp.text)} karakter")
            print("KAP'ERIŞIM: BAŞARILI" if resp.status_code == 200 else "KAP'ERIŞIM: HATA")
    except Exception as e:
        print(f"HATA: {e}")

asyncio.run(test_kap())