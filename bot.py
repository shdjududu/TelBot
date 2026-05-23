import telebot
import requests
import re
import time
import os
import threading
from flask import Flask
from urllib.parse import urlparse, parse_qs, urljoin

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
BOT_TOKEN = "8934174009:AAGIDDs1r6epZvpoUa-Mao24aawfywXtNUs"  # <-- Apna Token daalo
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Muh khol ayush bhai"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 🛡️ THE CORE BYPASS ENGINE (Human Emulator)
# ==========================================
def extract_key(url, html=""):
    blacklist = ['function', 'undefined', 'null', 'true', 'false', 'return']
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    
    for param in ['key', 'code']:
        if param in qs:
            val = qs[param][0]
            if val.lower() not in blacklist and len(val) > 3:
                return val
                
    v_match = re.search(r'(?:verify_|start=verify_)([A-Za-z0-9_-]{5,})', url)
    if v_match: return v_match.group(1)
        
    if html:
        v2_match = re.search(r'verify_([A-Za-z0-9_-]{8,})', html)
        if v2_match: return v2_match.group(1)
        
    return None

def bypass_arolinks(url):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    })
    
    # 🔥 The God-Mode Cookies
    target_domains = ['.arolinks.com', '.mahnokari.com', '.darkguruji.com', 'arolinks.com', 'mahnokari.com', 'darkguruji.com']
    for d in target_domains:
        session.cookies.set('adcadg', 'insurance,online_colleges,study_abroad,finance,loan', domain=d)
        session.cookies.set('eonstudb', 'insurance,online_colleges,study_abroad,finance,loan', domain=d)
        session.cookies.set('_uocat', 'value', domain=d)

    current_url = url
    referer = url
    
    try:
        # Loop exactly waisa chalega jaisa working CLI script mein tha
        for step in range(1, 26):
            # Allow redirects FALSE is crucial to prevent crash
            resp = session.get(current_url, headers={"Referer": referer}, allow_redirects=False, timeout=15)
            
            k = extract_key(resp.url)
            if k: return k, None

            # 1. Catch 301/302 Redirects
            if resp.status_code in (301, 302, 303, 307, 308):
                next_url = urljoin(resp.url, resp.headers.get('Location', ''))
                referer = current_url
                current_url = next_url
                time.sleep(1) # Chhota delay zaroori hai
                continue

            html = resp.text
            k = extract_key(resp.url, html)
            if k: return k, None

            # 2. Dynamic Cookies Injector
            for c_name, c_val in re.findall(r'document\.cookie\s*=\s*["\']\s*([^=]+)=([^;"\']+)', html):
                if c_name.strip() not in ['adcadg', 'eonstudb', '_uocat']:
                    session.cookies.set(c_name.strip(), c_val.strip(), domain=urlparse(current_url).netloc)

            action_taken = False
            
            # 3. Catch JS Redirects
            js_match = re.search(r'(?:window|document)\.location(?:\.href|\.replace)?\s*[\(=]\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if js_match:
                next_url = js_match.group(1)
                if not next_url.startswith('http'): next_url = urljoin(resp.url, next_url)
                referer = current_url
                current_url = next_url
                action_taken = True
                time.sleep(1)
                continue

            # 4. Catch Meta Redirects
            meta_match = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\']\d+;\s*url=([^"\']+)["\']', html, re.IGNORECASE)
            if meta_match:
                next_url = urljoin(resp.url, meta_match.group(1))
                referer = current_url
                current_url = next_url
                action_taken = True
                time.sleep(1)
                continue

            # 5. Catch Buttons and Links
            btn_href = None
            for a_tag in re.findall(r'<a\s+[^>]+>', html, re.IGNORECASE):
                if re.search(r'id=["\'](?:btn\d*|getlink|cross-snp2)["\']', a_tag, re.IGNORECASE) or 'class="ce-btn' in a_tag.lower() or 'readmore' in a_tag.lower():
                    href_match = re.search(r'href=["\']([^"\']+)["\']', a_tag, re.IGNORECASE)
                    if href_match:
                        cand = href_match.group(1).strip()
                        if cand and cand != "#" and not cand.lower().startswith("javascript:"):
                            btn_href = urljoin(resp.url, cand)
                            break
            
            if btn_href:
                referer = current_url
                current_url = btn_href
                action_taken = True
                time.sleep(2) # CRUCIAL: Server ko wait time dena padega
                continue

            # 6. Catch Hidden Forms
            forms = re.findall(r'<form(.*?)>(.*?)</form>', html, re.DOTALL | re.IGNORECASE)
            for f_attr, f_inner in forms:
                if 'search' in f_attr.lower() or 'comment' in f_attr.lower(): continue
                action_match = re.search(r'action=["\']([^"\']+)["\']', f_attr, re.IGNORECASE)
                inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', f_inner, re.IGNORECASE)
                if action_match and inputs:
                    action = action_match.group(1)
                    data = {k: v for k, v in inputs}
                    next_url = urljoin(resp.url, action)
                    
                    time.sleep(2) # CRUCIAL DELAY
                    post_resp = session.post(next_url, headers={"Referer": current_url}, data=data, allow_redirects=False, timeout=15)
                    
                    if post_resp.status_code in (301, 302, 303, 307, 308):
                        current_url = urljoin(post_resp.url, post_resp.headers['Location'])
                    else:
                        current_url = post_resp.url
                        
                    referer = resp.url
                    action_taken = True
                    break
            
            if action_taken: continue

            return None, "Bot reached a dead end. No buttons or redirects found."

        return None, "Too many steps. Loop didn't finish."
        
    except Exception as e:
        return None, f"Error: {str(e)}"


# ==========================================
# 🤖 TELEGRAM BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start'])
def welcome_msg(message):
    text = (
        "👋 *Ayush is feeling*\n\n"
        "Horny"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: 'arolinks.com' in msg.text)
def handle_link(message):
    url = message.text.strip()
    
    status_msg = bot.reply_to(message, "⏳ *Processing your link...*\n\n_Please wait exactly 2 Minutes and 5 Seconds for the key._", parse_mode="Markdown")
    
    start_time = time.time()
    
    # Yahan bot real delays ke sath exact process follow karega
    key, error = bypass_arolinks(url)
    
    elapsed_time = time.time() - start_time
    target_wait_time = 125  # 2 Minutes 5 Seconds
    
    # Agar key jaldi bhi mil gayi, toh telegram par wait karayega taaki safe rahe
    if elapsed_time < target_wait_time:
        time.sleep(target_wait_time - elapsed_time)
        
    if key:
        bot.edit_message_text(f"✅ **BYPASS SUCCESSFUL!**\n\n🔑 **Your Key:** `{key}`", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text(f"❌ **BYPASS FAILED.**\n\n_Error:_ `{error}`\n\n_Link might be expired._", chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")


# Engine Start
if __name__ == "__main__":
    print("🚀 Starting Web Server in Background...")
    threading.Thread(target=run_server, daemon=True).start()
    
    print("🤖 Stealth Telegram Bot Online...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
