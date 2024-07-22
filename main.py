import asyncio
from aiogram import Bot, Dispatcher
import logging
from config_data.config import Config, load_config
from handlers import handlers

# Настройка логирования
logging.basicConfig(
    filename='bot.log',  # Имя файла для записи логов
    filemode='a',        # Режим записи (a - добавление к существующему, w - перезапись файла)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config: Config = load_config()
    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher()
    dp.include_router(handlers.router)
    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

