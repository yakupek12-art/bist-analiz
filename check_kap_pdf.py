import requests, re

url = 'https://www.kap.org.tr/tr/Bildirim/1643239'
resp = requests.get(url, timeout=30)

# Find PDF links
pdfs = re.findall(r'href="([^"]*\.pdf[^"]*)"', resp.text)
print('PDF links:', pdfs)

# Check for all links
all_links = re.findall(r'href="([^"]*)"', resp.text)
for l in all_links[:30]:
    if '.pdf' in l or 'Attachment' in l or 'Ek' in l or 'indir' in l:
        print(l)