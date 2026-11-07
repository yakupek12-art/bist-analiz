import urllib.request, json, re

# ASELS için bildirim ara - doğru API kullanımı
url = 'https://www.kap.org.tr/tr/api/disclosures'
data = {
    "companyQuery": {"text": "Aselsan"},
    "disclosureType": "FR",  # Finansal Rapor
    "submit": "Getir"
}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.load(resp)
    print(f'Toplam finansal rapor bildirimi: {len(result)}')
    for i, r in enumerate(result[:10]):
        print(f'{i+1}. {r.get("disclosureDate")} - {r.get("disclosureTitle")} - ID: {r.get("disclosureId")}')
except Exception as e:
    print(f'Hata: {e}')