import tokenize
import sys

with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

try:
    compile(content, 'parallel_agents.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}, offset {e.offset}: {e.msg}')
    with open('parallel_agents.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(max(0, e.lineno-10), min(len(open('parallel_agents.py', 'r', encoding='utf-8').readlines()), e.lineno+5)):
        marker = '>>>' if i+1 == e.lineno else '   '
        print(f'{marker} {e.lineno if i+1 == e.lineno else i+1:4d}: {open("parallel_agents.py", "r", encoding="utf-8").readlines()[i].rstrip()}')
    
    # Also check tokenization
    try:
        tokens = list(tokenize.generate_tokens(open('parallel_agents.py', 'r', encoding='utf-8').readline))
        print(f'Total tokens: {len(tokens)}')
        # Look for tokens around line 444
        for tok in tokens:
            if tok.start[0] == 444:
                print(f'Token at line 444: {tok}')
                break
    except Exception as e:
        print(f'Tokenize error: {e}')