import asyncio
from data_layer import fetch_complete_sync
from parallel_agents import AnalysisOrchestrator

data = fetch_complete_sync('SDTTR.IS')
print(f'Periods: {len(data.financial.periods)}')
print(f'periods_sorted: {len(data.financial.periods_sorted)}')
for p in data.financial.periods_sorted[:5]:
    print(f'  {p.period}: sales={p.sales}')

# Test _build_delta
orch = AnalysisOrchestrator()
delta = orch._build_delta(data)
print(f'Delta rows: {len(delta.rows)}')
for row in delta.rows:
    print(f'  {row["metric"]}: {len(row["values"])} values, trend={row["trend"]}')
    for v in row["values"]:
        period = v['period']
        value = v['value']
        print(f'    {period}: {value}')