# Cервис YaTube.

## Описание
Сервис блога с возможностью регистрации ползователей, создания публикаций, групп.

## Технологии
- Python 3.7
- Python Telegram Bot 13.7

# Установка
## Документация
# Копирование репозитория
Клонируем репозиторий
```
~ git clone git@github.com:Certelen/homework_telebot.git
```
Переходим в клонированный репозиторий
```
~ cd {путь до папки с клонированным репозиторем}
~ cd homework_telebot
```
Устанавливаем и активируем виртуальное окружение
```
~ py -3.7 -m venv venv
~ . venv/Scripts/activate
```
Устанавливаем требуемые зависимости:
```
~ pip install -r requirements.txt
```
# env
Создаем файл .env и заполняем его:
```
- PRACTICUM_TOKEN - Токен пользователя Яндекс.Практикума
- TELEGRAM_TOKEN - Токен бота Телеграма
- TELEGRAM_CHAT_ID - Id пользователя, которому отправляются сообщения
```
# Запуск
Запуск сервиса производится командой:
```
~ python homework.py
```
### Авторы
- :white_check_mark: [Коломейцев Дмитрий(Certelen)](https://github.com/Certelen)
