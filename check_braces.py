with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find AGENT_PROMPTS start
idx = content.find('AGENT_PROMPTS = {')
print(f'AGENT_PROMPTS starts at: {idx}')

# Count braces from AGENT_PROMPTS start
brace_count = 0
in_string = False
escape_next = False
for i in range(content.find('AGENT_PROMPTS = {'), len(content)):
    c = content[i]
    if not in_string:
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                print(f'AGENT_PROMPTS ends at position {i}')
                print(f'Next 20 chars: {repr(content[i:i+20])}')
                break
        if content[i] == '"' and not escape_next:
            in_string = True
        elif c == '"' and escape_next:
            in_string = False
        elif c == '\\' and not in_string:
            escape_next = True
        else:
            escape_next = False
    else:
        if c == '"' and not escape_next:
            in_string = False
        elif c == '\\' and not in_string:
            escape_next = True
        else:
            escape_next = False

# Check if there's a comma after the closing brace of AGENT_PROMPTS
end_idx = content.find('}\n\n# Layer', content.find('AGENT_PROMPTS = {'))
if end_idx == -1:
    end_idx = content.find('}\n\n# Layer')
if end_idx != -1:
    print(f'Found end at {end_idx}')
    print(f'Context: {repr(content[end_idx:end_idx+50])}')
    # Check if there's a comma after the closing brace
    if end_idx + 1 < len(content) and content[end_idx+1] != ',':
        print('WARNING: Missing comma after AGENT_PROMPTS closing brace!')
    else:
        print('Comma found after AGENT_PROMPTS closing brace')