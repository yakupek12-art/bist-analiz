# Fix the braces in parallel_agents.py
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines, 1):
    if i == 525:  # Line 525: '},\n'
        print(f"Skipping line {i}: {repr(lines[i-1])}")
        continue  # Skip this line
    elif i == 527:  # Line 527: '}\n'
        print(f"Skipping line {i}: {repr(lines[i-1])}")
        continue  # Skip this line
    new_lines.append(lines[i-1])

with open('parallel_agents.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)  # Write original lines but we'll filter
    
# Actually, let's rebuild the list properly
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines, 1):
    if i == 525 or i == 527:
        print(f"Skipping line {i}: {repr(lines[i-1])}")
        continue
    new_lines.append(line)

with open('parallel_agents.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed!")