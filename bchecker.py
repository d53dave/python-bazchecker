#!/usr/bin/env python3
import time
import re
import os
import logging
import telebot
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_ERROR
from urllib.request import urlopen
from bs4 import BeautifulSoup

LOG_FILENAME="bchecker.log"
LOG_FORMAT="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
DATE_FMT="%c"
logging.basicConfig(level=logging.INFO,
                    format=LOG_FORMAT,
                    datefmt=DATE_FMT)
logging.getLogger("requests").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FMT)
handler = RotatingFileHandler(LOG_FILENAME, maxBytes=131072, backupCount=5)#10mb
handler.setFormatter(formatter)
logger.addHandler(handler)

base_url = 'http://www.bazar.at'
request_url = base_url+'/wien-wohnungen-anzeigen,dir,1,cId,14,fc,9,loc,9,vi,1,ret,9,rf,5,tp,0,at,1925'
chat_ids = set([])
capture_url = re.compile(r"showAdDetail\(\d+,\s+'(\S+)'\)")
cached_results = []
bot = telebot.TeleBot(os.environ['TELEBOT_TOKEN'])

@bot.message_handler(func=lambda message: True, content_types=['document', 'text'])
def command_handle_document(message):
    global chat_ids
    chat_ids.add(message.chat.id)
    logging.info("Registered user %s with chat id %s" % (message.from_user.username, message.chat.id))
    bot.reply_to(message, "You will receive future updates!")

def diff(a, b):
    b = set(b)
    return [aa for aa in a if aa not in b]

def send_new_results(new_results):
    result_count = str(len(new_results))
    msg = "There are %s new offers available!\n" % result_count
    msg += '\n****\n'.join([base_url+item_url for (item_id, item_url) in new_results])
    for chat_id in chat_ids:
        logger.info("Broadcasting %s new offers to chat %s" %(result_count, chat_id))
        bot.send_message(chat_id, msg)

def tick():
    response = urlopen(request_url)
    html_doc = response.read()
    soup = BeautifulSoup(html_doc, 'html.parser')
    new_results = []
    for result in  soup.find_all("li", class_="result"):
        if "tausch" in result['onclick'].lower(): #ignore swaping
            continue
        result_url = re.search(capture_url, result['onclick']).groups()[0]
        new_results.append((result['id'], result_url))
    global cached_results
    result_diff = diff(new_results, cached_results)
    logger.info("Found %s new offers!", str(len(result_diff)))
    if(len(result_diff) > 0):
        cached_results = new_results
        send_new_results(result_diff)


def error_listener(event):
    if event.exception:
        print('The job crashed :(')
        for chat_id in chat_ids:
            bot.send_message(chat_id, "Job crashed with exception [%s]" % event.exception)


if __name__ == '__main__':
    logger.info("Application startup.")
    scheduler = BackgroundScheduler()
    scheduler.add_job(tick, 'interval', minutes=5)
    scheduler.add_listener(error_listener, EVENT_JOB_ERROR)
    scheduler.start()
    bot.polling()

    try:
        while True:
           pass 
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()  
        logger.info("Application shutdown.")
