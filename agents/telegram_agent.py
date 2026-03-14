"""🐦‍⬛ Byte — Telegram Agent"""
import json, requests
from pathlib import Path

def load_config():
    with open(Path(__file__).parent.parent / "config.json") as f:
        return json.load(f)

def send_telegram_message(message: str) -> str:
    cfg = load_config()
    token = cfg.get("api_keys",{}).get("telegram_token","")
    chat_id = cfg.get("api_keys",{}).get("telegram_chat_id","")
    if not token: return "❌ Set Telegram token in Integrations settings"
    if not chat_id: return "❌ Set Telegram chat_id in Integrations settings"
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": f"🐦‍⬛ {message}"})
    return "✅ Telegram sent" if r.status_code == 200 else f"❌ {r.json().get('description','error')}"
