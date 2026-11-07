with open('parallel_agents.py', 'rb') as f:
    content = f.read()

# Find AGENT_PROMPTS start
idx = content.find(b'AGENT_PROMPTS = {')
print(f'AGENT_PROMPTS starts at: {idx}')

# Find the end of AGENT_PROMPTS dict
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
                print(f'AGENT_PROMPTS ends at byte {i}')
                print(f'Next 50 bytes: {content[i:i+50]!r}')
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

# Check if there's a comma after the closing brace
if end_idx + 1 < len(content):
    next_char = content[end_idx+1:end_idx+10]
    print(f'Bytes after closing brace: {content[end_idx:end_idx+10]!r}')
    if content[end_idx+1:end_idx+2] != b',':
        print('WARNING: Missing comma after AGENT_PROMPTS closing brace!')
    else:
        print('Comma found after AGENT_PROMPTS closing brace')

# Also check the teknik-ajani area
idx2 = content.find(b'teknik-ajani', content.find(b'AGENT_PROMPTS = {'))
print(f'First teknik-ajani at: {content.find(b"teknik-ajani")}')
idx2 = content.find(b'teknik-ajani', content.find(b'teknik-ajani') + 1)
print(f'Second teknik-ajani at: {idx2}')
if idx2 != -1:
    print(repr(content[idx2-200:idx2+500]))