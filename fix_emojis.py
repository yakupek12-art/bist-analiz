# -*- coding: utf-8 -*-
"""
Emoji karakterlerini ASCII ile değiştir
"""
with open('run_direct_analiz.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Emoji -> ASCII değiştirme
replacements = {
    '🟢': '[YESIL]',
    '🟡': '[SARI]',
    '🔴': '[KIRMIZI]',
    '🟢': '[YESIL]',
    '🟡': '[SARI]',
    '🔴': '[KIRMIZI]',
}

for emoji, ascii_rep in replacements.items():
    content = content.replace(emoji, ascii_rep)

with open('run_direct_analiz.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Emoji karakterleri ASCII ile değiştirildi.")