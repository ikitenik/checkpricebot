from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from aiogram.filters import Command, CommandStart
from aiogram import Router
from config_data.config import Config, load_config
from handlers.handlers_functions import get_text_message, show_buttons, buttons_redirect
from handlers.handlers_functions import del_product, add_product, check_product
#from filters.filters import
import logging
from services.user_states import UserState, set_state, get_state
from filters.filters import StateFilter


logger = logging.getLogger(__name__)
# Инициализируем роутер уровня модуля
router = Router()
config: Config = load_config()
bot = Bot(token = config.tg_bot.token)


# Обработчик нажатий на кнопки
@router.callback_query()
async def callback_worker(call: CallbackQuery):
    user_id = call.from_user.id
    await buttons_redirect(user_id, call)

# Обработчик проверки текущей стоимости товара
@router.message(StateFilter(UserState.CHECK))
async def handle_check(message: Message):
    await check_product(message)

# Обработчик удаления товара из отслеживаемых
@router.message(StateFilter(UserState.DEL))
async def handle_del(message: Message):
    await del_product(message)

# Обработчик добавления товара
@router.message(StateFilter(UserState.ADD))
async def handle_add(message: Message):
    await add_product(message)


@router.message(CommandStart())
async def get_any_message(message: Message):
    await get_text_message(message)


@router.message()
async def get_any_message(message: Message):
    await get_text_message(message)

