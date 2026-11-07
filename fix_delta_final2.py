import os

base_path = r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje"
file_path = os.path.join(base_path, "parallel_agents.py")

print(f"Using path: {file_path}")
print(f"Exists: {os.path.exists(file_path)}")

with open(file_path, 'rb') as f:
    content = f.read()

# Exact old bytes
old = b'''def _build_delta(self, data: CompleteData) -> DeltaAnalysis:
        """Delta analizi olu\xc5\x9ftur"""\"
        financial = data.financial
        periods = financial.periods_sorted[:5]
        
        rows = []
        for key, label in [(\'favok_margin_pct\', \'FAVOK Marji %\'), (\'net_debt_favok\', \'Net Borc/FAVOK\'),
                          (\'roic_pct\', \'ROIC %\'), (\'current_ratio\', \'Cari Oran\'), (\'fcf_net_income_pct\', \'FCF/NetKar %\')]:
            values = []
            for p in periods[:5]:
                val = getattr(p, key, None) if hasattr(p, key) else None
                values.append({\'period\': p.period, \'value\': val})
            rows.append({
                \'metric\': label,
                \'values\': [{\'period\': p.period, \'value\': getattr(p, key, None)} for p in periods[:5]],
                \'trend\': \'YUKARI\' if values[-1] and values[0] and values[-1] > values[0] else (\'ASAGI\' if values[-1] and values[0] else \'YATAY\')
            })
        return DeltaAnalysis(rows=rows)'''

new = b'''def _build_delta(self, data: CompleteData) -> DeltaAnalysis:
        """Delta analizi olu\xc5\x9ftur\"\"\"
        financial = data.financial
        periods = financial.periods_sorted[:5]
        
        # Filter for periods that have the required data
        valid_periods = [p for p in periods if p.period and hasattr(p, \'period\')]
        
        if not valid_periods:
            return DeltaAnalysis(rows=[])
        
        rows = []
        for key, label in [(\'favok_margin_pct\', \'FAVOK Marji %\'), (\'net_debt_favok\', \'Net Borc/FAVOK\'),
                           (\'roic_pct\', \'ROIC %\'), (\'current_ratio\', \'Cari Oran\'), (\'fcf_net_income_pct\', \'FCF/NetKar %\')]:
            values = []
            for p in valid_periods[:5]:
                val = getattr(p, key, None) if hasattr(p, key) else None
                values.append({\'period\': p.period, \'value\': val})
            if not values:
                continue
            rows.append({
                \'metric\': label,
                \'values\': [{\'period\': v[\'period\'], \'value\': v[\'value\']} for v in values],
                \'trend\': \'YUKARI\' if values[-1] and values[0] and values[-1] > values[0] else (\'ASAGI\' if values[-1] and values[0] else \'YATAY\')
            })
        return DeltaAnalysis(rows=rows)'''

file_path = r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\parallel_agents.py"

with open(file_path, 'rb') as f:
    content = f.read()

if old in content:
    new_content = content.replace(old, new)
    with open(file_path, 'wb') as f:
        f.write(new_content)
    print('Done!')
else:
    print('Old not found!')
    # Debug: find the actual content
    idx = content.find(b'def _build_delta')
    if idx >= 0:
        print('Found at:', idx)
        print(repr(content[idx:idx+500]))