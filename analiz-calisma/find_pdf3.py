import re, json
with open('analiz-calisma/ASELS-veri/kap_test.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Script tag'lerinde JSON data ara
script_pattern = r'<script[^>]*>(.*?)</script>'
scripts = re.findall(script_pattern, html, re.DOTALL)
for i, script in enumerate(scripts):
    if 'pdf' in script.lower() or 'bildirim' in script.lower():
        # JSON objeleri ara
        json_matches = re.findall(r'\{[^{}]*"pdf"[^{}]*\}', script)
        for m in json_matches:
            print(f"Script {i}: {m[:200]}")
        # URL pattern
        urls = re.findall(r'https?://[^"\'\s]+\.pdf', script)
        for u in urls:
            print(f"  PDF URL: {u}")