import json

with open('veri/finansal.json', 'r') as f:
    fdata = json.load(f)

cols = [
    ('2026/6', '2026 Q2'),
    ('2025/12', '2025'),
    ('2024/12', '2024'),
    ('2023/12', '2023'),
    ('2022/12', '2022'),
    ('2021/12', '2021'),
]

print('=== İSTENEN SIRALAMA ===')
for period, label in cols:
    d = fdata.get(period, {})
    satis = fdata.get('satislar', {}).get(period, 0) / 1e6
    net_kar = fdata.get('net_kar_anaortak', {}).get(period, 0) / 1e6
    favok = fdata.get('favok', {}).get(period, 0) / 1e6
    fcf = fdata.get('fcf', {}).get(period, 0) / 1e6
    oz = fdata.get('ozkaynak', {}).get(period, 0) / 1e6
    net_borc = fdata.get('net_borc', {}).get(period, 0) / 1e6
    nakit = fdata.get('nakit', {}).get(period, 0) / 1e6
    
    favok_marj = d.get('favok_marj')
    net_marj = d.get('net_marj')
    brut_marj = d.get('brut_marj')
    net_borc_favok = d.get('net_borc_favok')
    cari = d.get('cari_oran')
    fcf_netkar = d.get('fcf_netkar')
    roic = d.get('roic')
    brut_marj_val = d.get('brut_marj')
    net_marj_val = d.get('net_marj')
    
    print(f'{label}: Satis={satis:.1f} NetKar={net_kar:.1f} FAVOK={favok:.1f} FCF={fcf:.1f} OzKaynak={oz:.1f} NetBorc={net_borc:.1f} Nakit={nakit:.1f} FavokMarj={favok_marj} NetMarj={net_marj_val} BrutMarj={brut_marj_val} NetBorcFavok={net_borc_favok} Cari={cari} FCFNetKar={d.get("fcf_netkar")} ROIC={roic} BrutMarj={brut_marj_val} NetMarj={net_marj_val}')