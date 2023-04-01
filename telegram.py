"""
Телеграм бот для отправки сообщения пользователю при истечении даты
в колонке "Срок поставки" таблицы google_sheet
"""

from datetime import datetime
import os
import time

from aiogram import Bot, Dispatcher, types, executor
from dotenv import load_dotenv
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from art import tprint

from database import TelegramDatabase
from googlesheet import GoogleTable


load_dotenv()

bot = Bot(os.environ["TOKEN"])
dp = Dispatcher(bot)

telegram_db = TelegramDatabase()
telegram_db.create_telegram_table()

scheduler = AsyncIOScheduler()

table = GoogleTable()

logger.add(
    "log",
    format='{time} {level} {message}',
    level='DEBUG',
    rotation='1 week',
    compression='zip'
)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    """
    Обработчик команды "/start".
    Заносит id пользователя в базу данных и отправляет приветственное сообщение

    :param message: types.Message, входящее сообщение пользователя
    :return: None
    """

    # Получаем id пользователя
    id = message.from_id
    answer = (
        f"Доброго времени суток!✋\n"
        f"Я оповещу Вас, если срок поставки истечет ⏰"
    )

    # Проверяем наличие пользователя в базе денных.
    # Если такого id нет, добавляем в базу
    if not telegram_db.check_user_exist(id):
        try:
            telegram_db.add_user(id)
        except Exception as error:
            logger.debug(f"{error}: id {id} (query add_user didn't work)")

    # отправляем приветственное сообщение
    try:
        await bot.send_message(id, answer, parse_mode="Markdown")
    except Exception as error:
        logger.debug(f"{error}: id {id} (user didn't get start message)")


async def reminder():
    """
    Функция отправляет сообщение в телеграм бота, если есть истекшие сроки поставки.

    :return: None
    """

    # Проверяем, есть ли истекшие даты заказов
    if len(table.check_expired_date()):
        orders = table.check_expired_date()

        # Получаем id пользователей из базы данных
        try:
            users_ids = telegram_db.get_users_ids()
        except Exception as error:
            logger.debug(f"{error}: (query get_users_ids didn't work)")

        # Отправляем всем пользователям сообщение об истекших заказах
        for id in users_ids:
            if id[0]:
                try:
                    await bot.send_message(
                        id[0],
                        f"❗❗❗ У следующих заказов истек срок поставки:\n\n"
                        f"{orders}"
                    )
                except Exception as error:
                    logger.debug(f"{error}; {id} (user didn't get message about expired orders)")
        else:
            print("Order date has expired, check the telegram bot\n")


if __name__ == '__main__':
    tprint('Hello!', 'starwars')
    time.sleep(1.5)
    print("I'll tell you when the table is updated.\n"
          "Don't forget to activate the bot @Test_task12_bot!")

    # Добавляем график обновления данных в таблице.
    # Аргументы метода add_job:
    # table.check_table_changes - функция, которая будет выполняться по заданнаному графику;
    # 'interval' - аргумент, обозначающий интервальное выполнение функции
    # minutes=1 - аргумент, обозначающий частоту вызова метода table.check_table_changes один раз в минуту.
    # start_time - аргумент, принимающий объект datetime и обозначающий с какого времени начнется интервальный
    #              вызов функции;
    # timezone - аргумент, обозначающий часовой пояс
    # Обновление таблицы происходит один раз в минуту.
    scheduler.add_job(
        table.check_table_changes,
        'interval',
        minutes=1,
        start_date=datetime.now(),
        timezone='Europe/Moscow'
    )

    # Проверка на истекший срок поставки происходит раз в 30 минут
    # Если есть истекший срок, отправляет сообщение в телеграм.
    scheduler.add_job(
        reminder,
        'interval',
        minutes=30,
        start_date=datetime.now(),
        timezone='Europe/Moscow'
    )

    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
