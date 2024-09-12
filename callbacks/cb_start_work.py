import time
import asyncio

from aiosmtplib import send
from email.mime.text import MIMEText
from aiogram.types import CallbackQuery, Message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from settings import config, EDIT_MSG_DELAY
from keyboard.mkp_cancel import mkp_cancel
from external.messages import send_to_group
from bot_create import bot
from modules.randomize_msg import generate_variations


class Startwork(StatesGroup):
    credentials = State()
    theme = State()
    text = State()
    recipients = State()


router_cb_start = Router()

@router_cb_start.callback_query(F.data.startswith('start.'))
async def start_working(call: CallbackQuery, state: FSMContext):
    if call.data == 'start.work':
        await call.message.edit_text(text='<b>📝 Введите данные от аккаунтов:</b>',
                                     parse_mode='html', reply_markup=mkp_cancel)
        await state.set_state(Startwork.credentials)


@router_cb_start.message(Startwork.credentials)
async def input_credentials(msg: Message, state: FSMContext):
    await state.update_data(credentials=msg.text.split('\n'))
    await msg.answer('<b>📝 Введите тему рассылки: </b>', parse_mode='html')
    await state.set_state(Startwork.theme)


@router_cb_start.message(Startwork.theme)
async def input_theme(msg: Message, state: FSMContext):
    await state.update_data(theme=msg.text)
    await msg.answer('<b>📝 Введите текст рассылки(можно с html тегами)</b>',
                     parse_mode='html')
    await state.set_state(Startwork.text)
    
    
@router_cb_start.message(Startwork.text)
async def input_text(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await msg.answer('<b>📝 Отправьте список получателей (можно в формате txt)</b>',
                     parse_mode='html')
    await state.set_state(Startwork.recipients)
    

@router_cb_start.message(Startwork.recipients)
async def input_recipients(msg: Message, state: FSMContext):
    recipients = msg.text
    if msg.document:
        file_id = msg.document.file_id
        file = await bot.get_file(file_id)
        content = await bot.download_file(file.file_path)
        content_str = content.read().decode('utf-8')
        recipients = content_str.strip()
    recipients_list = recipients.strip().split('\n')
    data = await state.get_data()
    count_accs = len(data['credentials'])
    COUNT_MSG = config.get_count_messages()
    if count_accs * COUNT_MSG > len(recipients_list):
        await msg.reply(f'<b>❌ Количество получателей должно быть равно или больше: {count_accs * COUNT_MSG}</b>',
                        parse_mode='html')
        return
    await state.clear()
    await send_to_emails(msg, data, recipients_list)


async def send_to_emails(msg, data: dict, recipients: list):
    count_recipients = len(recipients)
    count = 0
    last_edit_time = 0
    COUNT_MSG = config.get_count_messages()
    config.count_errors = 0
    
    count_sent = 0
    count_need_sent = config.get_count_messages()
    
    accounts = data['credentials']
    theme = data['theme']
    text = data['text']
    
    delay = config.get_delay()
    message_count = await msg.answer(f'<b>⌛️ Начинаем рассылку! Отправлено: [{count}/{count_recipients}]</b>',
                    parse_mode='html')
    smtp_settings = {
        'hostname': 'smtp.gmail.com',
        'port': 587
    }
    # Список для хранения задач
    tasks = []
    generation = config.get_generation()
    for acc in accounts:
        config.update_error(False)
        user = acc.split(':')[0]
        password = acc.split(':')[1]
        smtp_settings['user'] = user
        smtp_settings['password'] = password
        for recipient in recipients[count_sent:count_need_sent]:
            if config.get_status_error():
                break
            count += 1
            current_time = time.time()
            if generation:
                generate_theme = await generate_variations(theme)
                generate_text = await generate_variations(text)
            # Обновляем сообщение о статусе
            if current_time - last_edit_time >= EDIT_MSG_DELAY:
                await message_count.edit_text(
                    f'<b>⌛️ Начинаем рассылку!'
                    f'\n⌛️ Задержка: {delay} сек'
                    f'\n🤖 Генерация: {"включена" if generation else "выключена"}'
                    f'\n✉️ Кол-во сообщений на 1 аккаунт: {COUNT_MSG}'
                    f'\n✅ Отправлено: [{count}/{count_recipients}]'
                    f'\n🚫 Ошибок во время отправки: {config.get_count_errors()}'
                    f'\n➡️ Рассылка идёт с аккаунта: {user}</b>',
                    parse_mode='html')
                last_edit_time = current_time
            if generation:
                task = asyncio.create_task(send_email(generate_theme, generate_text, recipient, smtp_settings))
            else:
                task = asyncio.create_task(send_email(theme, text, recipient, smtp_settings))
            tasks.append(task)
            tasks.append(asyncio.create_task(handle_task(task, acc, msg.from_user.username)))
            await asyncio.sleep(delay)
        count_sent = count
        count_need_sent *= 2

    await msg.answer('<b>✅ Рассылка успешно завершена!</b>', parse_mode='html')
    await send_to_group(f'<b>Пользователь @{msg.from_user.username} разослал {count} писем</b>')


async def handle_task(task, account, user):
    try:
        await task
    except Exception as e:
        config.update_error(True)
        config.count_errors += 1
        await send_to_group(f'<b>Ошибка при отправке письма с аккаунта {account}: {e}\nВозникла у @{user}</b>')

async def send_email(subject, html_body, recipient, smtp_settings):
    message = MIMEText(html_body, 'html')  
    message['Subject'] = subject
    message['From'] = smtp_settings['user']
    message['To'] = recipient
    await send(
        message,
        hostname=smtp_settings['hostname'],
        port=smtp_settings['port'],
        username=smtp_settings['user'],
        password=smtp_settings['password'],
        use_tls=False
    )