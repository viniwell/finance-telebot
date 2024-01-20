import requests
from bs4 import BeautifulSoup
def get_price(url):
    try:
        price = requests.get(url)
        bs = BeautifulSoup(price.text, 'html.parser')
        return bs.find('div', class_='YMlKec fxKbKc').text
    except Exception:
        return 'Couldn`t find any data('
    
    