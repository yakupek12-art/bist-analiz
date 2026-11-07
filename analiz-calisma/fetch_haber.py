#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haber Verisi Çekici — Google News RSS
"""

import sys, re, xml.etree.ElementTree as ET

symbol = sys.argv[1] if len(sys.argv) > 1 else 'TUPRS'

print(f"Haber verisi çekiliyor: {symbol}")

try:
    import urllib.request
    url = f"https://news.google.com/rss/search?q={symbol}&hl=tr&gl=TR&ceid=TR:tr"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req, timeout=15)
    content = response.read()
    
    # UTF-16 decode dene
    try:
        text = content.decode('utf-16')
    except:
        text = content.decode('utf-8', errors='ignore')
    
    # Regex ile item'leri bul
    items = re.findall(r'<item>.*?</item>', text, re.DOTALL)
    
    count = 0
    with open('veri/haberler.txt', 'w', encoding='utf-8') as f:
        for item in items:
            # Title
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item)
            title = (title_match.group(1) or title_match.group(2) or '').strip() if title_match else ''
            
            # Source
            source_match = re.search(r'<source[^>]*><!\[CDATA\[(.*?)\]\]></source>|<source[^>]*>(.*?)</source>', item)
            source = (source_match.group(1) or source_match.group(2) or '').strip() if source_match else ''
            
            # PubDate
            pub_match = re.search(r'<pubDate><!\[CDATA\[(.*?)\]\]></pubDate>|<pubDate>(.*?)</pubDate>', item)
            pub = (pub_match.group(1) or pub_match.group(2) or '').strip() if pub_match else ''
            
            # Link
            link_match = re.search(r'<link><!\[CDATA\[(.*?)\]\]></link>|<link>(.*?)</link>', item)
            link = (link_match.group(1) or link_match.group(2) or '').strip() if link_match else ''
            
            # Description
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>', item)
            desc = (desc_match.group(1) or desc_match.group(2) or '').strip() if desc_match else ''
            
            if title:
                f.write(f'{title} | {source} | {pub} | {link} | {desc}\n')
                count += 1
    
    print(f"Haber başlığı: {count}")
    
except Exception as e:
    print(f"Haber çekme hatası: {e}")
    with open('veri/haberler.txt', 'w') as f:
        f.write(f'Haber çekilemedi: {e}')