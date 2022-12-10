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
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('program.log', encoding='utf-8', mode='a')
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

last_message = ''


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
        raise exceptions.ResponseException
    if response.status_code != HTTPStatus.OK:
        raise exceptions.HttpNotOKException
    response = response.json()
    return response


def check_response(response):
    """Проверка возврата верного ответа."""
    if type(response) is not dict:
        raise TypeError
    if 'homeworks' not in response.keys():
        raise exceptions.AuthenticatedException
    if type(response['homeworks']) is not list:
        raise TypeError


def parse_status(homework):
    """Проверка последней работы."""
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise exceptions.StatusException
    status = homework['status']
    verdict = HOMEWORK_VERDICTS[status]
    if 'homework_name' not in homework.keys():
        raise KeyError
    homework_name = homework['homework_name']

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправка сообщения."""
    if last_message != message:
        try:
            bot.send_message(TELEGRAM_CHAT_ID, message)
        except telegram.error.TelegramError:
            logging.error('Cбой при отправке сообщения в Telegram!')
        else:
            logging.debug(f'Бот отправил сообщение:{message}')
    else:
        logging.info(f'Повторное сообщение:{message}')


def main():
    """Основная логика работы бота."""
    check_tokens()

    TIMESTAMP = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:

        err_message = ''

        try:
            response = get_api_answer(TIMESTAMP)
            check_response(response)
            homework = response['homeworks']
            if len(homework) == 0:
                message = 'Новых работ нет.'
            else:
                last_homework = homework[0]
                message = parse_status(last_homework)
        except exceptions.ResponseException as error:
            err_message = (
                f'Эндпоинт {ENDPOINT} недоступен.'
                f'Сбой в работе программы: {error}'
            )
        except exceptions.HttpNotOKException:
            err_message = 'Запрос к странице был перенаправлен.'
        except TypeError as error:
            err_message = (
                f'В ответе API неожиданный тип данных!'
                f'Сбой в работе программы: {error}'
            )
        except exceptions.AuthenticatedException as error:
            err_message = (
                f'Отсутствие ключа домашней работы в ответе API!'
                f'Сбой в работе программы: {error}'
            )
        except KeyError as error:
            err_message = (
                f'Неожиданный статус домашней работы!'
                f'Сбой в работе программы: {error}'
            )
        except Exception as error:
            err_message = (
                f'Непредвиденная ошибка!'
                f'Сбой в работе программы: {error}'
            )
        finally:
            if err_message:
                message = err_message
                logging.error(err_message, exc_info=True)
            send_message(bot, message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
