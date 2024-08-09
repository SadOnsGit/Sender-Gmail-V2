from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


mkp_main = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='📧 Начать рассылку',
                             callback_data='start.work')
    ],
    [
        InlineKeyboardButton(text='👁 Автоответ',
                             callback_data='start.autoanswer')
    ]
])