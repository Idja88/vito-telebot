import sharepoint as sp
import threading
import requests
import telebot
import json
import os
import re
from time import sleep
from telebot import types
from requests_ntlm import HttpNtlmAuth

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = '\\'.join([ROOT_DIR, 'config.json'])

with open(config_path) as config_file:
    config = json.load(config_file)
    tconfig = config['tele_gram']

bot = telebot.TeleBot(tconfig['token'])
BOT_INTERVAL = tconfig['interval']
BOT_TIMEOUT = tconfig['timeout']

KeyBoard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
btn1 = types.KeyboardButton('Подписаться',request_contact=True)
btn2 = types.KeyboardButton('Отписаться')
KeyBoard.row(btn1, btn2)

def botactions():
    @bot.message_handler(commands=['start'])
    def start_command(message):
        bot.send_message(
        message.chat.id,
        'Нажмите "подписаться", чтобы начать получать уведомления по задачам. \n'+
        'Нажмите "отписаться", чтобы перестать получать уведомления по задачам.',
        reply_markup=KeyBoard)

    @bot.message_handler(commands=['help'])
    def help_command(message):
        bot.send_message(
        message.chat.id,
        'Stop it.\n' +
        'Get some help')

    @bot.message_handler(content_types=['contact'])
    def subscribe(message):
        chat = str(message.chat.id)
        phone = str(message.contact.phone_number)
        phone = re.sub('[^A-Za-z0-9]+', '', phone)
        try:
            if not sp.check_subscriber(chat):
                sp.add_subscriber(phone, chat)
                bot.reply_to(message, 'Спасибо за подписку')
            else:
                bot.reply_to(message, 'Вы уже подписаны')
        except:
            print("Error")

    @bot.message_handler(func=lambda message: message.text == 'Отписаться')
    def unsubscribe(message):
        chat = str(message.chat.id)
        try:
            if not sp.check_subscriber(chat):
                bot.reply_to(message, 'Вы ещё не подписаны')
            else:
                sp.delete_subscriber(chat)
                bot.reply_to(message, 'Вы отписались от уведомлений')
        except:
            print("Error")

def bot_polling():
    global bot
    print("Starting bot polling now")
    while True:
        try:
            print("New bot instance started")
            botactions()
            bot.infinity_polling()
        except Exception as ex:
            print("Bot polling failed, restarting in {}sec. Error:\n{}".format(BOT_TIMEOUT, ex))
            bot.stop_polling()
            sleep(BOT_TIMEOUT)
        else:
            bot.stop_polling()
            print("Bot polling loop finished")
            break

polling_thread = threading.Thread(target=bot_polling)
polling_thread.daemon = True
polling_thread.start()

chat_data = {}

if __name__ == "__main__":
    while True:
        try:
            if sp.is_assignedto_subscriber(sp.get_changes(), chat_data) is True:
                chat_id = chat_data['TeleChat']
                task_id = chat_data['TaskId']
                bot.send_message(chat_id, text = f"новая задача {task_id}")
                #sleep(120)
        except KeyboardInterrupt:
            break