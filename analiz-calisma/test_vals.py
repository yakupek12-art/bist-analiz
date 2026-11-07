import csv, os
all_rows = {}
period_cols = set()
for fname in sorted(os.listdir('analiz-calisma/ASELS-veri')):
    if fname.endswith('.csv') and 'bilanco' in fname.lower():
        fpath = os.path.join('analiz-calisma/ASELS-veri', fname)
        with open(fpath, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline().strip()
            cols = [c.strip().strip('"') for c in first_line.split(',')]
            cols = ['EMPTY' if c == '' else c for c in cols]
            reader = csv.DictReader(f, fieldnames=cols)
            for row in reader:
                code = row.get('FINANCIAL_ITEM_CODE', '').strip()
                if not code: continue
                for k, v in row.items():
                    if '/' in k and k[0].isdigit():
                        if code not in all_rows: all_rows[code] = {}
                        all_rows[code][k] = v.strip() if v else ''

keys = ['3A','3B','3C','3DF','3HACA','3L','3H','3IA','3IB','3IC','3HF','3H','3DD','3DE','3C','3B','3HACA']
for k in keys:
    v = all_rows.get(k, {}).get('2024/12', 'YOK')
    print(k + ': ' + str(v))