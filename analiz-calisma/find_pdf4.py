import re
with open('analiz-calisma/ASELS-veri/kap_test.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Tüm href/src/data-* attribute'larını topla
attrs = re.findall(r'(href|src|data-[\w-]+)=["\']([^"\']+)["\']', html)
urls = set()
for attr, val in attrs:
    if val and ('pdf' in val.lower() or 'bildirim' in val.lower() or val.endswith('.pdf')):
        urls.add(val)

for u in sorted(urls):
    print(u)

print("\n--- Tüm .pdf geçenler ---")
for m in re.findall(r'[^"\'\s]+\.pdf', html, re.I):
    print(m)