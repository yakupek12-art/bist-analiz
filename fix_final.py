# Fix the extra closing braces
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove lines 526, 527, 528 (1-indexed)
# Line 526: '},\n'
# Line 527: '\n'
# Line 528: '}\n'
# Line 529: '\n'
# These are the extra lines after the AGENT_CONFIGS dict closes

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines, 1):
    if i in (526, 527, 528, 529):  # 1-indexed
        print(f"Removing line {i}: {repr(lines[i-1])}")
        continue
    new_lines.append(lines[i-1])

with open('parallel_agents.py', 'w', encoding='utf-8') as f:
    f.writelines(lines[i-1] for i in range(1, len(open('parallel_agents.py', 'r', encoding='utf-8').readlines())+1) if i not in (526, 527, 528, 529))

print("Fixed!")