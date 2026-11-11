import urllib.request
import json

test_models = ['gh/gpt-4o-mini', 'kc/google/gemini-2.5-flash', 'ollama/gemma4:31b-cloud', 'kc/deepseek/deepseek-chat']
for m in test_models:
    payload = {
        'model': m,
        'messages': [{'role': 'user', 'content': 'Say hi in 3 words'}],
        'temperature': 0.1
    }
    req = urllib.request.Request(
        'http://localhost:20128/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': 'Bearer sk-9router-local', 'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            content = data['choices'][0]['message']['content'].strip()
            print(f'Model {m}: SUCCESS -> "{content}"')
    except Exception as e:
        print(f'Model {m}: ERROR -> {e}')
