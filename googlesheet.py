"""
Класс GoogleTable отвечает за работу с Google Sheet.
"""

from datetime import datetime

import pygsheets
from loguru import logger
from dotenv import load_dotenv

import currency
from database import GoogleSheetDatabase

load_dotenv()
sheet_db = GoogleSheetDatabase()


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

        # Получаем актуальное значение валюты
        cur = currency.get_cur_value()

        # Проверяем, если предыдущая сохраненная гугл таблица в объекте current_table отсутствует,
        # то создаем новую таблицу в базе данных (если таблицы с таким названием еще не существует).
        # После создания или если таблица не равна текущей переменной all_table, то обновляем таблицу в базе данных.
        if self.current_table is None or self.current_table != all_table:
            if self.current_table is None:
                try:
                    sheet_db.create_sheet_table()
                except Exception as error:
                    logger.debug(f"{error} query create_table didn't work")

            try:
                sheet_db.delete_all_rows()
            except Exception as error:
                logger.debug(f"{error} query delete_all_rows didn't work")

            for row in all_table:
                # Считаем цену в рублях
                rub_col = round(int(row[2]) * cur, 2)
                try:
                    sheet_db.update_table(row, rub_col)
                except Exception as error:
                    logger.debug(f"{error} query update_table didn't work")

            # обновляем объект current_table
            self.current_table = all_table

    def check_expired_date(self):
        """
        Функция проверяет текущую дату, с датой в колонке "Срок поставки" в google_sheet.
        Если текущая дата больше даты из колонки "Срок поставки", то добавляем этот заказ в список.

        :return: list[list[int, int, int, str]], список с заказами, у которых истек срок поставки.
        """

        expired_dates = ""
        if self.current_table:
            for row in self.current_table:
                date = datetime.strptime(row[3], "%d.%m.%Y")
                if datetime.now() > date:
                    expired_dates += f"Заказ №{row[1]} на сумму ${row[2]} истек {row[3]}\n"
        return expired_dates
