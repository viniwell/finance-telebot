import threading
import datetime
import telebot
from config import BOT_TOKEN
from main_function import get_price
import requests
import pytz
from keep_alive import keep_alive
import os
import fcntl

global bot
bot = telebot.TeleBot(BOT_TOKEN)
shelve = {}
lockfile = "/tmp/mybot.lock"

def start_bot():
    if not acquire_lock():
        print("Error: another instance of the bot is already running")
        return
    try:
        while True:
            try:
                bot.polling(non_stop=True)
            except:
                pass
    finally:
        release_lock()

def acquire_lock():
    """Acquire the lock file."""
    if not os.path.exists(lockfile):
        open(lockfile, 'w').close()
    f = open(lockfile, 'r+')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True

def release_lock():
    """Release the lock file."""
    f = open(lockfile, 'r+')
    fcntl.flock(f, fcntl.LOCK_UN)
    os.remove(lockfile)


class User:
    def __init__(self, id, data=[], currencies={}):
        if data:
            self.last_command=data[0]
            self.time=data[1]
            self.currencies=currencies
        else:
            self.last_command=''
            self.time=[0, 0]
            self.currencies={
                'Bitcoin':'https://www.google.com/finance/quote/BTC-USD?sa=X&ved=2ahUKEwj-j6X_kNCDAxWAS_EDHbwmAi8Q-fUHegQIDhAf',
                'Ether':'https://www.google.com/finance/quote/ETH-USD?sa=X&ved=2ahUKEwiCyNm1pdCDAxVncfEDHbAeBkgQ-fUHegQIDhAf',}
        self.id=id
        self.tz=0

        self.start_thread(send_message)
    
    def start_thread(self, func):
        try:
            self.t.cancel()
        except Exception:
            pass
        current_time=datetime.datetime.now(pytz.timezone('UTC'))
        current_time=current_time.hour*3600+current_time.minute*60+current_time.second+self.tz
        if self.time[0]*3600+self.time[1]*60-current_time<0:
            self.t=threading.Timer(24*60*60+self.time[0]*3600+self.time[1]*60-current_time, func, [self.id])
        else:
            self.t=threading.Timer(self.time[0]*3600+self.time[1]*60-current_time, func, [self.id])
        
        self.t.start()

@bot.message_handler(commands=['start'])
def start_command(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='start'
    bot.send_message(message.chat.id, "Hi!You can easily learn cryptocurrency here")

@bot.message_handler(commands=['set_time'])
def set_time(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='set_time'
    responce='Choose time for bot to send a message with information: write it in format hours:minutes'
    bot.send_message(message.chat.id, responce)

@bot.message_handler(commands=['set_time_zone'])
def set_time_zone(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='set_time_zone'
    responce="Select your current time:"
    bot.send_message(message.chat.id, responce, reply_markup=get_tz())

@bot.message_handler(commands=['help'])
def help(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='help'
    text="""Commands available:
    /start - prints statement
    /set_time - Set the time when you want to receive information about cryptocurrency (format: hours:minutes)
    /set_time_zone - Set time zone for bot`s correct work
    /get_defined - Allows to view price of 1 cryptocurrency defined by you
    /get_all - Allows to view all cryptocurrencies
    /add - Allows to add new cryptocurrency
    /delete or /del - Allows to delete one of cryptocurrencies
    /info - Information about your account
    """
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['get_defined'])
def get_defined(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='get_defined'
    responce='Choose one cryptocurrency:'
    bot.send_message(message.chat.id, responce, reply_markup=get_crypto_list(message.from_user.id))

@bot.message_handler(commands=['get_all'])
def get_all_crypto(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='get_all'
    responce='\n'.join(f'{key} - {get_price(shelve[message.from_user.id].currencies[key]).replace("$", "")}' for key in shelve[message.from_user.id].currencies.keys())
    bot.send_message(message.chat.id, responce)

@bot.message_handler(commands=['info'])
def info(message):
    check_user(message.from_user.id)
    time=datetime.datetime.now(pytz.timezone('UTC'))
    time=time.hour*3600+time.minute*60+shelve[message.from_user.id].tz
    responce=f'Message time - {shelve[message.from_user.id].time[0]//10}{shelve[message.from_user.id].time[0]%10}:{shelve[message.from_user.id].time[1]//10}{shelve[message.from_user.id].time[1]%10}\n'+f'Your current time - {time//3600//10}{time//3600%10}:{time%3600//60//10}{time%3600//60%10}\n'+"\n".join(f'{key} - {shelve[message.from_user.id].currencies[key]}' for key in shelve[message.from_user.id].currencies.keys())
    bot.send_message(message.chat.id, responce)

@bot.message_handler(commands=['add'])
def add(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='add'
    responce='Please type name and url(on https://www.google.com/finance/) of cryptocurrency (format: name-url)'
    bot.send_message(message.chat.id, responce)

@bot.message_handler(commands=['delete', 'del'])
def delete(message):
    check_user(message.from_user.id)
    shelve[message.from_user.id].last_command='delete'
    if len(shelve[message.from_user.id].currencies)>1:
        responce='Choose one cryptocurrency to delete'
    else:
        responce="You have just 1 currency left"
    bot.send_message(message.chat.id, responce, reply_markup=get_crypto_list(message.from_user.id))

@bot.message_handler(content_types=['text'])
def text(message):
    check_user(message.from_user.id)
    if shelve[message.from_user.id].last_command=='set_time':
        try:
            time = list(map(int, message.text.split(':')))
            if 0<=time[0]<=23 and 0<=time[1]<=59:
                shelve[message.from_user.id].time=time
                responce=f'Time is set successfully at {shelve[message.from_user.id].time[0]//10}{shelve[message.from_user.id].time[0]%10}:{shelve[message.from_user.id].time[1]//10}{shelve[message.from_user.id].time[1]%10}'
                shelve[message.from_user.id].start_thread(send_message)
            else:
                responce='Incorrect data'
        except Exception:
            responce='Incorrect data'
    elif shelve[message.from_user.id].last_command=='get_defined':
        try:
            responce=f'{message.text} - {get_price(shelve[message.from_user.id].currencies[message.text])}'
        except:
            responce='Incorrect data'
    elif shelve[message.from_user.id].last_command=='add':
        try:
            name, url=message.text[:message.text.index('-')], message.text[message.text.index('-')+1:]
            if name not in shelve[message.from_user.id].currencies.keys():
                if str(requests.get(url))=='<Response [200]>':
                    shelve[message.from_user.id].currencies[name]=url
                    responce=f"Added '{name}' to your currencies."
                else:
                    responce='Invalid url'
            else:
                responce="This currency already exists"
        except Exception:
            responce='Invalid data'
    elif shelve[message.from_user.id].last_command=='delete':
        if len(shelve[message.from_user.id].currencies)>1:
            try:
                del shelve[message.from_user.id].currencies[message.text]
                responce=f'Successfully deleted {message.text}'
            except Exception:
                responce='Incorrect data'
        else:
            responce='You have only 1 currency left'
    elif shelve[message.from_user.id].last_command=='set_time_zone':
        if message.text in list(tz_list.keys()):
            shelve[message.from_user.id].tz=tz_list[message.text]
            responce=f'Time zone set as {message.text}'
        else:
            responce='Incorrect data'
    else:
        responce='I`m sorry, i don`t understand what you want me to do'
    bot.send_message(message.chat.id, responce)

def get_crypto_list(user_id):
    buttons=telebot.types.ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True
    )
    buttons.add(*shelve[user_id].currencies.keys())
    return buttons

def send_message(user_id):
    responce='Fresh cryptocurrency!!\n\n'
    responce+='\n'.join(f'{key} - {get_price(shelve[user_id].currencies[key]).replace("$", "")}' for key in shelve[user_id].currencies.keys())
    bot.send_message(user_id, responce)
    shelve[user_id].start_thread(send_message)

def check_user(user_id):
    if user_id not in shelve.keys():
        shelve[user_id]=User(user_id)

def get_tz():
    buttons=telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True
    )
    utc=datetime.datetime.now(pytz.timezone('UTC'))
    utc=utc.hour*3600+utc.minute*60+utc.second
    global tz_list
    tz_list=sorted([datetime.datetime.now(pytz.timezone(tz)).utcoffset().seconds for tz in pytz.common_timezones_set if datetime.datetime.now(tz=pytz.timezone('UTC')).minute==datetime.datetime.now(pytz.timezone(tz)).minute])
    tz_list={f'{(utc+tz)//3600%24//10}{(utc+tz)//3600%24%10}:{(utc+tz)%3600//60//10}{(utc+tz)%3600//60%10}':tz for tz in tz_list}
    buttons.add(*list(tz_list.keys()))
    return buttons

start_bot()