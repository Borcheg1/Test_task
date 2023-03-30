"""
Модуль для получения корректного курса валюты.
К сожалению воспользоваться сайтом cbr.ru не удалось, сайт доступен только из РФ.
Парсим Google.com. Там обновление валюты, судя по документации, происходит раз в 5-10 минут.
"""

from bs4 import BeautifulSoup

import requests
import re


# Валюта по коду (ISO 4217), по отношению к которой будет рассчитываться стоимость
main_cur = 'USD'

# Валюта по коду (ISO 4217), стоимость которой надо узнать
sec_cur = 'RUB'

# Урл на сайт Google.com с переданными параметрами
url = f'https://www.google.com/search?q={main_cur}+{sec_cur}'


def get_cur_value(url=url):
    """
    Поиск на Google.com стоимости валюты.

    :param url: str, урл на сайт Google.com с параметрами поиска
    :return: float, стоимость валюты
    """

    response: requests.models.Response = requests.get(url)
    data: str = response.text
    soup: str = BeautifulSoup(data, 'html.parser').text.split('=')[1]

    # Поиск в строке значения типа "65,13" или "600,00"
    # Если значение будет больше 999,99, то гугл пишет цифру как 1.234,56 с использованием символа "."
    pattern: str = re.search(r'\b\d+[,]\d{2}\b', soup)[0]

    # Заменяем символ "," на символ "." и переводим в тип float
    current_value: float = float(pattern.replace(',', '.'))
    return current_value
