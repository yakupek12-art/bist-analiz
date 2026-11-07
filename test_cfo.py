import asyncio
from data_layer import fetch_complete_sync

data = fetch_complete_sync('SDTTR.IS')
print(f'Periods: {len(data.financial.periods)}')
for p in data.financial.get_year_ends():
    cfo = getattr(p, 'cfo', 'YOK')
    print(f'  {p.period}: cfo={cfo}')