"""👾 Byte — WhatsApp Agent"""
import json, time
from pathlib import Path

def load_config():
    with open(Path(__file__).parent.parent / "config.json") as f:
        return json.load(f)

def send_whatsapp_message(contact: str, message: str) -> str:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        return "❌ Install selenium: pip install selenium"

    cfg = load_config()
    phone = cfg.get("contacts", {}).get(contact, contact)

    options = Options()
    options.add_argument(f"--user-data-dir={cfg.get('whatsapp_profile','./whatsapp_session')}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if cfg.get("chrome_path"):
        options.binary_location = cfg["chrome_path"]

    try:
        driver = webdriver.Chrome(options=options)
        clean = phone.replace("+","").replace(" ","").replace("-","")
        url = f"https://web.whatsapp.com/send?phone={clean}&text={message}" if clean.isdigit() else "https://web.whatsapp.com"
        driver.get(url)
        wait = WebDriverWait(driver, 60)
        try:
            box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
            time.sleep(1)
            if not clean.isdigit():
                s = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
                s.send_keys(contact); time.sleep(2)
                wait.until(EC.presence_of_element_located((By.XPATH, f'//span[@title="{contact}"]'))).click()
                time.sleep(1)
                box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
            box.send_keys(message); time.sleep(0.5); box.send_keys(Keys.ENTER)
            time.sleep(2); driver.quit()
            return f"✅ Sent to {contact}"
        except Exception as e:
            return f"⚠️ Browser opened — send manually ({e})"
    except Exception as e:
        return f"❌ {e}"
