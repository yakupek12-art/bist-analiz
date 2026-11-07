import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from degerleme import calculate_valuation

all_rows = {}
period_cols = set()
for fname in sorted(os.listdir('veri')):
    if fname == 'bilanco.csv':
        with open(os.path.join('veri', fname), 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
            cols = [c.strip().strip('"') for c in first_line.split(',')]
            cols = ['EMPTY' if c == '' else c for c in cols]
            reader = csv.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get('FINANCIAL_ITEM_CODE', '').strip()
                if not code: continue
                if code not in all_rows: all_rows[code] = {}
                for k, v in row.items():
                    if '/' in k and k[0].isdigit():
                        period_cols.add(k)
                        all_rows[code][k] = v.strip() if v else ''

period_cols = sorted(period_cols, key=lambda x: (int(x.split('/')[0]), int(x.split('/')[1])))

with open('veri/fiyat.json') as f:
    price_data = json.load(f)
price = price_data.get('last')
shares = 3500000

result = calculate_valuation(all_rows, period_cols, price_per_share=price, shares=shares)
with open('veri/degerleme.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print('Degerleme tamamlandi')