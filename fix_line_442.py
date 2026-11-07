# Fix the missing closing brace before 'teknik-ajani'
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with just ',' (line 442 in 1-indexed, so index 441)
for i, line in enumerate(lines):
    if line.strip() == ',' and i > 430 and i < 450:
        print(f"Line {i+1}: {repr(lines[i])}")
        # Fix: replace ',' with '},'
        lines[i] = '    },\n'
        print(f"Fixed line {i+1}")
        break

with open('parallel_agents.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed!")