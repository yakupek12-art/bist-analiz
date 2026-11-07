# Fix the missing comma in parallel_agents.py
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the teknik-ajani entry
idx = content.find("'teknik-ajani': {")
if idx == -1:
    # Try with single quotes
    idx = content.find("'teknik-ajani': {")
    if idx == -1:
        idx = content.find("'teknik-ajani': {")

if idx == -1:
    print("Could not find teknik-ajani entry")
    exit(1)

# Find the previous entry's closing brace
# Look backwards from the teknik-ajani entry
prev_end = content.rfind('},\n\n    ', 0, idx)
if prev_end == -1:
    prev_end = content.rfind('},\n\n    ', 0, idx)

if prev_end == -1:
    print("Could not find previous entry end")
    exit(1)

# Check if there's a comma after the previous entry's closing brace
check_pos = prev_end + 3  # after '},\n'
if content[prev_end:prev_end+4] != '},\n':
    print(f"Found issue at position {prev_end}: missing comma or wrong format")
    print(f"Context: {repr(content[prev_end:prev_end+20])}")
    
    # Fix: ensure there's a comma after the closing brace
    new_content = content[:prev_end+2] + ',\n' + content[prev_end+2:]
    with open('parallel_agents.py', 'w', encoding='utf-8') as f:
        f.write(content[:prev_end+2] + ',\n' + content[prev_end+2:])
    print("Fixed: Added missing comma after previous entry")
else:
    print("Comma already present")

print("Done")