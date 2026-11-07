import json

with open('veri/finansal.json', 'r') as f:
    fdata = json.load(f)

years = ['2020/12', '2021/12', '2022/12', '2023/12', '2024/12', '2025/12']

def fmt(v):
    if v is None: return 'N/A'
    if isinstance(v, float): return f'{v:.2f}'
    return str(v)

print('=== TAM TABLO (Yil Sonu) ===')
print('YIL | SATIS | FAVOK_MARJ | NET_KAR | NET_BORC/FAVOK | CARI | FCF/NETKAR | ROIC | BRUT_MARJ | NET_MARJ | FCF | OZKAYNAK | NET_BORC | NAKIT')
print('---|-------|------------|---------|----------------|------|------------|------|-----------|----------|-----|----------|----------|------')
for y in ['2020/12', '2021/12', '2022/12', '2023/12', '2024/12', '2025/12']:
    d = fdata[y]
    satis = fdata.get('satislar', {}).get(y, 0) / 1e6
    net_kar = fdata.get('net_kar_anaortak', {}).get(y, 0) / 1e6
    fcf = fdata.get('fcf', {}).get(y, 0) / 1e6
    oz = fdata.get('ozkaynak', {}).get(y, 0) / 1e6
    net_borc = d.get('net_borc', 0) / 1e6
    nakit = fdata.get('nakit', {}).get(y, 0) / 1e6
    
    def fmt(v):
        if v is None: return 'N/A'
        if isinstance(v, float): return f'{v:.2f}'
        return str(v)
    
    row = f'{y} | {fdata.get("satislar", {}).get(y, 0)/1e6:.1f} | '
    row += fmt(fdata[y].get('favok_marj')) + ' | '
    row += f'{fdata.get("net_kar_anaortak", {}).get(y, 0)/1e6:.1f} | '
    row += fmt(fdata[y].get('net_borc_favok')) + ' | '
    row += fmt(fdata[y].get('cari_oran')) + ' | '
    row += fmt(fdata[y].get('fcf_netkar')) + ' | '
    row += fmt(fdata[y].get('roic')) + ' | '
    row += fmt(fdata[y].get('brut_marj')) + ' | '
    row += fmt(fdata[y].get('net_marj')) + ' | '
    row += f'{fdata.get("fcf", {}).get(y, 0)/1e6:.1f} | '
    row += f'{fdata.get("ozkaynak", {}).get(y, 0)/1e6:.1f} | '
    row += f'{d.get("net_borc", 0)/1e6:.1f} | '
    row += f'{fdata.get("nakit", {}).get(y, 0)/1e6:.1f}'
    print(row)

print()
print('=== YoY DEGISIM % (Onceki Yila Gore) ===')
print('YIL | SATIS% | NET_KAR% | FCF% | OZKAYNAK% | NET_BORC% | NAKIT% | FAVOK_MARJ_CHG_pp | NET_BORC/FAVOK_CHG_pp | CARI_CHG_pp | ROIC_CHG_pp')
print('---|--------|----------|------|-----------|-----------|--------|------------------|----------------------|-----------|---------')
prev_data = None
for y in ['2020/12', '2021/12', '2022/12', '2023/12', '2024/12', '2025/12']:
    curr = {
        'satis': fdata.get('satislar', {}).get(y, 0),
        'net_kar': fdata.get('net_kar_anaortak', {}).get(y, 0),
        'fcf': fdata.get('fcf', {}).get(y, 0),
        'oz': fdata.get('ozkaynak', {}).get(y, 0),
        'net_borc': fdata[y].get('net_borc', 0),
        'nakit': fdata.get('nakit', {}).get(y, 0),
        'favok_marj': fdata[y].get('favok_marj'),
        'net_borc_favok': fdata[y].get('net_borc_favok'),
        'cari': fdata[y].get('cari_oran'),
        'roic': fdata[y].get('roic')
    }
    
    if prev_data is not None:
        def pct_chg(curr_v, prev_v):
            if prev_v == 0 or prev_v is None or curr_v is None: return 'N/A'
            return round((curr_v - prev_v) / abs(prev_v) * 100, 1)
        
        sat_chg = pct_chg(fdata.get('satislar', {}).get(y, 0), prev_data['satis'])
        nk_chg = pct_chg(fdata.get('net_kar_anaortak', {}).get(y, 0), prev_data['net_kar'])
        fcf_chg = pct_chg(fdata.get('fcf', {}).get(y, 0), prev_data['fcf'])
        oz_chg = pct_chg(fdata.get('ozkaynak', {}).get(y, 0), prev_data['oz'])
        nb_chg = pct_chg(fdata[y].get('net_borc', 0), prev_data['net_borc'])
        nak_chg = pct_chg(fdata.get('nakit', {}).get(y, 0), prev_data['nakit'])
        fm_chg = pct_chg(fdata[y].get('favok_marj'), prev_data['favok_marj'])
        nbf_chg = pct_chg(fdata[y].get('net_borc_favok'), prev_data['net_borc_favok'])
        car_chg = pct_chg(fdata[y].get('cari_oran'), prev_data['cari'])
        roic_chg = pct_chg(fdata[y].get('roic'), prev_data['roic'])
        
        print(f'{y} | {sat_chg}% | {nk_chg}% | {fcf_chg}% | {oz_chg}% | {nb_chg}% | {nak_chg}% | {fm_chg}pp | {nbf_chg}pp | {car_chg}pp | {roic_chg}pp')
    
    prev_data = {
        'satis': fdata.get('satislar', {}).get(y, 0),
        'net_kar': fdata.get('net_kar_anaortak', {}).get(y, 0),
        'fcf': fdata.get('fcf', {}).get(y, 0),
        'oz': fdata.get('ozkaynak', {}).get(y, 0),
        'net_borc': fdata[y].get('net_borc', 0),
        'nakit': fdata.get('nakit', {}).get(y, 0),
        'favok_marj': fdata[y].get('favok_marj'),
        'net_borc_favok': fdata[y].get('net_borc_favok'),
        'cari': fdata[y].get('cari_oran'),
        'roic': fdata[y].get('roic')
    }