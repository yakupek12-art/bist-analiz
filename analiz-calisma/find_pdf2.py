import re
with open('analiz-calisma/ASELS-veri/kap_test.html', 'r', encoding='utf-8') as f:
    html = f.read()
# Farklı patternler dene
patterns = [
    r'href=["\']([^"\']*\.pdf)["\']',
    r'src=["\']([^"\']*\.pdf)["\']',
    r'data-pdf=["\']([^"\']*)["\']',
    r'\.pdf',
    r'Bildirim.*?pdf',
]
for pat in patterns:
    matches = re.findall(pat, html, re.I)
    if matches:
        print(f'Pattern: {pat}')
        for m in matches[:5]:
            print(f'  -> {m[:100]}')
        print()