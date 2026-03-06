import json
import requests

def test_api(model_name):
    with open('src/apikey.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    api_key = config.get("api_keys", {}).get("gemini", "")

    url = "https://api.minimax.chat/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name, 
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Model: {model_name} -> Status: {resp.status_code}")
        if resp.status_code != 200:
            print("Response:", resp.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    for m in ["MiniMax-M2.5", "minimax-text-01", "MiniMax-Text-01"]:
        test_api(m)
