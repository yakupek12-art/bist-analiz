import asyncio
from data_layer import fetch_complete_sync

data = fetch_complete_sync('TUPRS.IS')
print(f"Valuation metadata: {data.financial.metadata.get('valuation', {})}")
val = data.financial.metadata.get('valuation', {})
if val:
    print(f"Market Cap: {val.get('market_cap_mn')} Mn TL")
    print(f"EV: {val.get('enterprise_value_mn')} Mn TL")
    print(f"Fair Value Range: {val.get('fair_value_range')}")
    print(f"Current Price: {val.get('current_price')} TL")
    print(f"Discount: {val.get('discount_pct')}%")
    print(f"Rows: {len(val.get('rows', []))}")
    for r in val.get('rows', []):
        print(f"  {r['method']}: 5Y={r['five_year_avg_multiple']}x, Current={r['current_multiple']}x, FV={r['fair_value_tl']} TL, Margin={r['safety_margin_pct']}%")