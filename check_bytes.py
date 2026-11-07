with open('parallel_agents.py', 'rb') as f:
    content = f.read()

idx = content.find(b'teknik-ajani')
idx2 = content.find(b'teknik-ajani', idx + 1)
if idx2 != -1:
    chunk = content[idx2-200:idx2+200]
    for i, b in enumerate(chunk):
        if b > 127 or b in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31):
            c = chr(chunk[i]) if 32 <= chunk[i] < 127 else '?'
            print(f'Offset {idx2-200+i}: {hex(chunk[i])} ({chr(chunk[i]) if 32 <= chunk[i] < 127 else "?"})')