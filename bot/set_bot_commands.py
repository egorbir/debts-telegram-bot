from aiogram import types, Dispatcher
from aiogram.types import BotCommandScopeAllGroupChats


async def set_bot_group_commands(dp: Dispatcher):
    """
    Set commands for bot working in telegram group
    :param dp: aiogram dispatcher for the bot
    """

    await dp.bot.set_my_commands(
        commands=[
            types.BotCommand("start", "Start bot"),
            types.BotCommand("newgroup", "Create new group of payments"),
            types.BotCommand("restart", "Restart old group of payments"),
            types.BotCommand("reg", "Register in the group of payments"),
            types.BotCommand("unreg", "Leave group of payments"),
            types.BotCommand("list", "List of group of payments members"),
            types.BotCommand("pay", "Add new payment"),
            types.BotCommand("delete", "Delete payment"),
            types.BotCommand("status", "Status of calculations"),
            types.BotCommand("stats", "Group of payments statistics"),
            types.BotCommand("history", "Payments history"),
            types.BotCommand("cancel", "Cancel"),
            types.BotCommand("end", "Finish and calculate all debts"),
            types.BotCommand("help", "Help"),
        ],
        scope=BotCommandScopeAllGroupChats()
    )


async def set_bot_commands(dp: Dispatcher):
    """
    Set command for bot personal chat with user
    :param dp: aiogram dispatcher for th bot
    """

    await dp.bot.set_my_commands(
        commands=[
            types.BotCommand("start", "Start bot"),
            types.BotCommand("help", "Help"),
            types.BotCommand("feedback", "Feedback")
        ]
    )
