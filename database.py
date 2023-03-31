"""
Используется база данных PostgreSQL
Класс, отвечающий за все запросы к базе данных
"""

import os

import psycopg2


class GoogleSheetDatabase:
    def __init__(self):
        """
        Конструктор класса

        Для обеспечения коннекта к базе данных задайте следующие
        переменные окружения в файле .env

        PGDATABASE: str, название базы данных, например PGDATABASE=google_sheets
        PGUSER: str, имя пользователя, например PGUSER=postgres
        PGPASSWORD: str, пароль к базе данных, например PGPASSWORD=123
        PGHOST: str, хост базы данных, например PGHOST=localhost
        PGPORT: str, порт базы данных, например PGPORT=5432
        """

        self.connection = psycopg2.connect(
            database=os.environ["PGDATABASE"],
            user=os.environ["PGUSER"],
            password=os.environ["PGPASSWORD"],
            host=os.environ["PGHOST"],
            port=os.environ["PGPORT"]
        )
        self.cursor = self.connection.cursor()

    def create_sheet_table(self):
        """
        Запрос на создание таблицы основаной на google sheet, если таблицы с таким названием не существует
        :return: None
        """

        with self.connection:
            self.cursor.execute(
                'CREATE TABLE IF NOT EXISTS google_sheet ('
                '№ INTEGER PRIMARY KEY,'
                '"Заказ №" INTEGER UNIQUE,'
                '"Стоимость,$" INTEGER,'
                '"Срок поставки" VARCHAR (15),'
                '"Стоимость в руб." NUMERIC (10, 2))'
            )

    def get_all_data(self):
        """
        Запрос на получение всех данных из таблицы

        :return: list[tuple], лист с кортежами данных каждой строки таблицы
        """
        with self.connection:
            self.cursor.execute("SELECT * FROM google_sheet")
        return self.cursor.fetchall()

    def update_table(self, row, rub):
        """
        Запрос на добавление строки в таблицу

        :param row: tuple[list[int, int, int, str]], кортеж со списками, в которых содержатся данные для
                    четырех столбцов таблицы
        :return: None
        """

        with self.connection:
            self.cursor.execute(
                'INSERT INTO google_sheet (№, "Заказ №", "Стоимость,$", "Срок поставки", "Стоимость в руб.")'
                'VALUES (%s, %s, %s, %s, %s)',
                (int(row[0]), int(row[1]), int(row[2]), row[3], rub)
            )

    def delete_all_rows(self):
        """
        Запрос на удаление всех строк из таблицы, кроме заголовков

        :return: None
        """
        with self.connection:
            self.cursor.execute("DELETE FROM google_sheet WHERE № > 0")


class TelegramDatabase(GoogleSheetDatabase):
    def create_telegram_table(self):
        """
        Запрос на создание таблицы пользователей телеграм, если таблицы с таким названием не существует
        :return: None
        """

        with self.connection:
            self.cursor.execute(
                'CREATE TABLE IF NOT EXISTS telegram_id ('
                '№ serial PRIMARY KEY,'
                'user_id INTEGER UNIQUE)'
            )

    def add_user(self, user_id):
        """
        Добавление id пользователя.
        :param user_id: int, id пользователя
        :return: None
        """

        with self.connection:
            self.cursor.execute("INSERT INTO telegram_id (user_id) VALUES (%s)", (user_id,))

    def check_user_exist(self, user_id):
        """
        Проверка есть ли пользователь в БД

        :param user_id: int, id пользователя
        :return: bool
        """

        with self.connection:
            self.cursor.execute("SELECT user_id FROM telegram_id WHERE user_id = (%s)", (user_id,))
            return bool(len(self.cursor.fetchall()))

    def get_users_ids(self):
        """
        Получение id всех пользователей.

        :return: list[tuple], лист с кортежами, в которых user_id: int
        """

        with self.connection:
            self.cursor.execute("SELECT user_id FROM telegram_id")
            return self.cursor.fetchall()


