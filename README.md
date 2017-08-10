# python-bazchecker

A small python script I wrote that periodically checks a website that hosts apartment offers and sends new apartment offers to my phone via [Telegram, using its Bots API](https://core.telegram.org/bots/api).

## How to install

Just git clone it.

It works with Python 3, I did not bother testing it with Python2, Pypy, Jython or others.

This script depends on APScheduler, BeautifulSoup4 and pyTelegramBotAPI, all of which can be installed using pip.

It expects you to set up a Bot with Telegram and provide the access token as an env variable called 'TELEBOT_TOKEN'
