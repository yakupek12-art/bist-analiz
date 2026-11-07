# Fix the syntax error in parallel_agents.py
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the problematic area and rewrite it cleanly
# Find the degerleme-ajani entry end and teknik-ajani start
old_section = """    },
    
    'teknik-ajani': {"""

new_section = """},
    
    'teknik-ajani': {"""

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

if '},\n\n    \'teknik-ajani\': {' in content:
    content = content.replace('},\n\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {')
    with open('parallel_agents.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Pattern not found")
    # Try alternative
    if '},\n\n    \'teknik-ajani\': {' in content:
        content = content.replace('},\n\n    \'teknik-ajani\': {', '},\n\n    \'teknik-ajani\': {')
        with open('parallel_agents.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed with alt pattern!")
    else:
        print("Pattern not found")