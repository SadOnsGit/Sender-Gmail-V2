from aiogram import Router
from aiogram.filters import Command
from aiogram import types

from keyboard.mkp_main import mkp_main

from settings import config


router_start = Router()


@router_start.message(Command('start'))
async def start_message(msg: types.Message):
    await msg.answer('<b>Добро пожаловать в бота рассылку Gmail.'
                     '\n🛠 Текущие настройки проекта:'
                     f'\n🤖 Генерация текста: {"включена" if config.get_generation() else "выключена"}'
                     f'\n✉️ Кол-во сообщений на 1 аккаунт: {config.get_count_messages()}'
                     f'\n⏳ Задержка между сообщениями: {config.get_delay()} секунд(-ы)</b>',
                     parse_mode='html', reply_markup=mkp_main)