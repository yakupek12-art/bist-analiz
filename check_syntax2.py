import ast

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

try:
    ast.parse(content)
    print('Syntax OK')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}, offset {e.offset}: {e.msg}')
    with open('parallel_agents.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
        print(f'{i+1}: {lines[i].rstrip()}')