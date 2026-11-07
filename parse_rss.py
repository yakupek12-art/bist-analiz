import re

with open('veri/haberler.xml', 'rb') as f:
    content = f.read()

# UTF-16 decode
content = content.decode('utf-16', errors='ignore')

# Find all items
items = re.findall(r'<item>.*?</item>', content, re.DOTALL)

count = 0
with open('veri/haberler.txt', 'w', encoding='utf-8') as f:
    for item in items:
        # Extract title, source, pubDate, link, description
        title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
        source_match = re.search(r'<source[^>]*><!\[CDATA\[(.*?)\]\]></source>|<source[^>]*>(.*?)</source>', item)
        pub_match = re.search(r'<pubDate><!\[CDATA\[(.*?)\]\]></pubDate>|<pubDate>(.*?)</pubDate>', item)
        link_match = re.search(r'<link><!\[CDATA\[(.*?)\]\]></link>|<link>(.*?)</link>', item)
        desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>', item)
        
        t = (title_match.group(1) or title_match.group(2) or '').strip() if title_match else ''
        s = (source_match.group(1) or source_match.group(2) or '').strip() if source_match else ''
        p = (pub_match.group(1) or pub_match.group(2) or '').strip() if pub_match else ''
        l = (link_match.group(1) or link_match.group(2) or '').strip() if link_match else ''
        d = (desc_match.group(1) or desc_match.group(2) or '').strip() if desc_match else ''
        
        if t or d:
            f.write('{} | {} | {} | {} | {}\n'.format(t, s, p, l, d))
            count += 1

print('Haber basligi:', count)