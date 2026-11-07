with open('parallel_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check lines around 444
for i in range(435, 455):
    line = open('parallel_agents.py', 'r', encoding='utf-8').readlines()[i-1].rstrip()
    marker = '>>>' if i == 444 else '   '
    print(f'{i:4d}: {marker} {i}: {line}')