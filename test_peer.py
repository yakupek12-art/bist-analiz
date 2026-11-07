import asyncio
from data_layer import fetch_complete_sync

data = fetch_complete_sync('TUPRS.IS')
print(f"Peer financials keys: {data.financial.metadata.get('peer_financials', {}).keys()}")
peer_comp = data.financial.metadata.get('peer_comparison', {})
print(f"Peer comparison keys: {peer_comp.keys()}")
print(f"Peer names: {peer_comp.get('peer_names')}")
print(f"Target symbol: {peer_comp.get('target_symbol')}")
print(f"Rows count: {len(peer_comp.get('rows', []))}")
for i, row in enumerate(peer_comp.get('rows', [])):
    print(f"  Row {i}: {row['metric']}, target={row.get('target')}, peers={list(row.get('peers', {}).keys())}")