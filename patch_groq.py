import re
import traceback

def fix_groq(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix the syntax error const API_KEY = ;
        # The user's code might literally be `const API_KEY = ;`
        content = re.sub(r'const API_KEY\s*=\s*(.*?);', 
                         r'const API_KEY = localStorage.getItem("GROQ_API_KEY") || prompt("Groq API Key (gsk_...):");\nif(!localStorage.getItem("GROQ_API_KEY") && API_KEY) localStorage.setItem("GROQ_API_KEY", API_KEY);', content)

        # Update API_URL
        content = re.sub(r'const API_URL\s*=\s*".*?";', 
                         r'const API_URL = "https://api.groq.com/openai/v1/chat/completions";', content)

        # Update MODEL
        content = re.sub(r'const MODEL\s*=\s*".*?";', 
                         r'const MODEL = "llama3-70b-8192";', content)

        # Update callClaude function logic for Groq/OpenAI compatible shape
        old_fetch = r"""  const response = await fetch\(API_URL, \{[\s\S]*?body: JSON\.stringify\(\{[\s\S]*?model: MODEL,[\s\S]*?max_tokens: 1000,[\s\S]*?system: systemPrompt,[\s\S]*?messages: \[\{ role: 'user', content: userMessage \}\][\s\S]*?\}\)[\s\S]*?\}\);"""
        
        new_fetch = """  const response = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY },
    body: JSON.stringify({
      model: MODEL,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage }
      ]
    })
  });"""
        content = re.sub(old_fetch, new_fetch, content)

        # Update data extraction
        old_data = r"const text = data\.content\.map\(b => b\.type === 'text' \? b\.text : ''\)\.join\(''\);"
        new_data = r"const text = data.choices[0].message.content;"
        content = re.sub(old_data, new_data, content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched Groq in {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}")
        traceback.print_exc()

fix_groq('d:/NG/neuroguard (1).html')
fix_groq('d:/NG/NeuroGuard — AI Predictive Maintenance.html')
