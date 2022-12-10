class ResponseException(Exception):
    """Эндпоинт недоступен."""

    pass


class HttpNotOKException(Exception):
    """Запрос к эндпоинту был перенаправлен."""

    pass


class AuthenticatedException(Exception):
    """Неверный auth токен."""

    pass


class StatusException(Exception):
    """Статуса нет в таблице."""

    pass
