import asyncio
from nvidia_client import call_nvidia

async def test():
    result = await call_nvidia('Test', 'Merhaba, JSON formatinda cevap ver: {"test": "ok"}', max_tokens=50)
    print(f'Result: {result[:200]}')

asyncio.run(test())