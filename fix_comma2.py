with open('parallel_agents.py', 'rb') as f:
    content = f.read()

# Find the end of AGENT_PROMPTS
brace_count = 0
in_string = False
escape_next = False
end_idx = -1

for i in range(content.find(b'AGENT_PROMPTS = {'), len(content)):
    c = content[i:i+1]
    if not in_string:
        if c == b'{':
            brace_count += 1
        elif c == b'}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break
        if c == b'"' and not escape_next:
            in_string = True
        elif c == b'"' and escape_next:
            in_string = False
        elif c == b'\\' and not escape_next:
            escape_next = True
        else:
            escape_next = False
    else:
        if c == b'"' and not escape_next:
            in_string = False
        elif c == b'\\' and not in_string:
            escape_next = True
        else:
            escape_next = False

print(f'AGENT_PROMPTS ends at byte {end_idx}')
print(f'Next 30 bytes: {content[end_idx:end_idx+30]!r}')
print(f'Byte after closing brace: {content[end_idx+1:end_idx+2]!r}')

# Check if comma exists
if content[end_idx+1:end_idx+2] != b',':
    print('Adding comma...')
    new_content = content[:end_idx+1] + b',' + content[end_idx+1:]
    with open('parallel_agents.py', 'wb') as f:
        f.write(content[:end_idx+1] + b',' + content[end_idx+1:])
    print('Fixed!')
else:
    print('Comma already present')