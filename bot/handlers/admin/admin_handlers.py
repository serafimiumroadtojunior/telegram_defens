import re
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Chat, Message

from database import (add_rules_id, add_user, add_warn, check_warns,
                      delete_warn, reset_warns)
from utils import (answer_message, ban_user, handle_ban, handle_mute,
                   handle_unban, handle_unban_for_callback, handle_unmute,
                   handle_unmute_for_callback)

admin_router: Router = Router()

@admin_router.message(Command("mute"))
async def mute_handler(message: Message, command: CommandObject):
    bot: Optional[Bot] = message.bot
    if bot is None:
        return
    await handle_mute(bot=bot, message=message, command=command)

@admin_router.message(Command("ban"))
async def ban_handler(message: Message, command: CommandObject):
    bot: Optional[Bot] = message.bot
    if bot is None:
        return
    await handle_ban(bot=bot, message=message, command=command)

@admin_router.callback_query(F.data.startswith("unmute_"))
async def unmute_callback_handler(callback_query: CallbackQuery):
    bot: Optional[Bot] = callback_query.message.bot if callback_query.message else None
    if bot is None:
        return
    await handle_unmute_for_callback(bot=bot, callback_query=callback_query)

@admin_router.callback_query(F.data.startswith("unban_"))
async def unban_callback_handler(callback_query: CallbackQuery):
    bot: Optional[Bot] = callback_query.message.bot if callback_query.message else None
    if bot is None:
        return
    await handle_unban_for_callback(bot=bot, callback_query=callback_query)

@admin_router.callback_query(F.data.startswith("rewarn_"))
async def rewarn_callback_handler(callback_query: CallbackQuery):
    if isinstance(callback_query.message, Message) and callback_query.from_user:
        await callback_query.message.delete()

    chat: Optional[Chat] = callback_query.message.chat if callback_query.message else None
    bot: Optional[Bot] = callback_query.message.bot if callback_query.message else None

    if chat is None or bot is None:
        return

    user_id_str: Optional[str] = callback_query.data.split("_")[1] if callback_query.data else None

    if user_id_str is not None:
        user_id: int = int(user_id_str)
        await delete_warn(user_id)

        await answer_message(
            bot=bot,
            chat_id=chat.id,
            text=f"👀 The <a href='tg://user?id={callback_query.from_user.id}'><b>{callback_query.from_user.first_name}</b></a>'s warn has been removed",
            delay=30
        )

@admin_router.message(Command("unmute"))
async def unmute_handler(message: Message):
    bot: Optional[Bot] = message.bot
    if bot is None:
        return
    await handle_unmute(bot=bot, message=message)

@admin_router.message(Command("unban"))
async def unban_handler(message: Message):
    bot: Optional[Bot] = message.bot
    if bot is None:
        return
    await handle_unban(bot=bot, message=message)

@admin_router.message(Command("warn"))
async def warn_user(message: Message, command: CommandObject):
    chat: Optional[Chat] = message.chat
    reply: Optional[Message] = message.reply_to_message

    if reply is None or reply.from_user is None or chat is None:
        return
    
    bot: Optional[Bot] = message.bot
    if bot is None:
        return

    reason: str = command.args if command.args else "no reason provided"

    await add_user(reply.from_user.id)
    await add_warn(reply.from_user.id)
    warns: int = await check_warns(reply.from_user.id)

    if warns >= 3:
        await reset_warns(reply.from_user.id)
        try:
            await ban_user(bot=bot, tg_id=reply.from_user.id, chat_id=chat.id)

            await answer_message(
                bot=bot,
                chat_id=chat.id,
                text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been permanently banned for receiving 3 warnings.",
                delay=30,
                callback_data=f"unban_{reply.from_user.id}",
                button_text="Unban✅"
            )

        except TelegramBadRequest:
            await answer_message(
                bot=bot,
                chat_id=chat.id,
                text="<b>🔴Error ban!</b>",
                delay=10
            )

    else:
        await answer_message(
            bot=bot,
            chat_id=chat.id,
            text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has received a warning for: {reason}. \n<i>Current count: {warns}.</i>",
            delay=30,
            callback_data=f"rewarn_{reply.from_user.id}",
            button_text="Delete Warn✅"
        )

@admin_router.message(Command("set_rules"))
async def help_handler(message: Message, command: CommandObject):
    message_id: Optional[str] = command.args
    chat: Optional[Chat] = message.chat
    bot: Optional[Bot] = message.bot
    
    if chat is None or bot is None:
        return

    if not message_id or not re.fullmatch(r"\d+", message_id):
        await answer_message(
            bot=bot,
            chat_id=chat.id,
            text="🔴Error: Please provide a valid message ID containing only digits."
        )
        return

    message_id_int: int = int(message_id)
    await add_rules_id(chat_id=chat.id ,message_id=message_id_int)

    await answer_message(
        bot=bot,
        chat_id=chat.id,
        text="👀<b>Success!</b> Rules have been successfully added!",
        delay=30
    )