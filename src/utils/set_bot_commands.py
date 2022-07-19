from aiogram import types, Dispatcher


async def set_bot_commands(dp: Dispatcher):
    await dp.bot.set_my_commands(
        [
            types.BotCommand('start', 'Запустить бота'),
            types.BotCommand('reg', 'Войти в группу'),
            types.BotCommand('cancel', 'Отменить ввод транзакции'),
            types.BotCommand('end', 'Закончить и рассчитать все транзакции'),
            types.BotCommand('help', 'Справка'),
        ]
    )
