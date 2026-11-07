# Remove extra closing braces
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 525, 527, 528 (1-indexed)
# Line 525: '},\n'
# Line 527: '}\n'
# Line 528: '\n'

lines_to_remove = {525, 527, 528}

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines, 1):
    if i in (525, 527, 528):
        print(f"Removing line {i}: {repr(lines[i-1])}")
        continue
    new_lines.append(line)

with open('parallel_agents.py', 'w', encoding='utf-8') as f:
    f.writelines([lines[i-1] for i in range(1, len(open('parallel_agents.py', 'r', encoding='utf-8').readlines())+1) if i not in (525, 527, 528)])

print("Fixed!")