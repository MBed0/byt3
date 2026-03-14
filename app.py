"""
🐦‍⬛ Byte — Flask Web Server
Run: python app.py  OR  byte
"""
import json, sys, threading, time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import webbrowser

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from byte_core import (
    load_config, save_config, ollama_running, start_ollama,
    list_local_models, chat_stream, run_actions, pull_model
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "byte-secret-2026" # Change that

chat_sessions = {}  # session_id -> list of messages

# ── Pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("index.html", page="dashboard")

@app.route("/chat")
def chat_page():
    return render_template("index.html", page="chat")

@app.route("/models")
def models_page():
    return render_template("index.html", page="models")

@app.route("/settings")
def settings_page():
    return render_template("index.html", page="settings")

@app.route("/integrations")
def integrations_page():
    return render_template("index.html", page="integrations")

# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    cfg = load_config()
    running = ollama_running()
    models = list_local_models() if running else []
    return jsonify({
        "ollama": running,
        "model": cfg["model"],
        "models": models,
        "emoji": cfg["emoji"],
        "bot_name": cfg["bot_name"],
        "user_name": cfg["user_name"],
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    session_id = data.get("session_id", "default")
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "empty message"}), 400

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    chat_sessions[session_id].append({"role": "user", "content": user_msg})

    def generate():
        full = []
        for token in chat_stream(chat_sessions[session_id]):
            full.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"

        full_text = "".join(full)
        chat_sessions[session_id].append({"role": "assistant", "content": full_text})

        # Run actions
        actions = run_actions(full_text)
        if actions:
            yield f"data: {json.dumps({'actions': actions})}\n\n"

        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    data = request.json or {}
    sid = data.get("session_id", "default")
    chat_sessions.pop(sid, None)
    return jsonify({"ok": True})

@app.route("/api/models")
def api_models():
    models = list_local_models()
    cfg = load_config()
    return jsonify({"models": models, "current": cfg["model"]})

@app.route("/api/models/select", methods=["POST"])
def api_select_model():
    data = request.json
    model = data.get("model", "")
    if not model:
        return jsonify({"error": "no model"}), 400
    cfg = load_config()
    cfg["model"] = model
    save_config(cfg)
    return jsonify({"ok": True, "model": model})

@app.route("/api/models/pull", methods=["POST"])
def api_pull_model():
    data = request.json
    model = data.get("model", "")

    def do_pull():
        pull_model(model)

    t = threading.Thread(target=do_pull)
    t.daemon = True
    t.start()
    return jsonify({"ok": True, "message": f"Pulling {model} in background..."})

@app.route("/api/config", methods=["GET"])
def api_get_config():
    cfg = load_config()
    # Don't expose full system prompt in one call, keep it clean
    return jsonify(cfg)

@app.route("/api/config", methods=["POST"])
def api_save_config():
    data = request.json
    cfg = load_config()
    allowed = ["bot_name", "emoji", "user_name", "model", "ollama_host",
               "ollama_path", "theme", "chrome_path", "system_prompt",
               "auto_start_ollama", "contacts", "api_keys", "port"]
    for key in allowed:
        if key in data:
            cfg[key] = data[key]
    save_config(cfg)
    return jsonify({"ok": True})

@app.route("/api/ollama/start", methods=["POST"])
def api_start_ollama():
    result = start_ollama()
    return jsonify({"ok": result, "running": ollama_running()})

@app.route("/api/history")
def api_history():
    sid = request.args.get("session_id", "default")
    return jsonify({"messages": chat_sessions.get(sid, [])})

# ── Launch ────────────────────────────────────────────────────────────────────

def open_browser_delayed(port):
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{port}")

def run_server(port=None, open_browser=True):
    cfg = load_config()
    port = port or cfg.get("port", 7821)

    if cfg.get("auto_start_ollama") and not ollama_running():
        print("🐦‍⬛ Starting Ollama...")
        start_ollama()

    print(f"\n🐦‍⬛ Byte is running at: http://localhost:{port}")
    print("   Press Ctrl+C to stop\n")

    if open_browser:
        t = threading.Thread(target=open_browser_delayed, args=(port,))
        t.daemon = True
        t.start()

    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

if __name__ == "__main__":
    run_server()
