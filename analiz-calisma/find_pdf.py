import re
with open('analiz-calisma/ASELS-veri/kap_test.html', 'r', encoding='utf-8') as f:
    html = f.read()
pdf_links = re.findall(r'href=["\']([^"\']*\.pdf)["\']', html, re.I)
for link in pdf_links:
    print(link)