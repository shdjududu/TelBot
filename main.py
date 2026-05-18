import base64
import json
import os
import re
import sys
import time
import hashlib
import threading
from urllib.parse import urlparse, parse_qs, quote
from flask import Flask

try:
    import requests
    import telebot
except ImportError:
    print("ERROR: Install requests and pyTelegramBotAPI")
    sys.exit(1)

try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None

# =========== BOT & FLASK CONFIGURATION ===========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8934174009:AAGIDDs1r6epZvpoUa-Mao24aawfywXtNUs")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Route to serve your HTML website for UptimeRobot
@app.route('/')
def home():
    try:
        with open("index.html", "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Sigma Bot is Online 24/7! (UI file not found: {e})"

# Function to run Flask server continuously
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# =========== CORE BYPASS LOGIC ===========
DEFAULT_TARGET = "https://zoo0.pages.dev"
DEFAULT_USER_AGENT = "Dart/3.8 (dart:io)"
KEY = "k6kW8r#Tz3f;"
HEADER_NAMES = ("x-request-id", "x-payload", "authorization", "x-data")

def get_initial_response_headers(target_url, user_agent, verify):
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    resp = session.get(target_url, timeout=25, verify=verify, allow_redirects=True)
    return resp.headers, resp

def build_combined(headers):
    parts = []
    for hn in HEADER_NAMES:
        val = next((v.strip() for k, v in headers.items() if k.lower() == hn.lower()), "")
        parts.append(val)
    return "".join(parts)

def decode_b64_xor(combined_b64: str, xor_key: bytes) -> str:
    raw = base64.b64decode(combined_b64)
    out = bytearray([b ^ xor_key[i % len(xor_key)] for i, b in enumerate(raw)])
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        txt = out.decode("latin1", errors="ignore")
        start, end = txt.find("{"), txt.rfind("}")
        if start != -1 and end != -1 and end > start:
            return txt[start:end+1]
        raise ValueError("Decoded bytes invalid")

def extract_baseurl(decoded_text: str) -> str:
    try:
        obj = json.loads(decoded_text)
    except Exception:
        start, end = decoded_text.find("{"), decoded_text.rfind("}")
        obj = json.loads(decoded_text[start:end+1])
    for k in ("baseUrl", "baseurl", "base_url"):
        if k in obj: return obj[k]
    raise ValueError("'baseUrl' not found")

def decrypt(chipertext: str, alias: str) -> str:
    if AES is None: return None
    try:
        key_hash = hashlib.sha256(("sDye71jNq5" + alias).encode("utf-8")).hexdigest()
        iv_hash = hashlib.sha256(("7M9u8DG4X" + alias).encode("utf-8")).hexdigest()
        cipher = AES.new(key_hash[:32].encode("utf-8"), AES.MODE_CBC, iv=iv_hash[:16].encode("utf-8"))
        return cipher.decrypt(base64.b64decode(base64.b64decode(chipertext))).decode("utf-8")
    except Exception: return None

def extract_form_data(html_content):
    def get_val(pattern):
        m = re.search(pattern, html_content)
        return m.group(1) if m else ""
    return {
        "csrf_token": get_val(r'name="_csrfToken"[^>]*value="([^"]+)"'),
        "ad_form_data": get_val(r'name="ad_form_data"[^>]*value="([^"]+)"'),
        "token_fields": get_val(r'name="_Token\[fields\]"[^>]*value="([^"]+)"'),
        "token_unlocked": get_val(r'name="_Token\[unlocked\]"[^>]*value="([^"]+)"'),
        "action": get_val(r'action="([^"]+)"')
    }

# =========== LINK HANDLERS ===========
def handle_telegram_url(key_url, session, verify):
    parsed = urlparse(key_url)
    start_param = parse_qs(parsed.query).get('start', [None])[0]
    if not start_param:
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0].endswith("bot"):
            start_param = path_parts[-1]
    if not start_param: return None, key_url, "No 'start' parameter"
    if start_param.startswith("verify_"): return start_param[7:], None, None
    elif start_param == "direct": return None, key_url, "Manual bot interaction needed"
    elif re.match(r'^[A-Fa-f0-9]{10,14}$', start_param): return start_param, None, None
    return None, key_url, "Unknown format"

def handle_nano_links(key_url, session, verify):
    ext_id = urlparse(key_url).path.strip("/").split("/")[-1]
    try:
        r1 = session.get(f"https://nano.tackledsoul.com/includes/open.php?id={ext_id}", cookies={"tp": ext_id, "open": ext_id}, timeout=30, verify=verify, allow_redirects=False)
        if r1.status_code in (301, 302, 303, 307, 308):
            new_id = urlparse(r1.headers.get('Location')).path.strip("/").split("/")[-1]
            r2 = session.get(f"https://vi-music.app/includes/open.php?id={new_id}", cookies={"tp": new_id, "open": new_id}, timeout=30, verify=verify, allow_redirects=False)
            if r2.status_code in (301, 302, 303, 307, 308):
                key = parse_qs(urlparse(r2.headers.get('Location')).query).get("key", [None])[0]
                if key: return key, None, None
    except Exception as e: return None, key_url, str(e)
    return None, key_url, "Nano handler failed"

def handle_aro_links(key_url, session, verify):
    identifier = urlparse(key_url).path.strip("/").split("/")[-1]
    try:
        res = session.get(key_url, timeout=30, verify=verify)
        match = re.search(r'window\.location\.href = "([^"]+)"', res.text) or re.search(r'<a href="([^"]+)"', res.text)
        if match:
            res2 = session.get(key_url, headers={"cookie": f"gt_uc_={identifier}", "referer": match.group(1)}, timeout=30, verify=verify)
            f_url = re.search(r'href="(https?://[^"]+(key|code)=[^"&]+[^"]*)"', res2.text)
            if f_url:
                k = re.search(r'(key|code)=([^&"]+)', f_url.group(1))
                if k: return k.group(2), None, None
    except Exception as e: return None, key_url, str(e)
    return None, key_url, "Aro handler failed"

def handle_lksfy(key_url, session, verify):
    alias = urlparse(key_url).path.strip("/").split("/")[-1]
    try:
        res1 = session.get(key_url, headers={"referer": key_url}, timeout=30, verify=verify, allow_redirects=False)
        if res1.status_code in (301, 302, 303, 307, 308):
            res2 = session.get(key_url, headers={"referer": res1.headers.get('Location')}, timeout=30, verify=verify)
            b64_match = re.search(r'var base64 = \'([^\']+)\'', res2.text)
            if b64_match:
                html = decrypt(b64_match.group(1), alias)
                if html:
                    fd = extract_form_data(html)
                    body = f"_method=POST&_csrfToken={quote(fd['csrf_token'])}&ad_form_data={quote(fd['ad_form_data'])}&_Token%5Bfields%5D={fd['token_fields']}&_Token%5Bunlocked%5D={quote(fd['token_unlocked'])}"
                    time.sleep(5)
                    post_res = session.post(f"https://lksfy.com{fd['action']}", headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8", "referer": "https://lksfy.com/", "cookie": f"csrfToken={fd['csrf_token']}", "x-requested-with": "XMLHttpRequest"}, data=body, timeout=30, verify=verify)
                    if post_res.status_code == 200 and post_res.json().get("status") == "success":
                        dec_url = decrypt(post_res.json().get("url"), alias)
                        if dec_url:
                            for reg in [r'key=([^\&\s]+)', r'verify_([A-Fa-f0-9]+)', r'start=verify_([A-Fa-f0-9]+)']:
                                m = re.search(reg, dec_url)
                                if m: return m.group(1).strip(), None, None
    except Exception as e: return None, key_url, str(e)
    return None, key_url, "Lksfy handler failed"

def fetch_key_flow(baseurl, verify):
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
    try:
        r1 = session.get(baseurl.rstrip("/") + "/api/v1/auth/generate?server=1", timeout=30, verify=verify)
        key_url = r1.json()["data"]["keyUrl"]
        if "t.me" in key_url: return handle_telegram_url(key_url, session, verify)
        elif "nanolinks" in key_url: return handle_nano_links(key_url, session, verify)
        elif "arolinks" in key_url: return handle_aro_links(key_url, session, verify)
        elif "lksfy" in key_url: return handle_lksfy(key_url, session, verify)
        else: return handle_nano_links(key_url, session, verify)
    except Exception as e: return None, None, str(e)

# =========== TELEGRAM HANDLERS ===========
@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.reply_to(message, "🤖 *Sigma Key Extractor Bot*\nSend me a direct link (lksfy, nanolinks) or use /default.", parse_mode='Markdown')

@bot.message_handler(commands=['default'])
def default_cmd(message):
    bot.reply_to(message, "⏳ *Checking Default API...*", parse_mode='Markdown')
    try:
        h, _ = get_initial_response_headers(DEFAULT_TARGET, DEFAULT_USER_AGENT, True)
        combined = build_combined(h)
        baseurl = extract_baseurl(decode_b64_xor(combined, KEY.encode("utf-8")))
        key, _, err = fetch_key_flow(baseurl, True)
        if key: bot.reply_to(message, f"✅ *KEY FOUND:* `{key}`", parse_mode='Markdown')
        else: bot.reply_to(message, f"❌ Failed: {err}")
    except Exception as e: bot.reply_to(message, f"💥 Error: {e}")

@bot.message_handler(func=lambda msg: msg.text.startswith('http'))
def handle_link(message):
    url = message.text.strip()
    bot.reply_to(message, f"🔍 Processing: `{url}`", parse_mode='Markdown')
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
    key, err = None, None
    try:
        if "t.me" in url: key, _, err = handle_telegram_url(url, session, True)
        elif "nanolinks" in url: key, _, err = handle_nano_links(url, session, True)
        elif "arolinks" in url: key, _, err = handle_aro_links(url, session, True)
        elif "lksfy" in url: key, _, err = handle_lksfy(url, session, True)
        else:
            for h in [handle_lksfy, handle_nano_links, handle_aro_links]:
                key, _, err = h(url, session, True)
                if key: break
        
        if key: bot.reply_to(message, f"🎯 *BYPASS SUCCESSFUL!*\n\n*YOUR KEY:* `{key}`", parse_mode='Markdown')
        else: bot.reply_to(message, f"❌ Bypass failed: {err}")
    except Exception as e: bot.reply_to(message, f"💥 Bot Exception: {e}")

# =========== START SCRIPT ===========
if __name__ == "__main__":
    print("🌐 Starting Web Server in background thread...")
    threading.Thread(target=run_web_server).start()
    print("🚀 Starting Telegram Bot polling...")
    bot.infinity_polling()