"""
🐦‍⬛ Byte Core — Ollama connection + Action Engine
"""
import json, re, subprocess, sys, os, datetime, requests, webbrowser
from pathlib import Path

BASE        = Path(__file__).parent
CONFIG_PATH = BASE / "config.json"

DEFAULT_CONFIG = {
    "bot_name": "Byte",
    "emoji": "🐦‍⬛",
    "model": "gemma3:1b",
    "ollama_path": "ollama",
    "ollama_host": "http://localhost:11434",
    "theme": "dark",
    "user_name": "User",
    "port": 7821,
    "contacts": {},
    "api_keys": {
        "discord_token": "",
        "discord_webhook": "",
        "telegram_token": "",
        "telegram_chat_id": ""
    },
    "chrome_path": "",
    "whatsapp_profile": "./whatsapp_session",
    "auto_start_ollama": True,
    "dataset_path": "./datasets/byte_dataset.jsonl",
    "system_prompt": "You are Byte, an advanced local AI assistant. Be direct, efficient, and helpful. Keep responses concise unless explaining code. Always respond in the same language the user writes in.\n\nACTION RULES: ONLY use action tags like [ACTION: OPEN_URL|...] when the user explicitly asks to perform that action. For normal conversation, respond with plain text only."
}

def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # Fill in any missing keys from defaults
    changed = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
            changed = True
    if changed:
        save_config(cfg)
    return cfg

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# ── Ollama ────────────────────────────────────────────────────────────────────

def ollama_running():
    try:
        cfg = load_config()
        r = requests.get(f"{cfg['ollama_host']}/api/tags", timeout=3)
        return r.status_code == 200
    except:
        return False

def start_ollama():
    cfg = load_config()
    try:
        kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if sys.platform == "win32":
            kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.Popen([cfg.get("ollama_path","ollama"), "serve"], **kw)
        import time; time.sleep(2)
        return ollama_running()
    except:
        return False

def list_local_models():
    cfg = load_config()
    try:
        r = requests.get(f"{cfg['ollama_host']}/api/tags", timeout=5)
        return [m["name"] for m in r.json().get("models", [])]
    except:
        return []

def pull_model(model_name: str):
    cfg = load_config()
    try:
        subprocess.run([cfg.get("ollama_path","ollama"), "pull", model_name], check=True)
        return True
    except:
        return False

def chat_stream(messages: list, weather_ctx: str = ""):
    """
    Generator: yields text tokens.
    weather_ctx: optional weather string injected into system prompt.
    """
    cfg         = load_config()
    sys_content = cfg["system_prompt"]
    if weather_ctx:
        sys_content += weather_ctx

    system   = {"role": "system", "content": sys_content}
    all_msgs = [system] + messages

    # Detect if last user message requests an action
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = m.get("content","").lower()
            break

    action_keywords = [
        "open chrome","open browser","send whatsapp","send discord",
        "send telegram","open app","run command","open url",
    ]
    expects_action = any(kw in last_user for kw in action_keywords)

    try:
        resp = requests.post(
            f"{cfg['ollama_host']}/api/chat",
            json={
                "model":    cfg["model"],
                "messages": all_msgs,
                "stream":   True,
                "options":  {
                    "num_keep":    24,
                    "temperature": cfg.get("temperature", 0.7),
                }
            },
            stream=True,
            timeout=180
        )

        buffer = ""
        for raw in resp.iter_lines():
            if not raw:
                continue
            try:
                data  = json.loads(raw)
                token = data.get("message", {}).get("content", "")
                if token:
                    buffer += token
                    if "[ACTION:" not in buffer:
                        yield buffer
                        buffer = ""
                    elif "]" in buffer:
                        if expects_action:
                            yield buffer
                        else:
                            cleaned = ACTION_RE.sub("", buffer).strip()
                            if cleaned:
                                yield cleaned
                        buffer = ""
                if data.get("done"):
                    if buffer:
                        cleaned = (ACTION_RE.sub("", buffer).strip()
                                   if not expects_action else buffer)
                        if cleaned:
                            yield cleaned
                    break
            except Exception:
                pass

    except Exception as e:
        yield f"\n\n❌ Ollama error: {e}"


# ── Action Engine ─────────────────────────────────────────────────────────────

ACTION_RE = re.compile(r'\[ACTION:\s*([^\]]+)\]')

def parse_params(parts):
    p = {}
    for part in parts:
        if ":" in part:
            k, _, v = part.partition(":")
            p[k.strip().lower()] = v.strip()
    return p

def execute_action(action_str: str) -> str:
    parts = [x.strip() for x in action_str.split("|")]
    atype = parts[0].upper()
    cfg   = load_config()

    try:
        if atype == "OPEN_URL":
            url = parts[1] if len(parts)>1 else ""
            webbrowser.open(url)
            return f"✅ Opened: {url}"

        elif atype == "OPEN_BROWSER":
            app = parts[1] if len(parts)>1 else "chrome"
            _launch_app(app, cfg)
            return f"✅ Launched {app}"

        elif atype == "OPEN_APP":
            app = parts[1] if len(parts)>1 else ""
            _launch_app(app, cfg)
            return f"✅ Launched {app}"

        elif atype == "WHATSAPP_SEND":
            params = parse_params(parts[1:])
            from agents.whatsapp_agent import send_whatsapp_message
            return send_whatsapp_message(params.get("contact",""), params.get("message",""))

        elif atype == "DISCORD_SEND":
            params = parse_params(parts[1:])
            from agents.discord_agent import send_discord_message
            return send_discord_message(params.get("channel","general"), params.get("message",""))

        elif atype == "TELEGRAM_SEND":
            params = parse_params(parts[1:])
            from agents.telegram_agent import send_telegram_message
            return send_telegram_message(params.get("message",""))

        elif atype == "GET_TIME":
            return datetime.datetime.now().strftime("%H:%M:%S — %d/%m/%Y")

        elif atype == "RUN_CMD":
            cmd = parts[1] if len(parts)>1 else ""
            out = subprocess.run(cmd, shell=True, capture_output=True,
                                 text=True, timeout=15)
            return (out.stdout or out.stderr or "done")[:500]

        else:
            return f"Unknown action: {atype}"

    except Exception as e:
        return f"❌ {e}"

def run_actions(text: str) -> list:
    results = []
    for m in ACTION_RE.findall(text):
        res = execute_action(m.strip())
        results.append({"action": m.strip(), "result": res})
    return results

def _launch_app(name: str, cfg: dict):
    name = name.lower()
    if sys.platform == "win32":
        paths = {
            "chrome": cfg.get("chrome_path") or
                      r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        }
        cmd = paths.get(name, name)
        subprocess.Popen(cmd, shell=True)
    elif sys.platform == "darwin":
        apps = {"chrome": "Google Chrome", "code": "Visual Studio Code"}
        subprocess.Popen(["open", "-a", apps.get(name, name)])
    else:
        subprocess.Popen([name])
