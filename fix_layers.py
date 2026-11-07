with open('layers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the hendek-ajani user_template ending - add missing closing triple quotes
# Find the pattern where the string ends with 'Gercekce: ..."' but missing closing triple quotes
import re

# Find the pattern: 'Gercekce: ..."        },' and add missing """
pattern = r'(Gercekce: \.\.\."\s*\n\s*\},)'
content = re.sub(pattern, r'\1\n        """', content)

# Also check for other similar patterns and fix them
# Look for patterns where a triple-quoted string ends without closing """
patterns = [
    (r'(Gercekce: \.\.\."\s*\n\s*\},)', r'\1\n        """'),
    (r'(Gercekce: \.\.\."\s*\n\s*})', r'\1\n        """'),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

with open('layers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed layers.py')