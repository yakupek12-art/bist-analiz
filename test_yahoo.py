import httpx, asyncio
async def main():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get('https://query1.finance.yahoo.com/v8/finance/chart/ASELS.IS?range=1d&interval=1d', headers={'User-Agent':'Mozilla/5.0'})
        print('ASELS.IS:', r.status_code, len(r.text), 'bytes')
        print(r.text[:300])
asyncio.run(main())