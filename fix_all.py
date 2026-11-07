# Fix all syntax issues in parallel_agents.py
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Replace double commas
content = content.replace('},\r\n,', '},\r\n')
content = content.replace('},\r\n,', '},\r\n')
content = content.replace('},\n,', '},\n')
content = content.replace('},\n,', '},\n')

# Fix missing comma before teknik-ajani
content = content.replace('},\n\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {')

# Fix any remaining double commas
import re
content = re.sub(r'\},\s*,\s*\n', '},\n', content)
content = re.sub(r'\},\s*,\s*\n', '},\n', content)

# Write back
with open('parallel_agents.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")