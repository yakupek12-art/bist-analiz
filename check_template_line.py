with open('C:/Users/PC/OneDrive/Belgeler/Varsayılan Proje/parallel_agents.py', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.find('REPORT_TEMPLATE = """')
if start >= 0:
    end = content.find('"""', start + 20)
    template = content[start:end+3]
    lines = template.split('\n')
    print(f'Template has {len(lines)} lines')
    for i, line in enumerate(lines):
        if i >= 145 and i <= 155:
            print(f'{i+1}: {line}')