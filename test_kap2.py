import httpx, asyncio

async def test_kap():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get('https://www.kap.org.tr/tr', headers={'User-Agent':'Mozilla/5.0'})
            print('KAP ana sayfa:', r.status_code, len(r.text))
            
            r2 = await client.get('https://www.kap.org.tr/tr/Borsa/HisseSenedi/AKSA.IS', headers={'User-Agent':'Mozilla/5.0'})
            print('AKSA sayfa:', r2.status_code, len(r2.text))
            
            r3 = await client.get('https://www.kap.org.tr/tr/api/disclosures', headers={'User-Agent':'Mozilla/5.0'}, params={'companyQuery': {'text': 'AKSA'}, 'submit': 'Getir'})
            print('KAP API:', r3.status_code, len(r3.text))
            print(r3.text[:200])
        except Exception as e:
            print('HATA:', str(e))

asyncio.run(test_kap())