import ast
import sys

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

try:
    ast.parse(content)
    print('Syntax OK')
    sys.exit(0)
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}, offset {e.offset}: {e.msg}')
    with open('parallel_agents.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(max(0, e.lineno-5), min(len(lines), e.lineno+3)):
        marker = '>>>' if i+1 == e.lineno else '   '
        print(f'{marker} {i+1:4d}: {lines[i].rstrip()}')
    sys.exit(1)