#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix syntax errors in parallel_agents.py"""
import re

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Ensure AGENT_PROMPTS dict ends with a comma before next section
# Find the end of AGENT_PROMPTS dict
idx = content.find('AGENT_PROMPTS = {')
if idx == -1:
    print("AGENT_PROMPTS not found")
    exit(1)

# Find the end of AGENT_PROMPTS dict
brace_count = 0
in_string = False
escape_next = False
end_idx = -1

for i in range(content.find('AGENT_PROMPTS = {'), len(content)):
    c = content[i]
    if not in_string:
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break
    if not in_string:
        if c == '"' and not escape_next:
            in_string = True
        elif c == '"' and escape_next:
            in_string = False
        elif c == '\\' and not escape_next:
            escape_next = True
        else:
            escape_next = False
    else:
        if c == '"' and not escape_next:
            in_string = False
        elif c == '\\' and not escape_next:
            escape_next = True
        else:
            escape_next = False

# Check if there's a comma after the closing brace of AGENT_PROMPTS
next_char = content[i+1] if i+1 < len(content) else ''
print(f"AGENT_PROMPTS ends at {i}, next char: {repr(content[i+1:i+10])}")

# Check if there's a comma after the closing brace of AGENT_PROMPTS
if i+1 < len(content) and content[i+1] != ',':
    print("WARNING: Missing comma after AGENT_PROMPTS closing brace")

# Find the teknik-ajani line
lines = content.split('\n')
for i, line in enumerate(open('parallel_agents.py', 'r', encoding='utf-8').readlines(), 1):
    if "'teknik-ajani': {" in line:
        print(f"Found teknik-ajani at line {i+1}: {line.strip()}")
        # Check previous line for comma
        if i > 1:
            prev_line = open('parallel_agents.py', 'r', encoding='utf-8').readlines()[i-2].rstrip()
            print(f"Previous line: {prev_line}")
            if not prev_line.rstrip().endswith(','):
                print("WARNING: Previous line doesn't end with comma!")
            break

print("Done")