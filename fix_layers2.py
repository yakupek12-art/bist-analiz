with open('layers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The issue is that triple-quoted strings in the user_template fields are not properly closed
# Fix: Ensure each user_template ends with proper closing triple quotes

# Find all user_template patterns and fix them
import re

# Pattern: user_template ends with "Gercekce: ..." but missing closing """
# Fix: Add closing """ before the closing }, of the dictionary

# Pattern 1: hendek-ajani ends with "Gercekce: ..." but missing closing """
content = re.sub(
    r'(Gercekce: \.\.\."\s*\n\s*\})',
    r'\1\n        """',
    content
)

# Also check for other similar patterns in other layers
# Pattern: "Gercekce: ..." followed by }, but missing closing """
patterns = [
    (r'(Gercekce: \.\.\."\s*\n\s*\})', r'\1\n        """'),
    (r'(Gercekce: \.\.\."\s*\n\s*})', r'\1\n        """'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, r'\1\n        """', content)

with open('layers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed layers.py')