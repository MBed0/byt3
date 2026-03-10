# 👾 Byte — Local AI Assistant

> Powered by Ollama + qwen3:4b | Black/white Claude Code aesthetic

## Quick Start

```bash
# 1. Install dependencies + create 'byte' command
python setup.py

# 2. Launch (opens browser at http://localhost:7821)
byte

# OR: terminal mode
byte --cmd
```

## Features

| Feature | Description |
|---|---|
| 🌐 **Web GUI** | Local web app at `localhost:7821` |
| 💬 **Chat** | Stream chat with any Ollama model |
| ◻ **Models** | Select, switch, pull models from GUI |
| ⚙️ **Settings** | Emoji, name, system prompt, contacts |
| 🔌 **Integrations** | WhatsApp, Discord, Telegram |
| 📋 **Dashboard** | Status, quick commands, activity log |

## Commands (in chat)

```
Hey Byte, open Chrome
Hey Byte, text Yezdan Hello
Hey Byte, check my WhatsApp
Hey Byte, check my Instagram DMs
Hey Byte, send Discord message to general: I'm here
Hey Byte, send Telegram: meeting at 5pm
Hey Byte, open VS Code
```

## CLI Options

```bash
byte                    # Start GUI (auto-opens browser)
byte --no-browser       # Start server only
byte --port 8080        # Custom port
byte --cmd              # Terminal chat mode
byte --model llama3:8b  # Override model
```

## Integrations Setup

### WhatsApp
- Requires: `pip install selenium`
- First run: scan QR code → session saved automatically

### Discord
- Go to: discord.com/developers/applications → Bot → Token
- OR use a Webhook URL (easier)

### Telegram
- Message @BotFather → /newbot → copy token
- Find chat_id: `api.telegram.org/bot<TOKEN>/getUpdates`

## Requirements

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- `pip install flask requests selenium`
