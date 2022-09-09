import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

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
    try:
        bot.sent_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error(f'Сообщение не отправлено {error}')


def get_api_answer(current_timestamp):
    """Функция делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        logging.error(f'Ошибка запроса к API-сервиса: {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        logging.error(f'Ошибка от API-сервиса {homework_statuses.status_code}')
        raise Exception('Ошибка ответа')
    return homework_statuses.json()


def check_response(response):
    """Проверка корректного ответа API."""
    if not isinstance(response['homeworks'], list):
        raise TypeError('Эндпоинт не является словарём.')
    if response['current_date']:
        return response.get('homeworks')
    return []


def parse_status(homework):
    """Статус домашней работы."""
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
    return all(tokens)


def main():
    """Основная логика работы бота."""
    if not check_tokens:
        message_log = ('Ошибка, отсутствует токен')
        logging.critical(message_log)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            homework_status_json = get_api_answer(current_timestamp)
            homework = check_response(homework_status_json)
            message = parse_status(homework)
            if message:
                homework = message[0]
                send_message(bot, message)
            current_timestamp = homework_status_json.get(current_timestamp)

        except KeyboardInterrupt:
            finish = input(
                'Вы действительно хотите прервать работу бота? Y/N: '
            )
            if finish in ('Y', 'y'):
                print('До встречи!')
                break
            elif finish in ('N', 'n'):
                print('Продолжаем работать!')

        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
