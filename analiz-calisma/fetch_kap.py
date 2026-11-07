import urllib.request, re, os, json

# ASELS son bildirimleri KAP'tan çek
url = 'https://www.kap.org.tr/tr/api/disclosures'
data = {
    'companyQuery': {'text': 'Aselsan'},
    'submit': 'Getir'
}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=30)
result = json.load(resp)
print(f'Toplam bildirim: {len(result)}')
for i, r in enumerate(result[:10]):
    print(f'{i+1}. {r.get("disclosureDate")} - {r.get("disclosureTitle")} - {r.get("disclosureId")}')