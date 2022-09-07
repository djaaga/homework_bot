import logging
import os
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Updater

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения."""
    return bot.sent_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    """Функция делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Ошибка запроса к API-сервиса: {error}')
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Ошибка от API-сервиса {response.status_code}')
        raise Exception('Ошибка ответа')
    return response.json()


def check_response(response):
    """Проверка словаря в базе."""
    if response == {0}:
        raise Exception('Словарь пуст')
    if type(response) is not dict:
        raise TypeError('homeworks is not dict')
    if type(response.get('homeworks')) is not list:
        raise TypeError('homeworks is not list')
    homework = response.get('homeworks')
    return homework


def parse_status(homework):
    """Статус домашней работы."""
    if homework == {}:
        return None
    else:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        if not homework_name:
            logging.error('Нету такого имени')
            raise KeyError('Домашняя работа не найдена')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    tokens = [
        PRACTICUM_TOKEN,
        TELEGRAM_CHAT_ID,
        TELEGRAM_TOKEN,
    ]
    if not all(tokens):
        logging.critical('Ошибка отсутствует токен')
        return print('Ошибка отсутствует токен')
    else:
        return True


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(token=TELEGRAM_TOKEN)
    updater.start_polling()
    updater.idle()
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(0)
            homework = check_response(response)
            message = parse_status(homework)
            current_timestamp = current_timestamp
            if message is not None:
                send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в коде зовите админа!: {error}'
            logging.error(message)
            bot.send_message(TELEGRAM_CHAT_ID, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
