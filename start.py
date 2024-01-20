import pip

names=['threaded','telebot','datetime','telebot','requests','pytz','flask','bs4']

for name in names:
    pip.main(['install', name])

import main

main.start_bot()