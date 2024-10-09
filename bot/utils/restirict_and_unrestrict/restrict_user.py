import asyncio
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject
from aiogram.types import Chat, Message

from ..helpers import (answer_message, ban_user, mute_user,
                       parse_time_and_reason, send_unrestriction_message)


async def handle_mute(bot: Bot, message: Message, command: CommandObject) -> None:
    chat: Optional[Chat] = message.chat
    reply: Optional[Message] = message.reply_to_message

    if reply is None or reply.from_user is None or chat is None:
        return
    
    if command.args is None:
        await answer_message(
            bot=bot,
            chat_id=message.chat.id,
            text="🔴Error! Provide time and reason in the command."
        )
        return

    until_date, reason, readable_time = parse_time_and_reason(command.args)

    if until_date is None:
        await answer_message(
            bot=bot,
            chat_id=message.chat.id,
            text="🔴Error! Could not parse the time. Correct format: /mute 12h for spam"
        )
        return

    try:
        await mute_user(
            bot=bot,
            chat_id=chat.id,
            tg_id=reply.from_user.id,
            until_date=until_date
        )
    except TelegramBadRequest:
        await answer_message(
            bot=bot, 
            chat_id=chat.id, 
            text="<b>🔴Error mute!</b>"
        )
        return

    asyncio.create_task(
        send_unrestriction_message(bot, chat.id, reply.from_user.id, until_date)
    )

    if message.from_user:
        await answer_message(
            bot=bot,
            chat_id=chat.id,
            text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been muted for {readable_time} \nfor the reason: {reason}. \nAdmin: <a href='tg://user?id={message.from_user.id}'><b>{message.from_user.first_name}</b></a>",
            button_text="Unmute✅",
            callback_data=f"unmute_{reply.from_user.id}",
            delay=30
        )


async def handle_ban(bot: Bot, message: Message, command: CommandObject) -> None:
    chat: Optional[Chat] = message.chat
    reply: Optional[Message] = message.reply_to_message

    if reply is None or reply.from_user is None or chat is None:
        return
    
    if command.args is None:
        await answer_message(
            bot=bot,
            chat_id=message.chat.id,
            text="🔴Error! Provide time and reason in the command."
        )
        return

    until_date, reason, readable_time = parse_time_and_reason(command.args)

    if until_date is None:
        await answer_message(
            bot=bot,
            chat_id=message.chat.id,
            text="🔴Error! Could not parse the time. Correct format: /mute 12h for spam"
        )
        return

    try:
        await ban_user(
            bot=bot,
            chat_id=chat.id,
            tg_id=reply.from_user.id,
            until_date=until_date
        )
    except TelegramBadRequest:
        await answer_message(
            bot=bot, 
            chat_id=chat.id, 
            text="<b>🔴Error ban!</b>"
        )
        return

    asyncio.create_task(
        send_unrestriction_message(bot, chat.id, reply.from_user.id, until_date)
    )

    if message.from_user:
        await answer_message(
            bot=bot,
            chat_id=chat.id,
            text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been banned for {readable_time} \nfor the reason: {reason}. \nAdmin: <a href='tg://user?id={message.from_user.id}'><b>{message.from_user.first_name}</b></a>",
            button_text="Unban✅",
            callback_data=f"unban_{reply.from_user.id}",
            delay=30
        )