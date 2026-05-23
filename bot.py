import telebot
import requests
import re
import time
import os
import threading
from flask import Flask
from urllib.parse import urlparse, parse_qs, urljoin

app = Flask(__name__)

@app.route('/')
def h(): 
    return "Bot RUNNING"

def run(): 
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

bot = telebot.TeleBot("8934174009:AAGIDDs1r6epZvpoUa-Mao24aawfywXtNUs")

def ext_k(u, h=""):
    b = ['function', 'undefined', 'null', 'true', 'false', 'return']
    q = parse_qs(urlparse(u).query)
    
    for p in ['key', 'code']:
        if p in q:
            v = q[p][0]
            if v.lower() not in b and len(v) > 3: 
                return v
                
    m1 = re.search(r'(?:verify_|start=verify_)([A-Za-z0-9_-]{5,})', u)
    if m1: 
        return m1.group(1)
        
    if h:
        m2 = re.search(r'verify_([A-Za-z0-9_-]{8,})', h)
        if m2: 
            return m2.group(1)
            
    return None

def byp(u, bot, cid, mid):
    def upd(txt):
        try: 
            bot.edit_message_text(txt, cid, mid, parse_mode="Markdown")
        except: 
            pass

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    })
    
    doms = ['.arolinks.com', '.mahnokari.com', '.darkguruji.com', 'arolinks.com', 'mahnokari.com', 'darkguruji.com']
    for d in doms:
        s.cookies.set('adcadg', 'insurance,online_colleges,study_abroad,finance,loan', domain=d)
        s.cookies.set('eonstudb', 'insurance,online_colleges,study_abroad,finance,loan', domain=d)
        s.cookies.set('_uocat', 'value', domain=d)

    c_u = u
    ref = u
    
    try:
        for stp in range(1, 9):
            upd(f"⏳link bypassing...\n\nStep {stp} thoda wait kar..")
            
            r = s.get(c_u, headers={"Referer": ref}, timeout=15, allow_redirects=True)
            h = r.text
            f_u = r.url
            
            k = ext_k(f_u, h)
            if k: return k, None

            if 'countdown' in h.lower() or 'ce-time' in h.lower() or 'please wait' in h.lower():
                for i in range(16, 0, -4):
                    upd(f"⏳ TIMER STARTED...\n\n{i} BOLA NA WAIT KAR LAUDE..")
                    time.sleep(4)
                    
                try:
                    vr = s.get(u, headers={"Referer": f_u}, timeout=15)
                    k = ext_k(vr.url, vr.text)
                    if k: return k, None
                except: 
                    pass

            for cn, cv in re.findall(r'document\.cookie\s*=\s*["\']\s*([^=]+)=([^;"\']+)', h):
                if cn.strip() not in ['adcadg', 'eonstudb', '_uocat']:
                    s.cookies.set(cn.strip(), cv.strip(), domain=urlparse(f_u).netloc)

            n_u = None
            
            jm = re.search(r'(?:window|document)\.location(?:\.href|\.replace)?\s*[\(=]\s*["\']([^"\']+)["\']', h, re.IGNORECASE)
            if jm: 
                n_u = jm.group(1)
            
            if not n_u:
                mm = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\']\d+;\s*url=([^"\']+)["\']', h, re.IGNORECASE)
                if mm: 
                    n_u = mm.group(1)
                    
            if not n_u:
                for at in re.findall(r'<a\s+[^>]+>', h, re.IGNORECASE):
                    if re.search(r'id=["\'](?:btn\d*|getlink|cross-snp2)["\']', at, re.IGNORECASE) or 'class="ce-btn' in at.lower() or 'readmore' in at.lower():
                        hm = re.search(r'href=["\']([^"\']+)["\']', at, re.IGNORECASE)
                        if hm:
                            cd = hm.group(1).strip()
                            if cd and cd != "#" and not cd.lower().startswith("javascript:"):
                                n_u = cd
                                break
                                
            if not n_u:
                fms = re.findall(r'<form(.*?)>(.*?)</form>', h, re.DOTALL | re.IGNORECASE)
                for fa, fi in fms:
                    if 'search' in fa.lower() or 'comment' in fa.lower(): continue
                    am = re.search(r'action=["\']([^"\']+)["\']', fa, re.IGNORECASE)
                    if am:
                        act = am.group(1)
                        ins = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', fi, re.IGNORECASE)
                        dt = {k: v for k, v in ins}
                        pr = s.post(urljoin(f_u, act), headers={"Referer": f_u}, data=dt, timeout=15)
                        k = ext_k(pr.url, pr.text)
                        if k: return k, None
                        n_u = pr.url
                        break
            
            if n_u:
                n_u = urljoin(f_u, n_u)
                if n_u.strip('/') == f_u.strip('/'):
                    cr = s.get(u, headers={"Referer": f_u}, timeout=15)
                    k = ext_k(cr.url, cr.text)
                    if k: return k, None
                    break 
                    
                ref = f_u
                c_u = n_u
                continue

            fp = s.get(u, headers={"Referer": f_u}, timeout=15)
            k = ext_k(fp.url, fp.text)
            if k: return k, None
            break

        return None, "Link Expired!"
        
    except Exception as e:
        return None, "Error in network.."

@bot.message_handler(commands=['start'])
def st(m):
    bot.reply_to(m, "ABE LAUDU! URL BHEJ COPY KARKE")

@bot.message_handler(func=lambda m: 'arolinks.com' in m.text)
def hl(m):
    sm = bot.reply_to(m, "💋 CHURRI PROCESSING STARTED...")
    
    k, e = byp(m.text.strip(), bot, m.chat.id, sm.message_id)
    
    if k:
        try: 
            bot.edit_message_text(f"✅ **Lo bhai tumhari key:**\n\n`{k}`\n\nMera muh me lo pahle", m.chat.id, sm.message_id, parse_mode="Markdown")
        except: 
            pass
    else:
        try: 
            bot.edit_message_text(f"❌ **Bypass fail ho gya bhai!**\n\n_{e}_", m.chat.id, sm.message_id, parse_mode="Markdown")
        except: 
            pass

    cm = bot.send_message(m.chat.id, "⏳ Cool down chal rha h laudu...")
    for i in range(90, 0, -5):
        try: 
            bot.edit_message_text(f"⏳ JAB YE TIME FINISH HO JAAYE TAB KEY KO SIGMA STUDY ME PASTE KARNA...\n\n**{i} seconds bache h.**", m.chat.id, cm.message_id, parse_mode="Markdown")
        except: 
            pass
        time.sleep(5)
        
    try: 
        bot.edit_message_text("Start The Bot.", m.chat.id, cm.message_id, parse_mode="Markdown")
    except: 
        pass

if __name__ == "__main__":
    threading.Thread(target=run, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)