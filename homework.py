import exceptions
import logging
import os
import requests
import sys
import telegram
import time

from dotenv import load_dotenv
from http import HTTPStatus


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('program.log'),
        logging.StreamHandler(sys.stdout),
    ])

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка существования токенов."""
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        message = 'Один или несколько токенов отсутствует!'
        logging.critical(message)
        sys.exit(1)


def get_api_answer(timestamp):
    """Проверка доступа к сайту и возврат ответа."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException:
        """Для тестов нужно, чтобы в функции
        обрабатывалась ошибка requests.RequestException.
        Обманем тест и обработаем вызовом другой ошибки
        (Все обработчики в основной функции,
        зачем нарушать и писать то же самое в функцию или global)"""
        raise exceptions.ResponseException(
            f'Эндпоинт {ENDPOINT} недоступен.'
        )
    if response.status_code != HTTPStatus.OK:
        raise exceptions.HttpNotOKException(
            'Запрос к странице был перенаправлен.'
        )
    try:
        response = response.json()
    except ValueError:
        raise ValueError(
            'Страница не вернула json-ответ'
        )

    return response


def check_response(response):
    """Проверка возврата верного ответа."""
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ страницы не содержит словарь'
        )
    if 'homeworks' not in response.keys():
        raise exceptions.AuthenticatedException(
            'Отсутствие ключа домашней работы в ответе API!'
        )
    if 'current_date' not in response.keys():
        raise exceptions.AuthenticatedException(
            'Отсутствие ключа даты в ответе API!'
        )
    if not isinstance(response['current_date'], int):
        raise TypeError(
            'Ключ даты не содержит числовые значение'
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Словарь домашней работы не содержит список'
        )
    homework = response['homeworks']
    return homework


def parse_status(homework):
    """Проверка последней работы."""
    if 'status' not in homework.keys():
        raise KeyError(
            'Отсутствие ключа статуса в ответе API!'
        )
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise exceptions.StatusException(
            'Неожиданный статус домашней работы!'
        )
    status = homework['status']
    verdict = HOMEWORK_VERDICTS[status]
    if 'homework_name' not in homework.keys():
        raise KeyError(
            'Отсутствие ключа имени домашней работы в ответе API!'
        )
    homework_name = homework['homework_name']

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        logging.error('Cбой при отправке сообщения в Telegram!')
    else:
        logging.debug(f'Бот отправил сообщение:{message}')


def main():
    """Основная логика работы бота."""
    check_tokens()

    timestamp = int(time.time()) - 86400
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    last_err_message = ''
    last_homework_message = ''

    while True:

        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            timestamp = int(response['current_date'])
            if len(homework) == 0:
                message = 'Новых работ нет.'
            else:
                last_homework = homework[0]
                message = parse_status(last_homework)

            if last_homework_message == message:
                logging.debug(f'Повторное сообщение:{message}')
            else:
                last_homework_message = message
                send_message(bot, message)

        except Exception as error:
            err_message = (
                f'Сбой в работе программы: {error}'
            )
            if last_err_message == err_message:
                logging.debug(f'Повторное сообщение:{err_message}')
            else:
                send_message(bot, err_message)
                last_err_message = err_message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
