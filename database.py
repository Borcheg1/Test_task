"""
Используется база данных PostgreSQL
Класс, отвечающий за все запросы к базе данных
"""

import os

import psycopg2


class DatabasePostgres:
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

    def create_table(self):
        """
        Запрос на создание таблицы, если таблицы с таким названием не существует
        :return: None
        """

        with self.connection:
            self.cursor.execute(
                'CREATE TABLE IF NOT EXISTS google_sheet ('
                '№ INTEGER PRIMARY KEY,'
                '"Заказ №" INTEGER UNIQUE,'
                '"Стоимость,$" INTEGER,'
                '"Срок поставки" VARCHAR (15))'
            )

    def get_all_data(self):
        """
        Запрос на получение всех данных из таблицы

        :return: list[tuple], лист с кортежами данных каждой строки таблицы
        """
        with self.connection:
            self.cursor.execute("SELECT * FROM google_sheet")
        return self.cursor.fetchall()

    def update_table(self, row):
        """
        Запрос на добавление строки в таблицу

        :param row: tuple[list[int, int, int, str]], кортеж со списками, в которых содержатся данные для
                    четырех столбцов таблицы
        :return: None
        """

        with self.connection:
            self.cursor.execute(
                'INSERT INTO google_sheet (№, "Заказ №", "Стоимость,$", "Срок поставки") VALUES (%s, %s, %s, %s)',
                (int(row[0]), int(row[1]), int(row[2]), row[3])
            )

    def delete_all_rows(self):
        """
        Запрос на удаление всех строк из таблицы, кроме заголовков

        :return: None
        """
        with self.connection:
            self.cursor.execute("DELETE FROM google_sheet WHERE № > 0")
