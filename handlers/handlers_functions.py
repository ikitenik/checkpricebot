from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from services.other_functions import check_new_user, check_list,check_duplicate, PositiveNumbers
from marketplaces.ozon import get_data
from services.user_states import UserState, set_state, get_state
from config_data.config import Config, load_config
import aiosqlite
import time
import asyncio
import threading
import schedule

config: Config = load_config()
bot = Bot(token=config.tg_bot.token)


# Стартовое сообщение
async def get_text_message(message: Message):
    user_id = message.from_user.id
    if await check_new_user(user_id):
        await bot.send_message(user_id, "Добро пожаловать в Телеграм-бот по отслеживанию стоимости товаров")
    await bot.send_message(user_id, "Выберите действие")
    await show_buttons(user_id)


# Вывод кнопок в inline-режиме
async def show_buttons(user_id):
    keys = []
    keys.append(InlineKeyboardButton(text='Добавить товар', callback_data='choice_add'))
    keys.append(InlineKeyboardButton(text='Убрать товар', callback_data='choice_del'))
    keys.append(InlineKeyboardButton(text='Посмотреть список товаров', callback_data='choice_show'))
    keys.append(InlineKeyboardButton(text='Посмотреть текущую стоимость', callback_data='choice_check'))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[i] for i in keys],)
    await bot.send_message(user_id, text='Выберите пункт', reply_markup=keyboard)


# Присвоение состояний пользователям и отправка их на выбранные кнопками обработчики
async def buttons_redirect(user_id: int, call):
    # Добавление товара для отслеживания
    if call.data == "choice_add":
        await bot.send_message(call.message.chat.id, "Отправьте ссылку на товар")
        await set_state(user_id, UserState.ADD)

    # Удаление товара из отслеживания
    if call.data == "choice_del":
        if await check_list(call.message.chat.id):
            await bot.send_message(call.message.chat.id, "Напиши id товара, которое надо удалить")
            await set_state(user_id, UserState.DEL)
        else:
            await bot.send_message(call.message.chat.id, "Товаров нет")
            await asyncio.sleep(1)
            await show_buttons(call.message.chat.id)

    # Вывод списка отслеживаемых товаров
    if call.data == "choice_show":
        await set_state(user_id, UserState.NO)
        if await check_list(call.message.chat.id):
            await bot.send_message(call.message.chat.id, "Вот Ваши товары")
            await show_list(call.message.chat.id)
        else:
            await bot.send_message(call.message.chat.id, "Товаров нет")
        await asyncio.sleep(1)
        await show_buttons(call.message.chat.id)

    if call.data == "choice_check":
        if await check_list(call.message.chat.id):
            await bot.send_message(call.message.chat.id, "Напиши id товара, стоимость которого хотите узнать")
            await set_state(user_id, UserState.CHECK)
        else:
            await bot.send_message(call.message.chat.id, "Товаров нет")
            await asyncio.sleep(1)
            await show_buttons(call.message.chat.id)


# Вывод списка отслеживаемых товаров
async def show_list(user_id):
    async with aiosqlite.connect(config.db.database) as connection:
        async with connection.execute('select * from products where user = ?', (user_id,)) as cursor:
            products_list = await cursor.fetchall()
    for product_info in products_list:
        message = f'ID:{product_info[0]}\n{product_info[2]}\nСтоимость без карты озон: {product_info[8]} рублей\n' \
                   f'Стоимость с картой озон: {product_info[9]} рублей\nСсылка: {product_info[5]}\n'
        await bot.send_message(user_id, message)


# Проверка текущей стоимости товара
async def check_product(message: Message):
    user_id = message.from_user.id
    try:
        int(message.text)
        if int(message.text) < 0:
            raise PositiveNumbers("ID должен быть не меньше 0")
    except ValueError:
        await bot.send_message(user_id, "Значение должно быть числом")
        await bot.send_message(user_id, "Введите ID еще раз")
    except PositiveNumbers as pn:
        await bot.send_message(user_id, str(pn))
        await bot.send_message(user_id, "Введите ID еще раз")
    else:
        async with aiosqlite.connect(config.db.database) as connection:
            async with connection.execute('select user from products where id = ?', (int(message.text),)) as cursor:
                user = await cursor.fetchall()
        if len(user) != 0 and user[0][0] == user_id:
            await set_state(user_id, UserState.NO)  # Сброс состояния
            async with aiosqlite.connect(config.db.database) as connection:
                async with connection.execute('select * from products where id = ?',
                                              (int(message.text),)) as cursor:
                    product_info = cursor.fetchall()
            product_info = product_info[0]
            await bot.send_message(message.chat.id, "Подождите")
            price = await get_data(product_info[5])
            message = ""
            message += f'ID:{product_info[0]}\n{product_info[2]}\nСтоимость без карты озон: {price[0]} рублей\n' \
                       f'Стоимость с картой озон: {price[1]} рублей\nСсылка: {product_info[5]}\n'
            if price[0] != product_info[8] or price[1] != product_info[9]:
                async with aiosqlite.connect(config.db.database) as connection:
                    async with connection.execute('UPDATE products SET price_nocard_current = ?,'
                                                  ' price_card_current = ? WHERE id = ?',
                               (price[0], price[1], product_info[0])) as cursor:
                        await connection.commit()
            await bot.send_message(product_info[1], message)
            await asyncyo.sleep(1)
            await show_buttons(product_info[1])
        else:
            button = InlineKeyboardButton(text='Посмотрите список товаров', callback_data='choice_show')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
            await bot.send_message(message.chat.id, "У Вас нет такого ID.\nВведите ID снова или", reply_markup=keyboard)


# Удаление отслеживаемого товара
async def del_product(message: Message):
    user_id = message.from_user.id
    try:
        int(message.text)
        if int(message.text) < 0:
            raise PositiveNumbers("ID должен быть не меньше 0")
    except ValueError:
        await bot.send_message(user_id, "Значение должно быть числом")
        await bot.send_message(user_id, "Введите ID еще раз")
    except PositiveNumbers as pn:
        await bot.send_message(user_id, str(pn))
        await bot.send_message(user_id, "Введите ID еще раз")
    else:
        connection = await aiosqlite.connect(config.db.database)
        cursor = await connection.execute('select user from products where id = ?', (int(message.text),))
        user = await cursor.fetchall()
        await cursor.close()
        await connection.close()
        if len(user) != 0 and user[0][0] == user_id:
            await set_state(user_id, UserState.NO)  # Сброс состояния
            async with aiosqlite.connect(config.db.database) as connection:
                async with connection.execute('delete from products where id = ?', (int(message.text),)) as cursor:
                    await bot.send_message(message.chat.id, "Товар удален")
                    await connection.commit()
            await show_buttons(message.chat.id)
        else:
            button = InlineKeyboardButton(text='Посмотрите список товаров', callback_data='choice_show')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
            await bot.send_message(message.chat.id, "У Вас нет такого ID.\nВведите ID снова или", reply_markup=keyboard)


# Добавление товара
async def add_product(message):
    user_id = message.from_user.id
    url = message.text
    if await check_duplicate(user_id, url):
        await bot.send_message(message.chat.id, "Товар уже добавлен")
        await set_state(user_id, UserState.NO)
        await asyncio.sleep(1)
        await show_buttons(user_id)
        return
    await bot.send_message(message.chat.id, "Подождите")
    result = await get_data(url)
    if result[0] == "Нет":
        await bot.send_message(user_id, "Товар не найден или ссылка введена некорректно\nОтправьте ссылку еще раз")
    else:
        async with aiosqlite.connect(config.db.database) as connection:
            async with connection.execute('INSERT INTO products (user, name, price_nocard, price_card, url,'
                       ' price_nocard_current, price_card_current, price_nocard_min, price_card_min)'
                       ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (user_id, result[2].replace("\\u002F ", ""), result[0],
                        result[1], url, result[0], result[1], result[0], result[1])):
                await connection.commit()

        await bot.send_message(message.chat.id, "Товар добавлен")
        await set_state(user_id, UserState.NO)
        await asyncio.sleep(1)
        await show_buttons(user_id)


# Проверка с перерывом в час, не изменилась ли стоимость товаров
async def run_scheduler():
    while True:
        cursor = connection.cursor()
        cursor.execute("select * from products")
        products = cursor.fetchall()
        cursor.close()
        for i in range(len(products)):
                if (products[i][5]) != "":
                    price = await get_data(url = products[i][5])
                    if price[0] < products[i][6] or price[1] < products[i][7]:

                        message = ""
                        message += f'Стоимость товара:{products[i][2]} уменьшилась c {products[i][6]} до {price[0]}' \
                                   f' рублей без карты озон и c {products[i][7]} до {price[1]} рублей с картой\n'
                        cursor = connection.cursor()
                        cursor.execute(
                            'UPDATE products SET price_nocard_min = ?, price_card_min = ? WHERE id = ?',
                            (price[0], price[1], products[i][0]))
                        cursor.execute(
                            'UPDATE products SET price_nocard_current = ?, price_card_current = ? WHERE id = ?',
                            (price[0], price[1], products[i][0]))

                        connection.commit()
                        cursor.close()
                        await bot.send_message(products[i][1], message)
                    await asyncio.sleep(60)
        await asyncio.sleep(3600)


def start_scheduler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_scheduler())

scheduler_thread = threading.Thread(target=start_scheduler)
scheduler_thread.start()