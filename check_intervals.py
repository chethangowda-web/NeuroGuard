import re
with open(r'd:\NG\neuroguard (1).html', 'r', encoding='utf-8') as f:
    content = f.read()
    matches = re.findall(r'setInterval\s*\(.*?,(.*?)(\)|;)', content)
    for m in matches:
        print(f"Interval found: {m[0].strip()}")
