import re

file_paths = [
    r'd:\NG\neuroguard (1).html',
    r'd:\NG\NeuroGuard — AI Predictive Maintenance.html'
]

for f in file_paths:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            txt = file.read()
        
        # Replace 30000) with 60000) for intervals
        txt = txt.replace('30000)', '60000)')
        # Replace 30000 -> 60000 globally just in case there are other occurences in setIntervals
        txt = re.sub(r'(?<=,\s)30000(?=\))', '60000', txt)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(txt)
        print(f"Updated {f}")
    except Exception as e:
        print(f"Failed to update {f}: {e}")
