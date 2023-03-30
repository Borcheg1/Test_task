"""
Класс GoogleTable отвечает за работу с Google Sheet.
"""

import os
import time

import pygsheets
from dotenv import load_dotenv
from loguru import logger
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

from database import DatabasePostgres


load_dotenv()
scheduler = BackgroundScheduler()
db = DatabasePostgres()

logger.add(
    "log",
    format='{time} {level} {message}',
    level='DEBUG',
    rotation='1 week',
    compression='zip'
)


class GoogleTable:

    current_table = None

    def __init__(
            self,
            credence: str = "client_secret.json",
            sheet_url: str = "https://docs.google.com/spreadsheets/d/1TIy1zfCCm0m6mTXJBixx71lcqNRhOnWfhMCuQYbgV2g/edit#gid=0",
    ) -> None:
        """
        Конструктор класса.

        :param credence: str, путь до файла с сервисным секретным ключом гугл проекта.
        :param sheet_url: str, ссылка на таблицу Google Sheet.
        """

        self.credence = credence
        self.sheet_url = sheet_url

    def _get_sheet_by_url(
            self,
            sheet_client: pygsheets.client.Client
    ) -> pygsheets.Spreadsheet:
        """
        Функция для получения доступа к гугл таблице через передачу урла таблицы
        в объект авторизованного пользователя.

        :param sheet_client: pygsheets.client.Client, объект авторизованного пользователя.
        :return: pygsheets.Spreadsheet, объект для взаимодействия с таблицей.
                 Метод sheet1 возвращает объект первой страницы гугл таблицы.
        """

        sheets: pygsheets.Spreadsheet = sheet_client.open_by_url(
            self.sheet_url
        )
        return sheets.sheet1

    def _get_sheet_client(self):
        """
        Функция авторизации пользователя.

        :return: pygsheets.client.Client, объект авторизованного пользователя.
        """

        return pygsheets.authorize(service_file=self.credence)

    def check_table_changes(self):
        """
        Функция для проверки соответствия текущего наполнения таблицы с таблицей в базе данных.
        Если в гугл таблице были изменения, перезаписываем таблицу в базе данных.

        :return: None
        """

        # Получаем объект гугл таблицы
        try:
            sheet_client: pygsheets.client.Client = self._get_sheet_client()
            wks: pygsheets.Spreadsheet = self._get_sheet_by_url(sheet_client)
        except Exception as error:
            logger.debug(f"{error}: client didn't pass authorization")

        # Берем диапазон ячеек A2:D1000
        all_table = wks.get_values("A2", "D1000")

        # Проверяем, если предыдущая сохраненная гугл таблица в объекте current_table отсутствует
        # или не равна текущей переменной all_table, то обновляем таблицу в базе данных.
        if self.current_table is None or self.current_table != all_table:
            try:
                db.delete_all_rows()
            except Exception as error:
                logger.debug(f"{error} query delete_all_rows didn't work")

            for row in all_table:
                try:
                    db.update_table(row)
                except Exception as error:
                    logger.debug(f"{error} query update_table didn't work")

            # обновляем объект current_table
            self.current_table = all_table


if __name__ == '__main__':
    table = GoogleTable()

    # Добавляем график обновления данных в таблице.
    # Аргументы метода add_job:
    # table.check_table_changes - метод, который будет выполняться по заданнаному графику;
    # 'interval' - аргумент, обозначающий интервальное выполнение функции
    # minutes=1 - аргумент, обозначающий частоту вызова метода table.check_table_changes один раз в минуту.
    # start_time - аргумент, принимающий объект datetime и обозначающий с какого времени начнется интервальный
    #              вызов метода table.check_table_changes;
    # timezone - аргумент, обозначающий часовой пояс
    scheduler.add_job(
        table.check_table_changes,
        'interval',
        minutes=1,
        start_date=datetime.now(),
        timezone='Europe/Moscow'
    )

    scheduler.start()

    # Кустарный способ зациклить работу программы.
    # Время сна в цикле не влияет на частоту вызова функции из графика scheduler
    while True:
        time.sleep(300)
