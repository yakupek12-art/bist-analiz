# Fix the syntax error in parallel_agents.py
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The issue is likely a missing comma before 'teknik-ajani' entry in AGENT_PROMPTS
# Find the previous entry (degerleme-ajani) and ensure it ends with a comma

# Read the file
with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with 'teknik-ajani': {
for i, line in enumerate(lines):
    if "'teknik-ajani': {" in line and "'name'" not in line and '"name"' not in line and '"name"' not in line:
        teknik_line = i
        print(f"Found teknik-ajani at line {i+1}: {lines[i].rstrip()}")
        # Check previous lines for the previous entry
        for j in range(i-1, max(0, i-10), -1):
            line = lines[j].rstrip()
            if line.strip():
                print(f"Line {j+1}: {line}")
                if line.strip().endswith('},'):
                    print(f"  -> Previous entry ends with comma: {lines[j].rstrip()}")
                elif line.strip().endswith('},'):
                    print(f"  -> Found closing brace with comma at line {j+1}")
                elif line.strip().endswith('},'):
                    print(f"  -> Found closing brace with comma at line {j+1}")
                break
        break

# Also check if there's a missing comma before 'teknik-ajani'
# Find the line before 'teknik-ajani' that should have a comma
for i in range(len(lines)-1, -1, -1):
    if "'teknik-ajani': {" in lines[i]:
        # Check previous non-empty line
        for j in range(i-1, -1, -1):
            if lines[j].strip():
                prev_line = lines[j].rstrip()
                print(f"Previous non-empty line ({j+1}): {repr(lines[j])}")
                if not prev_line.rstrip().endswith(','):
                    print("  -> Missing comma after previous entry!")
                    # Fix: add comma after the previous entry's closing brace
                    lines[j] = lines[j].rstrip() + ',\n'
                    with open('parallel_agents.py', 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    print("Fixed: Added missing comma")
                    break
                break
        break