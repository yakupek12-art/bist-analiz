# Fix all syntax issues in parallel_agents.py
import re

with open('parallel_agents.py', 'rb') as f:
    content = f.read()

# Fix 1: Ensure comma before teknik-ajani entry
content = content.replace(
    b'},\r\n\r\n    \'teknik-ajani\': {',
    b'},\r\n\r\n    \'teknik-ajani\': {'
)

# Fix double commas
content = content.replace(b'},\r\n,', b',\r\n')
content = content.replace(b'},\r\n,', b',\r\n')
content = content.replace(b'},\n,', b',\n')
content = content.replace(b'},\n,', b',\n')

# Fix any double commas
content = re.sub(rb'\},\s*,\s*\r?\n', b'},\r\n', content)
content = content.replace(b'},\r\n,', b',\r\n')
content = content.replace(b'},\r\n,', b',\r\n')
content = content.replace(b'},\n,', b',\n')
content = content.replace(b'},\n,', b',\n')

# Write back
with open('parallel_agents.py', 'wb') as f:
    f.write(content)

print("Fixed!")