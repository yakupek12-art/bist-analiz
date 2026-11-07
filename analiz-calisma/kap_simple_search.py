import urllib.request, json

# Daha basit sorgu - sadece companyQuery
url = 'https://www.kap.org.tr/tr/api/disclosures'
data = {
    "companyQuery": {"text": "Aselsan"},
    "submit": "Getir"
}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.load(resp)
    print(f'Toplam: {len(result)}')
    for i, r in enumerate(result[:10]):
        print(f'{i+1}. {r.get("disclosureDate")} - {r.get("disclosureTitle")} - ID: {r.get("disclosureId")} - Type: {r.get("disclosureType")}')
except Exception as e:
    print(f'Hata: {e}')