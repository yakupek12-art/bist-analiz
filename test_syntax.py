with open('parallel_agents.py', 'rb') as f:
    content = f.read()

# Find the teknik-ajani entry
idx = content.find(b'teknik-ajani')
idx2 = content.find(b'teknik-ajani', idx + 1)
if idx2 != -1:
    start = max(0, idx2 - 200)
    end = min(len(content), idx2 + 500)
    chunk = content[idx2-200:idx2+500]
    print(repr(content[idx2-200:idx2+200]))