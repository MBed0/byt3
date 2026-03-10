"""👾 Byte — Discord Agent"""
import json, requests
from pathlib import Path

def load_config():
    with open(Path(__file__).parent.parent / "config.json") as f:
        return json.load(f)

def send_discord_message(channel: str, message: str) -> str:
    cfg = load_config()
    token = cfg.get("api_keys",{}).get("discord_token","")
    webhook = cfg.get("api_keys",{}).get("discord_webhook","")
    if not token and not webhook:
        return "❌ Set Discord token/webhook in Integrations settings"
    if webhook:
        r = requests.post(webhook, json={"content": f"👾 {message}", "username": "Byte"})
        return "✅ Sent via webhook" if r.status_code in [200,204] else f"❌ {r.status_code}"
    if token:
        h = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
        guilds = requests.get("https://discord.com/api/v10/users/@me/guilds", headers=h).json()
        for g in guilds[:5]:
            chs = requests.get(f"https://discord.com/api/v10/guilds/{g['id']}/channels", headers=h).json()
            for ch in chs:
                if ch.get("name","").lower() == channel.lower() and ch.get("type") == 0:
                    r = requests.post(f"https://discord.com/api/v10/channels/{ch['id']}/messages", headers=h, json={"content": f"👾 {message}"})
                    return f"✅ Sent to #{channel}" if r.status_code == 200 else f"❌ {r.status_code}"
        return f"❌ Channel #{channel} not found"
