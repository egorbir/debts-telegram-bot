import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.utils import executor

from src.data.config import BOT_TOKEN
from src.handlers import register_payment_handlers, register_common_handlers, register_statistics_handlers
from src.utils.set_bot_commands import set_bot_commands

logger = logging.getLogger(__name__)


async def startup(dispatcher: Dispatcher):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.info('Bot started')

    await set_bot_commands(dispatcher)

    register_payment_handlers(dp=dispatcher)
    register_common_handlers(dp=dispatcher)
    register_statistics_handlers(dp=dispatcher)


async def shutdown(dispatcher: Dispatcher):
    dispatcher.stop_polling()
    logger.info('Bot stopped')


if __name__ == '__main__':
    bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    redis_storage = RedisStorage2(host='localhost', port=6379, db=1)
    dp = Dispatcher(bot=bot, storage=redis_storage)

    executor.start_polling(dispatcher=dp, on_startup=startup, on_shutdown=shutdown)
