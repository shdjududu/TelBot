from keep_alive import keep_alive
import base64
import json
import os
import re
import sys
import time
import hashlib
from urllib.parse import urlparse, parse_qs, quote

try:
    import requests
except ImportError:
    print("ERROR: install requests")
    sys.exit(1)

try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None

try:
    import telebot
except ImportError:
    print("ERROR: Pydroid me pip install pyTelegramBotAPI run karo.")
    sys.exit(1)

# =========== BOT CONFIGURATION ===========
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Yahan apna Bot Token daalo!
bot = telebot.TeleBot(BOT_TOKEN)
# =========================================

DEFAULT_TARGET = "https://zoo0.pages.dev"
DEFAULT_USER_AGENT = "Dart/3.8 (dart:io)"
KEY = "k6kW8r#Tz3f;"
HEADER_NAMES = ("x-request-id", "x-payload", "authorization", "x-data")

# --- tumhare purane helper functions waise hi rahenge ---
def get_initial_response_headers(target_url, user_agent, verify, debug=False):
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    resp = session.get(target_url, timeout=25, verify=verify, allow_redirects=True)
    return resp.headers, resp

def build_combined(headers, debug=False):
    parts = []
    missing = []
    for hn in HEADER_NAMES:
        val = None
        for k, v in headers.items():
            if k.lower() == hn.lower():
                val = v.strip()
                break
        if val is None:
            missing.append(hn)
            parts.append("")  
        else:
            parts.append(val)
    return "".join(parts), missing

def decode_b64_xor(combined_b64: str, xor_key: bytes, debug: bool=False) -> str:
    raw = base64.b64decode(combined_b64)
    out = bytearray(len(raw))
    for i, b in enumerate(raw):
        out[i] = b ^ xor_key[i % len(xor_key)]
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        txt = out.decode("latin1", errors="ignore")
        start = txt.find("{")
        end = txt.rfind("}")
        if start != -1 and end != -1 and end > start:
            return txt[start:end+1]
        raise ValueError("Decoded bytes invalid")

def extract_baseurl(decoded_text: str, debug: bool=False) -> str:
    try:
        obj = json.loads(decoded_text)
    except Exception:
        start = decoded_text.find("{")
        end = decoded_text.rfind("}")
        obj = json.loads(decoded_text[start:end+1])
    for k in ("baseUrl", "baseurl", "base_url"):
        if k in obj:
            return obj[k]
    raise ValueError("'baseUrl' not found")

def decrypt(chipertext: str, alias: str, debug: bool=False) -> str:
    if AES is None: return None
    try:
        key_source = "sDye71jNq5" + alias
        iv_source = "7M9u8DG4X" + alias
        key_hash = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
        iv_hash = hashlib.sha256(iv_source.encode("utf-8")).hexdigest()
        key_bytes = key_hash[:32].encode("utf-8")  
        iv_bytes = iv_hash[:16].encode("utf-8")    
        ciphertext = base64.b64decode(base64.b64decode(chipertext)) 
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv_bytes)
        return cipher.decrypt(ciphertext).decode("utf-8")
    except Exception:
        return None

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

# --- Handlers ---
def handle_telegram_url(key_url, session, verify, debug=False):
    parsed = urlparse(key_url)
    query_params = parse_qs(parsed.query)
    start_param = query_params.get('start', [None])[0]
    if start_param is None:
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0].endswith("bot"):
            start_param = path_parts[-1]
    
    if start_param is None: return None, key_url, "No 'start' parameter"
    if start_param.startswith("verify_"): return start_param[7:], None, None
    elif start_param == "direct": return None, key_url, "Manual bot interaction needed"
    elif re.match(r'^[A-Fa-f0-9]{10,14}$', start_param): return start_param, None, None
    return None, key_url, "Unknown format"

def handle_nano_links(key_url, session, verify, debug=False):
    parsed = urlparse(key_url)
    extracted_id = parsed.path.strip("/").split("/")[-1]
    first_url = f"https://nano.tackledsoul.com/includes/open.php?id={extracted_id}"
    cookies = {"tp": extracted_id, "open": extracted_id}
    
    try:
        r1 = session.get(first_url, cookies=cookies, timeout=30, verify=verify, allow_redirects=False)
        if r1.status_code in (301, 302, 303, 307, 308):
            redirect_url = r1.headers.get('Location')
            new_id = urlparse(redirect_url).path.strip("/").split("/")[-1]
            second_url = f"https://vi-music.app/includes/open.php?id={new_id}"
            new_cookies = {"tp": new_id, "open": new_id}
            
            r2 = session.get(second_url, cookies=new_cookies, timeout=30, verify=verify, allow_redirects=False)
            if r2.status_code in (301, 302, 303, 307, 308):
                final_redirect = r2.headers.get('Location')
                key = parse_qs(urlparse(final_redirect).query).get("key", [None])[0]
                if key: return key, None, None
    except Exception as e:
        return None, key_url, str(e)
    return None, key_url, "Nano handler failed"

def handle_aro_links(key_url, session, verify, debug=False):
    identifier = urlparse(key_url).path.strip("/").split("/")[-1]
    try:
        response = session.get(key_url, timeout=30, verify=verify)
        if response.status_code == 200:
            redirect_url_match = re.search(r'window\.location\.href = "([^"]+)"', response.text) or re.search(r'<a href="([^"]+)"', response.text)
            if redirect_url_match:
                second_response = session.get(key_url, headers={"cookie": f"gt_uc_={identifier}", "referer": redirect_url_match.group(1)}, timeout=30, verify=verify)
                final_url_match = re.search(r'nofollow noopener noreferrer" href="(https?://[^"]+key=[^"&]+[^"]*)"', second_response.text)
                final_url_match2 = re.search(r'nofollow noopener noreferrer" href="(https?://[^"]+code=[^"&]+[^"]*)"', second_response.text)
                if final_url_match:
                    key = re.search(r'key=([^&"]+)', final_url_match.group(1))
                    if key: return key.group(1), None, None
                elif final_url_match2:
                    key = re.search(r'code=([^&"]+)', final_url_match2.group(1))
                    if key: return key.group(1), None, None
    except Exception as e:
        return None, key_url, str(e)
    return None, key_url, "Aro handler failed"

def handle_lksfy(key_url, session, verify, debug=False):
    alias = urlparse(key_url).path.strip("/").split("/")[-1]
    try:
        response = session.get(key_url, headers={"referer": key_url}, timeout=30, verify=verify, allow_redirects=False)
        if response.status_code in (301, 302, 303, 307, 308):
            second_response = session.get(key_url, headers={"referer": response.headers.get('Location')}, timeout=30, verify=verify)
            base64_match = re.search(r'var base64 = \'([^\']+)\'', second_response.text)
            if base64_match:
                decrypted_html = decrypt(base64_match.group(1), alias, debug)
                if decrypted_html:
                    form_data = extract_form_data(decrypted_html)
                    post_url = f"https://lksfy.com{form_data['action']}"
                    post_headers = {
                        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "referer": "https://lksfy.com/",
                        "cookie": f"csrfToken={form_data['csrf_token']}",
                        "x-requested-with": "XMLHttpRequest"
                    }
                    post_body = f"_method=POST&_csrfToken={quote(form_data['csrf_token'])}&ad_form_data={quote(form_data['ad_form_data'])}&_Token%5Bfields%5D={form_data['token_fields']}&_Token%5Bunlocked%5D={quote(form_data['token_unlocked'])}"
                    time.sleep(5)
                    post_response = session.post(post_url, headers=post_headers, data=post_body, timeout=30, verify=verify)
                    if post_response.status_code == 200:
                        json_resp = post_response.json()
                        if json_resp.get("status") == "success":
                            decrypted_url = decrypt(json_resp.get("url"), alias, debug)
                            if decrypted_url:
                                for regex in [r'key=([^\&\s]+)', r'verify_([A-Fa-f0-9]+)', r'start=verify_([A-Fa-f0-9]+)']:
                                    m = re.search(regex, decrypted_url)
                                    if m: return m.group(1).strip(), None, None
    except Exception as e:
        return None, key_url, str(e)
    return None, key_url, "Lksfy handler failed"

def fetch_key_flow(baseurl: str, verify: bool, user_agent: str = None):
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent or "Mozilla/5.0"})
    url1 = baseurl.rstrip("/") + "/api/v1/auth/generate?server=1"
    try:
        r1 = session.get(url1, timeout=30, verify=verify)
        r1.raise_for_status()
        key_url = r1.json()["data"]["keyUrl"]
        
        if "t.me" in key_url: return handle_telegram_url(key_url, session, verify)
        elif "nanolinks" in key_url: return handle_nano_links(key_url, session, verify)
        elif "arolinks" in key_url: return handle_aro_links(key_url, session, verify)
        elif "lksfy" in key_url: return handle_lksfy(key_url, session, verify)
        else: return handle_nano_links(key_url, session, verify)
    except Exception as e:
        return None, None, str(e)

# =========== TELEGRAM BOT COMMANDS ===========

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *Sigma Key Extractor Bot*\n\n"
        "Bhai, apne direct target link (jaise lksfy, nanolinks) mujhe message me bhej do, "
        "ya default flow chalane ke liye /default bhejo.\n\n"
        "_Mil ke phodenge is task ko!_"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['default'])
def handle_default(message):
    bot.reply_to(message, "⏳ *Default API check kar raha hoon...* Thoda time lag sakta hai bhai.", parse_mode='Markdown')
    try:
        headers, resp = get_initial_response_headers(DEFAULT_TARGET, DEFAULT_USER_AGENT, verify=True)
        combined, missing = build_combined(headers)
        if all(not ch for ch in combined):
            return bot.reply_to(message, "❌ Bouncer! Server ne required headers nahi diye.")
        
        xor_key_bytes = KEY.encode("utf-8")
        decoded = decode_b64_xor(combined, xor_key_bytes)
        baseurl = extract_baseurl(decoded)
        
        bot.send_message(message.chat.id, f"🔗 Base URL mili: `{baseurl}`\nKey bypass kar raha hoon...", parse_mode='Markdown')
        key, _, error = fetch_key_flow(baseurl, verify=True, user_agent=DEFAULT_USER_AGENT)
        
        if key:
            bot.reply_to(message, f"✅ *MISSION SUCCESSFUL*\n\n*YOUR KEY:* `{key}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ Failed bhai. Error: {error}")
    except Exception as e:
        bot.reply_to(message, f"💥 Error ho gaya bhai: {str(e)}")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def handle_url_message(message):
    url = message.text.strip()
    bot.reply_to(message, f"🔍 Link mil gaya bhai! Bypass shuru kar raha hoon...\n`{url}`", parse_mode='Markdown')
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    key, error = None, None

    try:
        if "t.me" in url or "telegram" in url.lower():
            if "verify_" in url: key, _, error = handle_telegram_url(url, session, verify=True)
            else: error = "Is Telegram link me key parameter nahi hai."
        elif "nanolinks" in url:
            key, _, error = handle_nano_links(url, session, verify=True)
        elif "arolinks" in url:
            key, _, error = handle_aro_links(url, session, verify=True)
        elif "lksfy" in url:
            key, _, error = handle_lksfy(url, session, verify=True)
        else:
            bot.send_message(message.chat.id, "⚠️ Domain unknown hai, saare methods try kar raha hoon...")
            for handler in [handle_lksfy, handle_nano_links, handle_aro_links]:
                key, _, error = handler(url, session, verify=True)
                if key: break
        
        if key:
            bot.reply_to(message, f"🎯 *GAJAB! Bypass Done!*\n\n*YOUR KEY:* `{key}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ Bypass fail ho gaya bhai.\nError: {error}")
    except Exception as e:
         bot.reply_to(message, f"💥 Bot Exception: {str(e)}")

# =============================================

if __name__ == "__main__":
    print("🚀 Bot start ho raha hai bhai... Pydroid 3 ko background me chalta rehne do!")
    # Infinity polling script ko stop hone se bachati hai connection errors pe
    if __name__ == "__main__":
    print("🚀 Bot aur Web Server dono start ho rahe hain bhai...")
    keep_alive() # Ye tumhari Flask website ko start karega
    bot.infinity_polling() # Ye bot ko start karega