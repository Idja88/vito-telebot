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
    #Set all your bot handlers inside this function
    #If bot is used as a global variable, remove bot as an input param
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
            if not sp.check_phone(chat):
                sp.new_subscriber(phone,chat)
                bot.reply_to(message, 'Спасибо за подписку')
            else:
                bot.reply_to(message, 'Вы уже подписаны')
        except:
            print("Error")

    @bot.message_handler(func=lambda message: message.text == 'Отписаться')
    def unsubscribe(message):
        chat = str(message.chat.id)
        try:
            if not sp.check_phone(chat):
                bot.reply_to(message, 'Вы ещё не подписаны')
            else:
                sp.delete_subscriber(chat)
                bot.reply_to(message, 'Вы отписались от уведомлений')
        except:
            print("Error")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(f"Получено новое сообщение от {message.chat.username}: {message.text}")
    print(message)
    #bot.reply_to(message, message.text)

def bot_polling():
    #global bot #Keep the bot object as global variable if needed
    global bot
    print("Starting bot polling now")
    while True:
        try:
            print("New bot instance started")
            botactions() #If bot is used as a global variable, remove bot as an input param
            bot.polling(none_stop=True, interval=BOT_INTERVAL, timeout=BOT_TIMEOUT)
        except Exception as ex: #Error in polling
            print("Bot polling failed, restarting in {}sec. Error:\n{}".format(BOT_TIMEOUT, ex))
            bot.stop_polling()
            sleep(BOT_TIMEOUT)
        else: #Clean exit
            bot.stop_polling()
            print("Bot polling loop finished")
            break #End loop

polling_thread = threading.Thread(target=bot_polling)
polling_thread.daemon = True
polling_thread.start()

#Keep main program running while bot runs threaded
if __name__ == "__main__":
    while True:
        try:
            sp.get_changes()
            #sleep(120)
        except KeyboardInterrupt:
            break