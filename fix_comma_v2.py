# Fix the syntax error in parallel_agents.py by rewriting the problematic section
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the problematic section
# The issue is likely a missing comma or invalid character around line 444

old_section = '''    },
    
    'teknik-ajani': {'''

new_section = '''},
    
    'teknik-ajani': {'''

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Try multiple possible patterns
patterns = [
    ('},\n\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {'),
    ('},\n\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {'),
    ('},\r\n\r\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {'),
]

fixed = False
for old, new in [('},\n\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {'),
                  ('},\r\n\r\n    \'teknik-ajani\': {', '},\r\n\r\n    \'teknik-ajani\': {'),
                  ('},\n\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {')]:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed with pattern: {repr(old)} -> {repr(new)}")
        with open('parallel_agents.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed!")
        break
else:
    print("No matching pattern found")
    # Print context around the error
    idx = content.find("'teknik-ajani': {")
    if idx != -1:
        print(repr(content[idx-200:idx+200]))