from aiogram import types, Dispatcher
from aiogram.types import BotCommandScopeAllGroupChats


async def set_bot_group_commands(dp: Dispatcher):
    await dp.bot.set_my_commands(
        commands=[
            types.BotCommand('start', 'Запустить бота'),
            types.BotCommand('newgroup', 'Начать новую группу'),
            types.BotCommand('restart', 'Перезапустить старую группу'),
            types.BotCommand('reg', 'Войти в группу'),
            types.BotCommand('unreg', 'Войти в группу'),
            types.BotCommand('list', 'Список участников группы'),
            types.BotCommand('pay', 'Добавить новый платеж'),
            types.BotCommand('status', 'Текущий статус вычислений'),
            types.BotCommand('stats', 'Статистика группы'),
            types.BotCommand('history', 'История платежей'),
            types.BotCommand('cancel', 'Отмена'),
            types.BotCommand('end', 'Закончить и рассчитать все транзакции'),
            types.BotCommand('help', 'Справка'),
        ],
        scope=BotCommandScopeAllGroupChats()
    )


async def set_bot_commands(dp: Dispatcher):
    await dp.bot.set_my_commands(
        commands=[
            types.BotCommand('start', 'Запуск'),
            types.BotCommand('help', 'Справка'),
            types.BotCommand('feedback', 'Отзыв')
        ]
    )
