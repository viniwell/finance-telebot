from flask import Flask
from threading import Thread
import random
from main import *

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
  app.run(host='0.0.0.0',port=random.randint(2000,9000))

def keep_alive():
    t = Thread(target=run)
    t.start()
    t=Thread(target=start_bot)
    t.start()
  
keep_alive()