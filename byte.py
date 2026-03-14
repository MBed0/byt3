#!/usr/bin/env python3
"""
👾 Byte v3.1 — Local AI Assistant
"""
import sys, os, argparse, time, subprocess, json, datetime, re, threading
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))
VERSION = "3.1.0"

# ── Windows UTF-8 + ANSI ──────────────────────────────────────────────────────
if sys.platform == "win32":
    import io, ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    ctypes.windll.kernel32.SetConsoleCP(65001)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    os.system("reg add HKCU\\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1")

# ── Colors ────────────────────────────────────────────────────────────────────
class C:
    RESET="\033[0m"; BOLD="\033[1m"; DIM="\033[2m"; ITALIC="\033[3m"
    WHITE="\033[97m"; GRAY="\033[90m"; BLACK="\033[30m"
    CYAN="\033[96m"; GREEN="\033[92m"; YELLOW="\033[93m"
    RED="\033[91m"; BLUE="\033[94m"; MAG="\033[95m"
    BG_CY="\033[46m"
    HIDE_CURSOR="\033[?25l"; SHOW_CURSOR="\033[?25h"

R=C.RESET
def c(col,t):  return f"{col}{t}{R}"
def bold(t):   return f"{C.BOLD}{C.WHITE}{t}{R}"
def dim(t):    return f"{C.DIM}{C.GRAY}{t}{R}"
def hi(t):     return f"{C.BOLD}{C.CYAN}{t}{R}"
def ok(t):     return f"{C.GREEN}{t}{R}"
def err(t):    return f"{C.RED}{t}{R}"
def warn(t):   return f"{C.YELLOW}{t}{R}"
def tag(t):    return f"{C.BG_CY}{C.BLACK} {t} {R}"
def italic(t): return f"{C.ITALIC}{C.GRAY}{t}{R}"

def clear():
    if sys.platform == "win32":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="", flush=True)

def W():
    try:    return os.get_terminal_size().columns
    except: return 80

def line(ch="─", col=C.GRAY): return c(col, ch * min(W()-4, 60))
def pad(n=1):  print("\n"*(n-1))

# ── Keyboard ──────────────────────────────────────────────────────────────────
if sys.platform == "win32":
    import msvcrt
    def getch():
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):
            ch2 = msvcrt.getwch()
            return {'H':'UP','P':'DOWN','M':'RIGHT','K':'LEFT'}.get(ch2, '')
        if ch == '\x03': raise KeyboardInterrupt
        return ch
else:
    import tty, termios, select
    def getch():
        fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd); ch = sys.stdin.read(1)
            if ch == '\x1b':
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    sys.stdin.read(1)
                    ch3 = sys.stdin.read(1)
                    return {'A':'UP','B':'DOWN','C':'RIGHT','D':'LEFT'}.get(ch3, '')
                return '\x1b'
            if ch == '\x03': raise KeyboardInterrupt
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ══════════════════════════════════════════════════════════════════════════════
# SMOOTH MENU ENGINE  — diff rendering, no full clear on each keypress
# ══════════════════════════════════════════════════════════════════════════════

def _render_menu_lines(items, sel, header_lines, search, cfg=None):
    """Build list of display lines without printing."""
    bot = cfg.get("emoji","👾")+" "+cfg.get("bot_name","Byte") if cfg else "👾 Byte"
    lines = []
    lines.append("")
    lines.append(f"  {bold(bot)}  {dim('v'+VERSION)}  {tag('AI')}")
    lines.append(f"  {line()}")
    if header_lines:
        for hl in header_lines:
            lines.append(f"  {hl}")
        lines.append(f"  {line('·')}")
    lines.append("")
    for i, item in enumerate(items):
        label = item[0]
        desc  = item[1] if len(item)>1 else ""
        icon  = item[2] if len(item)>2 else " "
        if i == sel:
            pre = c(C.CYAN+C.BOLD, " ❯ ")
            lbl = f"{C.BOLD}{C.CYAN}{label}{R}"
            dsc = f"  {C.DIM}{C.CYAN}{desc}{R}" if desc else ""
            ic  = c(C.CYAN, icon)
        else:
            pre = "   "
            lbl = c(C.WHITE, label)
            dsc = f"  {dim(desc)}" if desc else ""
            ic  = dim(icon)
        lines.append(f"  {pre}{ic}  {lbl}{dsc}")
    lines.append("")
    if search:
        lines.append(f"  {dim('search:')} {hi(search)}")
    lines.append(f"  {dim('↑↓ navigate  enter select  esc/q back  type to search')}")
    lines.append("")
    return lines

# Global diff-render state
_mprev   = []
_mfirst  = True
_mheight = 0

def draw_menu_smooth(items, sel, header_lines=None, search="", cfg=None):
    global _mprev, _mfirst, _mheight
    new = _render_menu_lines(items, sel, header_lines, search, cfg)

    if _mfirst:
        clear()
        print(C.HIDE_CURSOR, end="", flush=True)
        for ln in new: print(ln)
        _mprev   = new[:]
        _mheight = len(new)
        _mfirst  = False
        return

    # Move cursor to top of menu block
    print(f"\033[{_mheight}A", end="", flush=True)

    max_len      = max(len(new), len(_mprev))
    prev_padded  = _mprev + [""] * (max_len - len(_mprev))
    new_padded   = new    + [""] * (max_len - len(new))

    for p, n in zip(prev_padded, new_padded):
        if p != n:
            print(f"\033[2K\r{n}\033[B\r", end="", flush=True)
        else:
            print("\033[1B", end="", flush=True)

    _mprev   = new[:]
    _mheight = max_len

def _menu_reset():
    global _mprev, _mfirst, _mheight
    _mprev = []; _mfirst = True; _mheight = 0

def run_menu(title, items, header_lines=None, start=0, cfg=None):
    _menu_reset()
    sel = start; search = ""; filtered = items[:]
    try:
        while True:
            display = filtered if search else items
            if not display: display = items; search = ""
            if sel >= len(display): sel = 0
            draw_menu_smooth(display, sel, header_lines, search, cfg)

            k = getch()
            if   k == 'UP':    sel = (sel-1) % max(len(display),1)
            elif k == 'DOWN':  sel = (sel+1) % max(len(display),1)
            elif k in ('\r','\n',' '):
                if display:
                    print(C.SHOW_CURSOR, end="", flush=True)
                    _menu_reset(); return sel, display[sel]
            elif k in ('q','Q','\x1b'):
                print(C.SHOW_CURSOR, end="", flush=True)
                _menu_reset(); return -1, None
            elif k in ('\x08','\x7f'):
                search = search[:-1]
                filtered = [it for it in items if search.lower() in it[0].lower()] if search else items[:]
                sel = 0; _menu_reset()
            elif k and len(k)==1 and k.isprintable():
                search += k
                filtered = [it for it in items if search.lower() in it[0].lower()]
                sel = 0; _menu_reset()
    except KeyboardInterrupt:
        print(C.SHOW_CURSOR, end="", flush=True)
        _menu_reset(); return -1, None

# ══════════════════════════════════════════════════════════════════════════════
# THINKING ANIMATION  (Ollama / nanobot style)
# ══════════════════════════════════════════════════════════════════════════════

_THINK_FRAMES = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
_THINK_STAGES = ["thinking", "analyzing", "composing reply"]

class ThinkingSpinner:
    def __init__(self):
        self._stop   = threading.Event()
        self._ready  = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=0.3)

    def _run(self):
        i = 0; stage = 0; ticks = 0
        self._ready.set()
        while not self._stop.is_set():
            frame  = _THINK_FRAMES[i % len(_THINK_FRAMES)]
            label  = _THINK_STAGES[stage % len(_THINK_STAGES)]
            time_s = f"{ticks*0.08:.1f}s"
            print(f"\r  {c(C.MAG,frame)}  {italic(label)}  {c(C.DIM+C.GRAY,time_s)}   ",
                  end="", flush=True)
            time.sleep(0.08)
            i += 1; ticks += 1
            if ticks % 30 == 0: stage += 1   # rotate stage every ~2.4 s
        print(f"\r{' '*60}\r", end="", flush=True)

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.5)

# ══════════════════════════════════════════════════════════════════════════════
# WEATHER MEMORY
# ══════════════════════════════════════════════════════════════════════════════
WEATHER_CACHE = BASE / ".weather_cache.json"

def _get_weather(city=None):
    """Fetch weather via wttr.in (no API key). Returns (summary, city)."""
    try:
        import requests as req
        cache = {}
        if WEATHER_CACHE.exists():
            try: cache = json.loads(WEATHER_CACHE.read_text(encoding="utf-8"))
            except: pass

        if not city:
            city = cache.get("city", "")
        if not city:
            return None, None

        # Use cache if fresh (< 30 min) and same city
        if city == cache.get("city") and time.time() - cache.get("timestamp",0) < 1800:
            return cache.get("summary",""), city

        r = req.get(
            f"https://wttr.in/{city}?format=j1",
            timeout=6,
            headers={"User-Agent": "Byte/3.1 (+local-ai)"}
        )
        if r.status_code == 200:
            d      = r.json()
            cur    = d["current_condition"][0]
            temp   = cur["temp_C"]
            feels  = cur["FeelsLikeC"]
            desc   = cur["weatherDesc"][0]["value"]
            humid  = cur["humidity"]
            wind   = cur["windspeedKmph"]
            summary = (f"{desc}, {temp}°C (feels {feels}°C)"
                       f" · humidity {humid}%"
                       f" · wind {wind} km/h")
            cache = {"city": city, "summary": summary, "timestamp": time.time()}
            WEATHER_CACHE.write_text(
                json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
            return summary, city
    except Exception:
        pass
    return None, city

def _weather_context():
    """Return a short weather string to inject into chat context."""
    if not WEATHER_CACHE.exists(): return ""
    try:
        wc = json.loads(WEATHER_CACHE.read_text(encoding="utf-8"))
        if time.time() - wc.get("timestamp",0) > 3600: return ""
        city    = wc.get("city","")
        summary = wc.get("summary","")
        if city and summary:
            return f"\n\n[User location: {city}. Current weather: {summary}]"
    except: pass
    return ""

def weather_menu():
    clear()
    print(f"\n  {bold('🌤 Weather')}\n  {line()}\n")

    cache = {}
    if WEATHER_CACHE.exists():
        try: cache = json.loads(WEATHER_CACHE.read_text(encoding="utf-8"))
        except: pass
    current = cache.get("city","")
    if current:
        print(f"  {dim('Saved city:')} {hi(current)}")
        if cache.get("summary"):
            print(f"  {c(C.WHITE, cache['summary'])}\n")

    city = input(f"  {hi('City')} {dim('(e.g. Istanbul, London, New York)')} › ").strip()
    if not city: city = current
    if not city: _flash("No city entered.", C.YELLOW); return main_menu()

    print(f"\n  ", end="", flush=True)
    sp = ThinkingSpinner(); sp.start()
    summary, used = _get_weather(city)
    sp.stop()

    if summary:
        print(f"  {ok('✓')} {bold('📍 '+used)}")
        print(f"  {c(C.WHITE, summary)}\n")
        print(f"  {dim('City saved — will be used automatically in chat.')}\n")
    else:
        print(f"  {warn('⚠ Could not fetch weather. Check the city name.')}\n")

    _wait_key(); main_menu()

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def _flash(msg, color=C.GREEN, duration=0.7):
    clear(); print(f"\n  {c(color, msg)}\n"); time.sleep(duration)

def _wait_key(msg="  Press any key to continue..."):
    print(c(C.DIM+C.GRAY, msg), flush=True); getch()

def _spinner(label, fn):
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    result = [None]; done = [False]
    def worker(): result[0] = fn(); done[0] = True
    t = threading.Thread(target=worker, daemon=True); t.start()
    i = 0
    while not done[0]:
        print(f"\r  {c(C.CYAN, frames[i%len(frames)])}  {dim(label)}...", end="", flush=True)
        time.sleep(0.08); i += 1
    print(f"\r  {ok('✓')}  {label}   ", flush=True)
    return result[0]

def _do_pull(name):
    from byte_core import load_config
    cfg = load_config(); clear()
    print(f"\n  {bold('Pulling')} {hi(name)}\n  {line()}\n")
    try:
        proc = subprocess.Popen(
            [cfg.get("ollama_path","ollama"), "pull", name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace"
        )
        for ln in proc.stdout:
            ln = ln.rstrip()
            if ln:
                print(f"  {dim(ln)}", end="\r" if "%" in ln else "\n", flush=True)
        proc.wait(); print()
        print(f"  {ok('✓ Done!') if proc.returncode==0 else err('✗ Failed.')}\n")
    except Exception as e:
        print(f"  {err(str(e))}\n")

# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING
# ══════════════════════════════════════════════════════════════════════════════
ONBOARD_FLAG = BASE / ".onboarded"

def run_onboarding():
    from byte_core import load_config, save_config, ollama_running, start_ollama, list_local_models
    cfg = load_config(); clear()
    print(f"""
{C.BOLD}{C.CYAN}
   ██████╗ ██╗   ██╗████████╗███████╗
   ██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔════╝
   ██████╔╝ ╚████╔╝    ██║   █████╗
   ██╔══██╗  ╚██╔╝     ██║   ██╔══╝
   ██████╔╝   ██║      ██║   ███████╗
   ╚═════╝    ╚═╝      ╚═╝   ╚══════╝{R}
  {dim('Local AI Assistant  ·  v'+VERSION+'  ·  Powered by Ollama')}

  {line()}
  {bold('Welcome!')} {dim("Let's get you set up.")}
  {line()}
""")
    _wait_key("  Press any key to begin setup...")

    # Step 1: Personalize
    clear(); _ob_hdr(1, 4, "Personalize")
    name = input(f"  {hi('Your name')} {dim('(default: User)')} › ").strip() or "User"
    cfg["user_name"] = name
    bot  = input(f"  {hi('Bot name')} {dim('(default: Byte)')} › ").strip() or "Byte"
    cfg["bot_name"] = bot
    emojis = ["👾","🤖","⚡","🧠","🔥","💡","🎯","🦾"]
    print(f"\n  {dim('Pick an emoji:')}\n")
    for i, e in enumerate(emojis): print(f"   {dim(str(i+1)+'.')} {e} ", end="  ")
    print()
    ei = input(f"\n  {hi('1-8')} {dim('(default 1)')} › ").strip()
    cfg["emoji"] = emojis[int(ei)-1] if ei.isdigit() and 1<=int(ei)<=8 else emojis[0]
    save_config(cfg)

    # Step 2: Ollama
    clear(); _ob_hdr(2, 4, "Ollama Check")
    print(f"  {dim('Checking Ollama...')}\n"); time.sleep(0.4)
    if ollama_running():
        print(f"  {ok('✓ Ollama is running!')}\n")
    else:
        print(f"  {warn('Starting Ollama...')}\n")
        if not _spinner("Starting Ollama", start_ollama):
            print(f"  {err('✗ Could not start Ollama.')}")
            print(f"  {dim('Install: https://ollama.com')}\n")
    _wait_key()

    # Step 3: Model
    clear(); _ob_hdr(3, 4, "Choose Model")
    models = list_local_models()
    if models:
        print(f"  {ok(f'Found {len(models)} model(s)!')}\n")
        items = [(m,"","◆") for m in models] + [("Skip","","·")]
        idx, _ = run_menu("Choose Model", items,
                          header_lines=[f"  Active: {hi(cfg.get('model','?'))}"])
        if 0 <= idx < len(models):
            cfg["model"] = models[idx]; save_config(cfg)
    else:
        print(f"  {warn('No local models found.')}\n")
        sugg = [("qwen3:4b","fast & smart"),("llama3.2:3b","lightweight"),
                ("phi4:latest","compact smart"),("mistral:7b","balanced")]
        for nm, ds in sugg: print(f"    {hi('◆')}  {bold(nm):<24}{dim(ds)}")
        print()
        pull = input(f"  {hi('Pull a model now?')} {dim('(name or enter to skip)')} › ").strip()
        if pull: _do_pull(pull); cfg["model"] = pull; save_config(cfg)

    # Step 4: Weather
    clear(); _ob_hdr(4, 4, "Weather (Optional)")
    print(f"  {dim('Byte can remember your city and use weather info in chat.')}\n")
    city = input(f"  {hi('Your city')} {dim('(e.g. Istanbul / leave blank to skip)')} › ").strip()
    if city:
        print(f"\n  ", end="", flush=True)
        sp = ThinkingSpinner(); sp.start()
        summary, _ = _get_weather(city)
        sp.stop()
        if summary:
            print(f"  {ok('✓')} {bold(city)}: {c(C.WHITE, summary)}\n")
        else:
            print(f"  {warn('Could not fetch weather — you can set it later.')}\n")
    _wait_key()

    # Done
    clear()
    print(f"\n  {ok('✓')} {bold('Setup complete!')}\n  {line()}\n")
    print(f"  {dim('Hello')} {bold(cfg['user_name'])} {dim('→')} {bold(cfg['emoji']+' '+cfg['bot_name'])}")
    print(f"  {dim('Model:')} {hi(cfg.get('model','?'))}\n")
    print(f"  {dim('Type')} {hi('/help')} {dim('inside chat for all commands')}\n")
    ONBOARD_FLAG.write_text("done")
    _wait_key("  Press any key to start...")
    main_menu()

def _ob_hdr(step, total, title):
    print(f"\n  {bold('👾 Setup')}  {dim(f'Step {step}/{total}')}  {hi(title)}")
    print(f"  {ok('▓'*step)}{dim('░'*(total-step))}")
    print(f"  {line()}\n")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════
def main_menu():
    from byte_core import load_config, ollama_running, list_local_models
    cfg     = load_config()
    running = ollama_running()
    models  = list_local_models() if running else []
    model   = cfg.get("model","?")
    user    = cfg.get("user_name","User")
    bot     = cfg.get("emoji","👾")+" "+cfg.get("bot_name","Byte")
    st      = ok("● online") if running else err("○ offline")

    header = [
        f"  {dim('User:')} {bold(user)}   {dim('Bot:')} {bold(bot)}   {dim('Ollama:')} {st}",
        f"  {dim('Model:')} {hi(model)}   {dim('Models:')} {c(C.WHITE, str(len(models)))}",
    ]
    if WEATHER_CACHE.exists():
        try:
            wc = json.loads(WEATHER_CACHE.read_text(encoding="utf-8"))
            if time.time() - wc.get("timestamp",0) < 3600:
                header.append(
                    f"  {dim('🌤')} {c(C.WHITE, wc.get('city',''))}: {dim(wc.get('summary','')[:45])}"
                )
        except: pass

    items = [
        ("Start Chat",       f"talk to {bot}",                  "💬"),
        ("Quick Ask",        "one-shot, no history",             "⚡"),
        ("Select Model",     f"{len(models)} available",         "◆"),
        ("Pull Model",       "download from ollama.com",         "↓"),
        ("Delete Model",     "remove local model",               "✕"),
        ("Weather",          "set city & view forecast",         "🌤"),
        ("Web Interface",    "browser UI · localhost:7821",      "🌐"),
        ("Integrations",     "WhatsApp · Discord · Telegram",    "🔌"),
        ("Settings",         "configure Byte",                   "⚙"),
        ("System Info",      "hardware · ollama · python",       "ℹ"),
        ("Help",             "commands & tips",                  "?"),
        ("Reset Onboarding", "run setup wizard again",           "↺"),
        ("Quit",             "",                                  " "),
    ]
    idx, _ = run_menu("Main", items, header_lines=header, cfg=cfg)
    dispatch = {
        0: run_chat, 1: quick_ask, 2: model_menu, 3: pull_menu,
        4: delete_model_menu, 5: weather_menu, 6: launch_web,
        7: integrations_menu, 8: settings_menu, 9: system_info,
        10: show_help, 11: _reset_onboard, 12: _quit
    }
    if idx == -1: _quit()
    dispatch.get(idx, main_menu)()

def _quit():
    clear()
    print(f"\n  {dim('👾 bye!')}\n")
    print(C.SHOW_CURSOR, end="", flush=True)
    sys.exit(0)

def _reset_onboard():
    ONBOARD_FLAG.unlink(missing_ok=True); run_onboarding()

# ══════════════════════════════════════════════════════════════════════════════
# MODEL MENU
# ══════════════════════════════════════════════════════════════════════════════
def model_menu():
    from byte_core import load_config, save_config, list_local_models, ollama_running, start_ollama
    if not ollama_running(): _spinner("Starting Ollama", start_ollama)
    models = list_local_models(); cfg = load_config(); cur = cfg.get("model","")
    if not models: _flash("No local models found.", C.YELLOW); return main_menu()
    items = [(m, ok("active") if m==cur else "", "◆") for m in models] + [("← Back","","  ")]
    idx, _ = run_menu("Select Model", items,
                      header_lines=[f"  Current: {hi(cur)}"], cfg=cfg)
    if idx == -1 or idx == len(models): return main_menu()
    cfg["model"] = models[idx]; save_config(cfg)
    _flash(f"✓ Model → {models[idx]}"); main_menu()

# ══════════════════════════════════════════════════════════════════════════════
# PULL / DELETE
# ══════════════════════════════════════════════════════════════════════════════
POPULAR = [
    ("qwen3:4b",       "Qwen3 4B  · fast & smart",          "⚡"),
    ("qwen3:8b",       "Qwen3 8B  · more capable",          "⚡"),
    ("llama3.2:3b",    "Llama 3.2 3B  · lightweight",       "🦙"),
    ("llama3.2:8b",    "Llama 3.2 8B  · balanced",          "🦙"),
    ("phi4:latest",    "Microsoft Phi-4  · compact+smart",  "🔬"),
    ("mistral:7b",     "Mistral 7B  · great for code",      "🌊"),
    ("gemma3:4b",      "Google Gemma3 4B  · multilingual",  "💎"),
    ("deepseek-r1:7b", "DeepSeek R1 7B  · reasoning",       "🧠"),
    ("codellama:7b",   "Code Llama 7B  · code only",        "💻"),
    ("↩ Enter manually","","  "),
    ("← Back","","  "),
]

def pull_menu():
    idx, item = run_menu("Pull Model", POPULAR,
                         header_lines=[dim("  Choose a model to download")])
    if idx == -1 or item[0] == "← Back": return main_menu()
    if item[0] == "↩ Enter manually":
        clear(); print(f"\n  {bold('Pull Model')}\n  {line()}\n")
        name = input(f"  {hi('Model name')} › ").strip()
    else:
        name = item[0]
    if not name: return main_menu()
    _do_pull(name); _wait_key(); main_menu()

def delete_model_menu():
    from byte_core import load_config, list_local_models
    cfg = load_config(); models = list_local_models()
    if not models: _flash("No models to delete.", C.YELLOW); return main_menu()
    items = [(m,"","✕") for m in models] + [("← Back","","  ")]
    idx, _ = run_menu("Delete Model", items,
                      header_lines=[warn("  This removes the model from disk")])
    if idx == -1 or idx == len(models): return main_menu()
    name = models[idx]; clear()
    confirm = input(f"\n  {warn('Delete')} {bold(name)}? {dim('Type YES')} › ").strip()
    if confirm == "YES":
        _spinner(f"Deleting {name}", lambda: subprocess.run(
            [cfg.get("ollama_path","ollama"), "rm", name], capture_output=True))
        _flash(f"✓ Deleted {name}.")
    else:
        _flash("Cancelled.", C.GRAY)
    main_menu()

# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATIONS
# ══════════════════════════════════════════════════════════════════════════════
def integrations_menu():
    from byte_core import load_config, save_config
    cfg = load_config(); keys = cfg.get("api_keys",{})
    def st(v): return ok("✓ set") if v else warn("✗ empty")
    fields = [
        ("discord_token",    "Discord Token",    "keys", "💬"),
        ("discord_webhook",  "Discord Webhook",  "keys", "💬"),
        ("telegram_token",   "Telegram Token",   "keys", "✈"),
        ("telegram_chat_id", "Telegram Chat ID", "keys", "✈"),
    ]
    items = [(f[1], st(keys.get(f[0],"")), f[3]) for f in fields]
    items.append(("← Back","","  "))
    idx, _ = run_menu("Integrations", items,
                      header_lines=[dim("  Configure messaging integrations")])
    if idx == -1 or idx == len(fields): return main_menu()
    fkey = fields[idx][0]; label = fields[idx][1]
    clear(); print(f"\n  {bold(label)}\n  {line()}\n")
    val = input(f"  {hi('New value')} {dim('(enter to keep current)')} › ").strip()
    if val:
        keys[fkey] = val; cfg["api_keys"] = keys; save_config(cfg)
        _flash(f"✓ {label} saved.")
    integrations_menu()

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
def settings_menu():
    from byte_core import load_config, save_config
    cfg = load_config()
    editable = [
        ("bot_name","Bot name","👾"),("user_name","Your name","👤"),
        ("emoji","Bot emoji","✨"),("model","Active model","◆"),
        ("ollama_host","Ollama host","🔗"),("ollama_path","Ollama binary","📁"),
        ("port","Web port","🌐"),("theme","Theme","🎨"),
        ("chrome_path","Chrome path","🌍"),
        ("auto_start_ollama","Auto-start Ollama","⚡"),
        ("system_prompt","System prompt","🧠"),
    ]
    items = [(name, dim(str(cfg.get(key,""))[:40]), ic) for key,name,ic in editable]
    items.append(("← Back","","  "))
    idx, _ = run_menu("Settings", items)
    if idx == -1 or idx == len(editable): return main_menu()
    key, label, _ = editable[idx]; cur = cfg.get(key,"")
    clear()
    print(f"\n  {bold('Edit:')} {hi(label)}")
    print(f"  {dim('Current:')} {c(C.WHITE, str(cur)[:80])}\n  {line()}\n")
    if isinstance(cur, bool):
        r  = input(f"  {hi('true/false')} › ").strip().lower()
        nv = r == "true"
    elif isinstance(cur, int):
        r  = input(f"  {hi('Number')} › ").strip()
        nv = int(r) if r.isdigit() else cur
    else:
        nv = input(f"  {hi('New value')} {dim('(enter to keep)')} › ").strip() or cur
    cfg[key] = nv; save_config(cfg)
    _flash(f"✓ {label} updated.")
    settings_menu()

# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM INFO
# ══════════════════════════════════════════════════════════════════════════════
def system_info():
    from byte_core import load_config, ollama_running, list_local_models
    import platform, shutil
    cfg = load_config(); clear()
    print(f"\n  {bold('System Info')}\n  {line()}\n")
    def row(l,v): print(f"  {c(C.CYAN,l):<32}{c(C.WHITE,str(v))}")
    row("OS",          platform.system()+" "+platform.release())
    row("Python",      sys.version.split()[0])
    row("Ollama",      ok("running") if ollama_running() else err("stopped"))
    row("Ollama host", cfg.get("ollama_host","?"))
    models = list_local_models()
    row("Local models", len(models))
    row("Active model", cfg.get("model","?"))
    row("Byte dir",    str(BASE))
    try:
        usage = shutil.disk_usage(BASE)
        row("Free disk", f"{usage.free/(1024**3):.1f} GB")
    except: pass
    try:
        r = subprocess.run(["ollama","--version"], capture_output=True, text=True, timeout=3)
        row("Ollama version", (r.stdout+r.stderr).strip())
    except: pass
    if models:
        print(f"\n  {bold('Local Models')}\n  {line('·')}")
        cur = cfg.get("model","")
        for m in models:
            print(f"    {c(C.CYAN,'◆')}  {m}{ok('  ← active') if m==cur else ''}")
    print(); _wait_key(); main_menu()

# ══════════════════════════════════════════════════════════════════════════════
# QUICK ASK
# ══════════════════════════════════════════════════════════════════════════════
def quick_ask():
    from byte_core import load_config, ollama_running, start_ollama, chat_stream
    cfg = load_config(); clear()
    print(f"\n  {bold('⚡ Quick Ask')}  {dim('one-shot · no history')}\n  {line()}\n")
    q = input(f"  {hi('Question')} › ").strip()
    if not q: return main_menu()
    if not ollama_running(): _spinner("Starting Ollama", start_ollama)

    print()
    sp = ThinkingSpinner(); sp.start()
    first = True
    try:
        for tok in chat_stream([{"role":"user","content":q}],
                                weather_ctx=_weather_context()):
            if first:
                sp.stop()
                print(f"  {c(C.GREEN,'👾')} ", end="", flush=True)
                first = False
            print(tok, end="", flush=True)
    except KeyboardInterrupt:
        sp.stop(); print(warn(" [stopped]"), end="")
    finally:
        sp.stop()

    print("\n"); _wait_key(); main_menu()

# ══════════════════════════════════════════════════════════════════════════════
# CHAT
# ══════════════════════════════════════════════════════════════════════════════
def run_chat(initial_model=None):
    from byte_core import (load_config, save_config, ollama_running,
                           start_ollama, chat_stream, run_actions, list_local_models)
    cfg = load_config()
    if initial_model: cfg["model"] = initial_model; save_config(cfg)
    if not ollama_running(): _spinner("Starting Ollama", start_ollama)
    history = []; _chat_hdr(cfg)

    while True:
        cfg = load_config()
        try:
            print(f"  {c(C.BLUE,'You')} {dim('›')} ", end="", flush=True)
            user_input = input().strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {dim('👾 bye!')}\n")
            print(C.SHOW_CURSOR, end="", flush=True)
            sys.exit(0)
        if not user_input: continue

        if user_input.startswith("/"):
            pts = user_input.split(None,1); cmd = pts[0].lower()
            arg = pts[1] if len(pts)>1 else ""

            if cmd in ("/bye","/exit","/quit","exit","quit"):
                print(f"\n  {dim('👾 bye!')}\n")
                print(C.SHOW_CURSOR, end="", flush=True)
                sys.exit(0)
            elif cmd == "/menu":   return main_menu()
            elif cmd == "/web":    return launch_web()
            elif cmd in ("/clear","/new"):
                history.clear(); _chat_hdr(cfg)
                if cmd == "/new": print(f"  {ok('✓')} New conversation.\n")
            elif cmd == "/help":   _chat_help()
            elif cmd == "/history":
                turns = len([m for m in history if m["role"]=="user"])
                print(f"\n  {dim(f'{turns} turns · {len(history)} messages')}\n")
            elif cmd == "/tokens":
                w = sum(len(m["content"].split()) for m in history)
                print(f"\n  {dim(f'~{w} words in context')}\n")
            elif cmd == "/models":
                ml = list_local_models(); cur = cfg.get("model","")
                print(f"\n  {bold('Local models:')}")
                for m in ml:
                    print(f"    {c(C.CYAN,'◆')}  {m}{ok('  ← active') if m==cur else ''}")
                print()
            elif cmd == "/model":
                if arg:
                    cfg["model"] = arg; save_config(cfg)
                    print(f"\n  {ok('✓')} Model → {hi(arg)}\n"); _chat_hdr(cfg)
                else:
                    ml = list_local_models()
                    if ml:
                        i, _ = run_menu("Switch Model", [(m,"","◆") for m in ml])
                        if i >= 0: cfg["model"] = ml[i]; save_config(cfg)
                    _chat_hdr(cfg)
            elif cmd == "/system":
                if arg:
                    cfg["system_prompt"] = arg; save_config(cfg)
                    print(f"\n  {ok('✓')} System prompt updated.\n")
                else:
                    print(f"\n  {dim(cfg.get('system_prompt','')[:120])}\n")
            elif cmd == "/save":     _save_chat(history)
            elif cmd == "/export":   _export_md(history)
            elif cmd == "/load":     history = _load_chat(history); _chat_hdr(cfg)
            elif cmd == "/copy":     _copy_last(history)
            elif cmd == "/summarize":
                if history:
                    print(f"\n  {c(C.GREEN,cfg.get('emoji','👾'))} ", end="", flush=True)
                    sumq = [{"role":"user","content":"Summarize this conversation in 3 bullets."}]
                    for tok in chat_stream(history+sumq): print(tok, end="", flush=True)
                    print("\n")
            elif cmd == "/retry":
                lu = next((m["content"] for m in reversed(history)
                           if m["role"]=="user"), None)
                if lu:
                    if history and history[-1]["role"]=="assistant": history.pop()
                    _do_stream(cfg, history, chat_stream, run_actions, lu)
            elif cmd == "/weather":
                summary, city = _get_weather()
                if summary:
                    print(f"\n  {bold('🌤 '+city)}: {c(C.WHITE, summary)}\n")
                else:
                    print(f"\n  {warn('No weather data. Go to Menu → Weather to set your city.')}\n")
            else:
                print(f"\n  {warn('Unknown command.')} {dim('Type /help')}\n")
            continue

        _do_stream(cfg, history, chat_stream, run_actions, user_input)

def _do_stream(cfg, history, chat_stream, run_actions, user_input):
    history.append({"role":"user","content":user_input})
    emoji = cfg.get("emoji","👾")

    print()
    sp = ThinkingSpinner(); sp.start()
    first = True; tokens = []

    try:
        for tok in chat_stream(history, weather_ctx=_weather_context()):
            if first:
                sp.stop()
                print(f"  {c(C.GREEN,emoji)} ", end="", flush=True)
                first = False
            print(tok, end="", flush=True)
            tokens.append(tok)
    except KeyboardInterrupt:
        sp.stop()
        print(warn(" [stopped]"), end="")
    finally:
        sp.stop()

    full = "".join(tokens)
    history.append({"role":"assistant","content":full})
    acts = run_actions(full)
    if acts:
        print(f"\n  {dim('↳ '+'  ·  '.join(a['result'] for a in acts))}", end="")
    print("\n")

def _chat_hdr(cfg):
    clear()
    print(f"\n  {bold(cfg.get('emoji','👾')+' '+cfg.get('bot_name','Byte'))}  {dim('·')}  {hi(cfg.get('model','?'))}")
    print(f"  {line()}")
    print(f"  {dim('/help  /model  /models  /clear  /save  /export  /copy  /weather  /web  /menu  /bye')}")
    if WEATHER_CACHE.exists():
        try:
            wc = json.loads(WEATHER_CACHE.read_text(encoding="utf-8"))
            if time.time() - wc.get("timestamp",0) < 3600:
                print(f"  {dim('🌤 '+wc.get('city',''))}: {c(C.DIM+C.WHITE, wc.get('summary','')[:50])}")
        except: pass
    print(f"  {line()}\n")

def _chat_help():
    print(f"""
  {bold('Commands')}
  {hi('/help')}              this list
  {hi('/model [name]')}      switch model
  {hi('/models')}            list all models
  {hi('/clear')}  {hi('/new')}       clear history
  {hi('/history')}           turn count
  {hi('/tokens')}            context word count
  {hi('/system [p]')}        view/set system prompt
  {hi('/save')}              save as .txt
  {hi('/export')}            save as .md
  {hi('/load')}              load saved chat
  {hi('/copy')}              copy last reply
  {hi('/summarize')}         summarize chat
  {hi('/retry')}             re-send last message
  {hi('/weather')}           show current weather
  {hi('/web')}               open web GUI
  {hi('/menu')}              main menu
  {hi('/bye')}               exit
""")

def _save_chat(history):
    fn   = f"byte_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = Path.home()/fn
    with open(path,"w",encoding="utf-8") as f:
        f.write(f"Byte Chat — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*60}\n\n")
        for m in history:
            f.write(f"[{m['role'].upper()}]\n{m['content']}\n\n")
    print(f"\n  {ok('✓')} Saved → {bold(str(path))}\n")

def _export_md(history):
    fn   = f"byte_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path = Path.home()/fn
    with open(path,"w",encoding="utf-8") as f:
        f.write(f"# Byte Chat\n_{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")
        for m in history:
            role = "**You**" if m["role"]=="user" else "**👾 Byte**"
            f.write(f"{role}\n\n{m['content']}\n\n---\n\n")
    print(f"\n  {ok('✓')} Exported → {bold(str(path))}\n")

def _load_chat(history):
    import glob
    saves = sorted(glob.glob(str(Path.home()/"byte_chat_*.txt")), reverse=True)[:10]
    if not saves:
        print(f"\n  {warn('No saved chats.')}\n"); return history
    items = [(Path(s).name,"","📄") for s in saves] + [("← Cancel","","  ")]
    idx, _ = run_menu("Load Chat", items)
    if idx == -1 or idx == len(saves): return history
    nh = []; role = None; buf = []
    with open(saves[idx], encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip()
            if ln in ("[USER]","[ASSISTANT]"):
                if role and buf:
                    nh.append({"role":role.lower(),"content":"\n".join(buf).strip()})
                role = ln[1:-1]; buf = []
            elif role:
                buf.append(ln)
    if role and buf:
        nh.append({"role":role.lower(),"content":"\n".join(buf).strip()})
    print(f"\n  {ok('✓')} Loaded {len(nh)} messages.\n")
    return nh

def _copy_last(history):
    for m in reversed(history):
        if m["role"] == "assistant":
            try:
                if sys.platform == "win32":
                    subprocess.run("clip", input=m["content"].encode("utf-16"), check=True)
                elif sys.platform == "darwin":
                    subprocess.run("pbcopy", input=m["content"].encode(), check=True)
                else:
                    subprocess.run(["xclip","-selection","clipboard"],
                                   input=m["content"].encode(), check=True)
                print(f"\n  {ok('✓')} Copied.\n")
            except:
                print(f"\n  {warn('Clipboard unavailable.')}\n")
            return
    print(f"\n  {dim('Nothing to copy.')}\n")

# ══════════════════════════════════════════════════════════════════════════════
# HELP  &  WEB
# ══════════════════════════════════════════════════════════════════════════════
def show_help():
    clear()
    print(f"""
  {bold('👾 Byte — Help')}
  {line()}

  {bold('CLI')}
    {hi('byte')}                    menu
    {hi('byte --cmd')}              direct chat
    {hi('byte --web')}              web GUI
    {hi('byte --quick "Q"')}        one-shot answer
    {hi('byte --model NAME')}       set model
    {hi('byte --port 8080')}        custom port
    {hi('byte --setup')}            re-run onboarding

  {bold('Say to Byte')}
    {dim('open chrome')}   {dim('open https://site.com')}
    {dim('run: dir')}      {dim('what time is it')}
    {dim('send WhatsApp to X: hello')}
    {dim('send Discord to general: hey')}
    {dim('send Telegram: meeting at 5pm')}
""")
    _wait_key(); main_menu()

def launch_web(port=None, open_browser=True):
    clear()
    from app import run_server
    run_server(port=port, open_browser=open_browser)

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(prog="byte", add_help=False)
    parser.add_argument("--cmd",        action="store_true")
    parser.add_argument("--web",        action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port",  type=int, default=None)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--quick", type=str, default=None, metavar="Q")
    parser.add_argument("--version",   action="store_true")
    parser.add_argument("--setup",     action="store_true")
    parser.add_argument("--help","-h", action="store_true")
    args = parser.parse_args()

    if args.version: print(f"👾 Byte v{VERSION}"); return
    if args.help:    show_help(); return
    if args.model:
        from byte_core import load_config, save_config
        cfg = load_config(); cfg["model"] = args.model; save_config(cfg)

    if args.quick:
        from byte_core import load_config, ollama_running, start_ollama, chat_stream
        if not ollama_running(): start_ollama()
        print("\n👾 ", end="", flush=True)
        for tok in chat_stream([{"role":"user","content":args.quick}],
                                weather_ctx=_weather_context()):
            print(tok, end="", flush=True)
        print("\n"); return

    if args.setup or not ONBOARD_FLAG.exists():
        return run_onboarding()

    if args.web:   launch_web(port=args.port, open_browser=not args.no_browser)
    elif args.cmd: run_chat()
    else:          main_menu()

if __name__ == "__main__":
    main()
