from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running 24/7 !"

def run():
    # Ye web server port 8080 par chalega
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Threading ka use kar rahe hain taaki bot aur website dono ek saath chalein
    t = Thread(target=run)
    t.start()