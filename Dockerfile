FROM python:3.10

WORKDIR /finance-telebot-1

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

CMD [ "python", "main.py"]