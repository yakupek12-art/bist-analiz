import asyncio
from data_layer import fetch_complete_sync

data = fetch_complete_sync('SDTTR.IS')
print(f"Technical price: {data.technical.price}")
print(f"Market cap metadata: {data.financial.metadata.get('market_cap')}")