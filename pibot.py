#/usr/bin/env python
# -*- coding: utf8 -*-
import argparse
import logging
import telebot
import subprocess
from json import load
from urllib2 import urlopen

# Disable urllib3 SSL warning because of old python version
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

logger = telebot.logger


class PiBot:

    def __init__(self):
        self.chat_id = None
        self.init_markup()

    def start(self, token, key, host, auth):
        self.key = key
        self.host = host
        self.auth = auth

        self.bot = telebot.TeleBot(token)

        @self.bot.message_handler(commands=['start'])
        def listen_welcome(message):
            self.send_welcome(message)

        @self.bot.message_handler(regexp='^start$')
        @self.check_chat_id
        def listen_start(message):
            self.torrent_start(message)

        @self.bot.message_handler(regexp='^stop$')
        @self.check_chat_id
        def listen_stop(message):
            self.torrent_stop(message)

        @self.bot.message_handler(regexp='^status$')
        @self.check_chat_id
        def listen_status(message):
            self.torrent_status(message)

        @self.bot.message_handler(regexp='^temp$')
        @self.check_chat_id
        def listen_temp(message):
            self.send_temp(message)

        @self.bot.message_handler(regexp='^space$')
        @self.check_chat_id
        def listen_space(message):
            self.send_space(message)

        @self.bot.message_handler(regexp='^ip$')
        @self.check_chat_id
        def listen_ip(message):
            self.send_public_ip(message)

        @self.bot.message_handler(func=lambda message: True)
        @self.check_chat_id
        def listen_all(message):
            self.echo_all(message)

        self.bot.polling()

    def send_welcome(self, message):
        unique_code = self.extract_unique_code(message.text)
        if unique_code == self.key:
            self.save_chat_id(message.chat.id)
            self.send_message(message, 'Hello!')
        else:
            logger.error('Invalid key received: %s' % unique_code)

    def torrent_start(self, message):
        self.send_message(message, 'Starting torrents!')
        output = subprocess.check_output(
            self.build_transmission_base_command() + ['-t', 'all', '--start']
        )
        self.send_message(message, output)

    def torrent_stop(self, message):
        self.send_message(message, 'Stopping torrents!')
        output = subprocess.check_output(
            self.build_transmission_base_command() + ['-t', 'all', '--stop']
        )
        self.send_message(message, output)

    def torrent_status(self, message):
        self.send_message(message, 'Checking torrents!')
        output = subprocess.check_output(
            self.build_transmission_base_command() + ['-l']
        )

        for row in output.split('\n'):
            # We don't want to send the torrent name
            self.send_message(message, ' '.join(row.split('   ')[:-2]))

    def send_temp(self, message):
        # output = subprocess.check_output(
        #     ['/opt/vc/bin/vcgencmd', 'measure_temp']
        # )
        # self.send_message(message, output)
        self.send_message(message, 'unsupported')

    def send_space(self, message):
        # output = subprocess.check_output(
        #     ['df', '-h', '/downloads']
        # )
        # self.send_message(message, output.split('\n')[1])
        self.send_message(message, 'unsupported')

    def send_public_ip(self, message):
        public_ip = load(urlopen('https://api.ipify.org/?format=json'))['ip']
        self.send_message(message, public_ip)

    def echo_all(self, message):
        self.send_message(message, message.text)

    def send_message(self, message, text):
        logger.debug('Sending message: %s' % text)
        self.bot.send_message(
            message.chat.id,
            text,
            reply_markup=self.markup
        )

    def build_transmission_base_command(self):
        return ['transmission-remote', self.host, '--auth', self.auth]

    def check_chat_id(self, func):
        def func_wrapper(message):
            if self.is_valid_chat_id(message.chat.id):
                return func(message)
            else:
                logger.warn('Invalid CHAT_ID, Ignoring message')
        return func_wrapper

    def init_markup(self):
        self.markup = telebot.types.ReplyKeyboardMarkup(row_width=1,
                                                        resize_keyboard=True)
        self.markup.row('start', 'status', 'stop')
        self.markup.row('temp', 'space')

    def extract_unique_code(self, text):
        # Extracts the unique_code from the sent /start command.
        return text.split()[1] if len(text.split()) > 1 else None

    def save_chat_id(self, chat_id):
        logger.info('Saving CHAT_ID: %s' % chat_id)
        self.chat_id = chat_id

    def is_valid_chat_id(self, chat_id):
        logger.debug('Checking CHAT_ID: %s | %s' % (self.chat_id, chat_id))
        return (self.chat_id == chat_id)


def main():

    parser = argparse.ArgumentParser(
        description='Simple telegramBot for managing raspberryPi'
    )

    parser.add_argument(
        '-t, --token', metavar='<token>', dest='token', required=True,
        help='bot token'
    )

    parser.add_argument(
        '-k, --key', metavar='<key>', dest='key', required=True,
        help='bot authentication key'
    )

    parser.add_argument(
        '-H, --host', metavar='<host:port>', dest='host', required=False,
        default='localhost:9091',
        help='host:port of transmission-daemon',
    )

    parser.add_argument(
        '-A, --auth', metavar='<user:pass>', dest='auth', required=False,
        default='admin:admin',
        help='user:password of transmission-daemon',
    )

    args = parser.parse_args()

    logger.setLevel(logging.INFO)

    bot = PiBot()
    bot.start(args.token, args.key, args.host, args.auth)

if __name__ == '__main__':
    main()
