import asyncio
import re
from datetime import datetime, timedelta
from contextlib import suppress
from typing import Any

from aiogram import Bot
from aiogram.filters import CommandObject
from aiogram.types import (Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton,
                            CallbackQuery, ChatMemberMember, ChatMember)
from aiogram.exceptions import TelegramBadRequest

def parse_time_and_reason(args):
    if not args:
        return None, None, None

    match = re.match(r"(\d+\s*[mhdw])\s*(.*)", args.lower().strip())
    if not match:
        return None, None, None

    time_string, reason = match.group(1).strip(), match.group(2).strip()
    match = re.match(r"(\d+)\s*([mhdw])", time_string)
    if not match:
        return None, None, None

    value, unit = int(match.group(1)), match.group(2)
    current_datetime = datetime.now()

    if unit == "m":
        time_delta = timedelta(minutes=value)
        readable_time = f"{value} minute{'s' if value > 1 else ''}"
    elif unit == "h":
        time_delta = timedelta(hours=value)
        readable_time = f"{value} hour{'s' if value > 1 else ''}"
    elif unit == "d":
        time_delta = timedelta(days=value)
        readable_time = f"{value} day{'s' if value > 1 else ''}"
    elif unit == "w":
        time_delta = timedelta(weeks=value)
        readable_time = f"{value} week{'s' if value > 1 else ''}"
    else:
        return None, None, None

    until_date = current_datetime + time_delta
    if not reason:
        reason = "no reason provided"
    return until_date, reason, readable_time

async def handle_unrestriction_for_callback(bot: Bot, callback_query: CallbackQuery, action: str):
    await callback_query.message.delete()
    
    user_id = int(callback_query.data.split('_')[1])

    if action == "unmute":
        await mute_and_unmute(bot=bot, chat_id=callback_query.message.chat.id, tg_id=user_id, permission=True)

    elif action == "unban":
        await unban_user(bot=bot, chat_id=callback_query.message.chat.id, tg_id=user_id)

    action_past = "unmuted" if action == "unmute" else "unbanned"
    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)
    await send_message_and_delete(
        bot=bot,
        chat_id=callback_query.message.chat.id,
        text=f"<a href='tg://user?id={user_info.user.id}'><b>👀{user_info.user.first_name}</b></a> has been {action_past}.",
        delay=30
    )

async def handle_unrestriction(bot: Bot, message: Message, action: str):
    reply = message.reply_to_message

    await check_object(
        bot=bot,
        error_object=reply,
        chat_id=message.chat.id,
        text="🔴Error! Reply to a message to use this command.",
        delay=10
    )

    if action == "unmute":
        await mute_and_unmute(bot=bot, chat_id=message.chat.id, tg_id=reply.from_user.id, permission=True)

    elif action == "unban":
        await unban_user(bot=bot, chat_id=message.chat.id, tg_id=reply.from_user.id)

    action_past = "unmuted" if action == "unmute" else "unbanned"
    await send_message_and_delete(
        bot=bot,
        chat_id=message.chat.id,
        text=f"<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been {action_past}.",
        delay=30
    )

async def handle_restriction(bot: Bot, message: Message, command: CommandObject, action: str):
    reply = message.reply_to_message

    await check_object(
        bot=bot,
        error_object=reply,
        chat_id=message.chat.id,
        text="🔴Error! Reply to a message to use this command.",
        delay=10
        )

    until_date, reason, readable_time = parse_time_and_reason(command.args)

    await check_object(
        bot=bot,
        error_object=until_date,
        chat_id=message.chat.id,
        text="🔴Error! Could not parse the time. Correct format: /mute 12h for spam",
        delay=10
    )

    try:
        if action == "mute":
            await mute_and_unmute(bot=bot, chat_id=message.chat.id, tg_id=reply.from_user.id, permission=False, until_date=until_date)

        elif action == "ban":
            await ban_user(bot=bot, chat_id=message.chat.id, tg_id=reply.from_user.id, until_date=until_date)

    except TelegramBadRequest:
        await send_message_and_delete(
            bot=bot,
            chat_id=message.chat.id,
            text=f"<b>🔴Error {action}!</b>",
            delay=10
        )
        return

    action_past = "muted" if action == "mute" else "banned"
    button_text = "Unmute✅" if action == "mute" else "Unban✅"
    callback_data = f'unmute_{reply.from_user.id}' if action == "mute" else f'unban_{reply.from_user.id}'
    
    asyncio.create_task(send_unrestriction_message(bot, message.chat.id, reply.from_user.id, until_date))

    await send_message_and_delete(
        bot=bot,
        chat_id=message.chat.id,
        text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been {action_past} for {readable_time} \nfor the reason: {reason}. \nAdmin: <a href='tg://user?id={message.from_user.id}'><b>{message.from_user.first_name}</b></a>",
        reply_markup=await optional_keyboard(button_text, callback_data),
        delay=30
    )

async def send_unrestriction_message(bot: Bot, chat_id: int, user_id: int, new_datetime: datetime):
    wait_time = (new_datetime - datetime.now()).total_seconds()
    
    if wait_time <= 0:
        return

    await asyncio.sleep(wait_time)

    chat_member: ChatMember = await bot.get_chat_member(chat_id, user_id)

    if isinstance(chat_member, ChatMemberMember):
        await send_message_and_delete(
            bot=bot,
            chat_id=chat_id,
            text=f"<a href='tg://user?id={user_id}'><b>👀{chat_member.user.first_name}</b></a> has been unmuted",
            delay=30
        )
    else:
        print(f"User with ID {user_id} is not a member of the chat or could not retrieve member info.") 

async def mute_and_unmute(bot: Bot, chat_id: int, tg_id: int, permission: bool, until_date=None):
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=tg_id,
            permissions=ChatPermissions(
                can_send_messages=permission,
                can_send_documents=permission,
                can_send_photos=permission,
                can_send_videos=permission,
                ),
            until_date=until_date
        )

async def ban_user(bot: Bot, chat_id: int, tg_id: int, until_date: datetime | None = None):
    await bot.ban_chat_member(
        chat_id=chat_id,
        user_id=tg_id,
        until_date=until_date
    )


async def unban_user(bot: Bot, chat_id: int, tg_id: int):
    await bot.unban_chat_member(
        chat_id=chat_id,
        user_id=tg_id,
    )


async def delayed_delete(delay: int, message: Message):
    with suppress(TelegramBadRequest, AttributeError):
        await asyncio.sleep(delay)
        await message.delete()


async def optional_keyboard(text, callback_data):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback_data)]])
    return keyboard

async def send_message_and_delete(bot: Bot, chat_id: int, text: str, parse_mode: str = 'HTML', delay: int = 30, reply_markup=None):
    sent_message = await bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)
    await delayed_delete(delay, sent_message)
    return sent_message

async def check_object(bot: Bot, error_object: Any, chat_id: int, text: str, delay: int = 10):
    object = error_object
    if not object:
        await send_message_and_delete(
            bot=bot,
            chat_id=chat_id,
            text=text,
            delay=delay
        )
        return
