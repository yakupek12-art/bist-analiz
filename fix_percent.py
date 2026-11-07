with open('layers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix % characters in the template strings - replace % with %% to avoid format string issues
# Only replace % followed by digit or letter (format specifiers)
import re

# Replace % followed by digit or letter with %%
# But not already escaped %%
content = re.sub(r'(?<!%)%(?=\d|[a-zA-Z])', '%%', content)

with open('layers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed % characters in layers.py')