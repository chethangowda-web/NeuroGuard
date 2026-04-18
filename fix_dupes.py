def fix_dupes(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        idx = content.find('</html>')
        if idx != -1:
            clean_content = content[:idx + len('</html>\n')]
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            print(f"Fixed duplicates in {file_path}")
        else:
            print(f"No </html> found in {file_path}")
            
    except Exception as e:
        print(f"Error {file_path}: {e}")

fix_dupes(r'd:\NG\neuroguard (1).html')
fix_dupes(r'd:\NG\NeuroGuard — AI Predictive Maintenance.html')
