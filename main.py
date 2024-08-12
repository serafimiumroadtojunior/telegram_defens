import asyncio
import os
import re
from datetime import timedelta, datetime
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from midlewares import (AdminCheckerMiddleware, CallbackAdminCheckerMiddleware,
                         ForbiddenWordsMiddleware, AntiFloodMiddleware,
                         AddUserToDataBase)
from models import engine, Base
from admin_requests import add_warn, reset_warns, check_warns, del_warn
from other import forbidden_words

load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

def parse_time_and_reason(args):
    """
    Функция для парсинга времени и причины
    :param args: Строка с указанием времени и причины
    :return: Время до которого разрешено повторно использовать бота, причина и читабельное представление времени
    """
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

async def handle_unrestriction_for_callback(callback_query: CallbackQuery, action: str):
    """
    Функция для разбана и размута по Callback
    :param callback_query: Объект CallbackQuery
    :param action: Тип действия (размутить/разбанить)
    """
    user_id = int(callback_query.data.split('_')[1])

    if action == "unmute":
        await bot.restrict_chat_member(
            chat_id=callback_query.message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=True)
        )

    elif action == "unban":
        await bot.unban_chat_member(
            chat_id=callback_query.message.chat.id,
            user_id=user_id
        )

    await callback_query.message.delete()
    action_past = "unmuted" if action == "unmute" else "unbanned"
    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)
    sent_message = await callback_query.message.answer(
        f"<a href='tg://user?id={user_info.user.id}'><b>👀{user_info.user.first_name}</b></a> has been {action_past}.", 
        parse_mode='HTML'
    )
    await asyncio.sleep(30)
    await sent_message.delete()

async def handle_unrestriction(message: Message, action: str):
    """
    Функция для разбана и размута по сообщению
    :param message: Объект Message
    :param action: Тип действия (размутить/разбанить)
    """
    reply = message.reply_to_message
    if not reply:
        sent_message = await message.answer("Error! Reply to a message to use this command.", parse_mode='HTML')
        await asyncio.sleep(15)
        await sent_message.delete()
        return

    if action == "unmute":
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=reply.from_user.id,
            permissions=ChatPermissions(can_send_messages=True)
        )

    elif action == "unban":
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=reply.from_user.id
        )

    action_past = "unmuted" if action == "unmute" else "unbanned"
    sent_message = await message.answer(
        f"<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been {action_past}.",
        parse_mode='HTML'
    )
    await asyncio.sleep(30)
    await sent_message.delete()

async def handle_restriction(message: Message, command: CommandObject, action: str):
    """
    Функция для бана и мута по сообщению
    :param message: Объект Message
    :param command: Объект CommandObject
    :param action: Тип действия (банить/мутить)
    """
    reply = message.reply_to_message
    if not reply:
        sent_message = await message.answer("🔴Error! Reply to a message to use this command.", parse_mode='HTML')
        await asyncio.sleep(30)
        await sent_message.delete()
        return

    until_date, reason, readable_time = parse_time_and_reason(command.args)
    if not until_date:
        sent_message = await message.answer("🔴Error! Could not parse the time. Correct format: /mute 12h for spam", parse_mode='HTML')
        await asyncio.sleep(30)
        await sent_message.delete()
        return

    if action == "mute":
        with suppress(TelegramBadRequest):
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=reply.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
    
    elif action == "ban":
        with suppress(TelegramBadRequest):
            await bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=reply.from_user.id,
                until_date=until_date
            )

    action_past = "muted" if action == "mute" else "banned"
    button_text = "Unmute✅" if action == "mute" else "Unban✅"
    callback_data = f'unmute_{reply.from_user.id}' if action == "mute" else f'unban_{reply.from_user.id}'
    
    button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    sent_message = await message.answer(
        f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been {action_past} for {readable_time} \nfor the reason: {reason}. \nAdmin: <a href='tg://user?id={message.from_user.id}'><b>{message.from_user.first_name}</b></a>", 
        parse_mode="HTML", 
        reply_markup=keyboard
    )
    await asyncio.sleep(30)
    await sent_message.delete()

    asyncio.create_task(send_unrestriction_message(message.chat.id, reply.from_user.id, action_past, until_date))

async def send_unrestriction_message(chat_id, user_id, action_past, new_datetime):
    """
    Функция для отправки сообщения об успешном разбане или размуте
    :param chat_id: ID чата
    :param user_id: ID пользователя
    :param action_past: Текстовое представление действия (размутен/разбанен)
    """
    wait_time = (new_datetime - datetime.now()).total_seconds()
    await asyncio.sleep(wait_time)

    chat_member = await bot.get_chat_member(chat_id, user_id)

    if chat_member.until_date and chat_member.until_date.timestamp() < new_datetime.timestamp():
        return None

    if not chat_member.can_send_messages:
        unrestriction_message = f"<a href='tg://user?id={user_id}'><b>👀{chat_member.user.first_name}</b></a> has been {'unmuted' if action_past == 'muted' else 'unbanned'}."
        sent_message = await bot.send_message(chat_id, unrestriction_message, parse_mode='HTML')
        await asyncio.sleep(30)
        await sent_message.delete()

@dp.message(Command('mute'))
async def mute_handler(message: Message, command: CommandObject):
    await handle_restriction(message, command, "mute")

@dp.message(Command('ban'))
async def ban_handler(message: Message, command: CommandObject):
    await handle_restriction(message, command, "ban")

@dp.callback_query(F.data.startswith('unmute_'))
async def unmute_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(callback_query, "unmute")

@dp.callback_query(F.data.startswith('unban_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(callback_query, "unban")

@dp.callback_query(F.data.startswith('rewarn_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    user_id = int(callback_query.data.split('_')[1])
    await del_warn(user_id)

    await callback_query.message.delete()

    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)
    sent_message = await callback_query.message.answer(f"👀The <a href='tg://user?id={user_info.user.id}'><b>{user_info.user.first_name}</b></a> warn has been removed", parse_mode='HTML')
    await asyncio.sleep(30)
    await sent_message.delete()

@dp.message(Command('unmute'))
async def unmute_handler(message: Message):
    await handle_unrestriction(message, "unmute")

@dp.message(Command('unban'))
async def unban_handler(message: Message):
    await handle_unrestriction(message, "unban")

@dp.message(Command("warn"))
async def warn_user(message: Message, command: CommandObject):
    """
    Функция для выдачи варна
    :param message: Объект Message
    :param command: Объект CommandObject
    """
    reply = message.reply_to_message

    if not reply:
        sent_message = await message.answer("This command must be used as a reply to a user's message.", parse_mode='HTML')
        await asyncio.sleep(30)
        await sent_message.delete()
        return

    reason = command.args if command.args else "no reason provided"

    await add_warn(reply.from_user.id)
    warns = await check_warns(reply.from_user.id)

    button = InlineKeyboardButton(text='Delete Warn✅', callback_data=f'rewarn_{reply.from_user.id}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    button2 = InlineKeyboardButton(text='Unban✅', callback_data=f'unban_{reply.from_user.id}')
    keyboard2 = InlineKeyboardMarkup(inline_keyboard=[[button2]])

    if warns >= 3:
        with suppress(TelegramBadRequest):
            await bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=reply.from_user.id
            )

            sent_message = await message.answer(
                f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been permanently banned for receiving 3 warnings.",
                reply_markup=keyboard2,
                parse_mode="HTML"
            )
            await reset_warns(reply.from_user.id)
            await asyncio.sleep(30)
            await sent_message.delete()
        
    else:
        sent_message = await message.answer(
            f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> \nhas received a warning for: {reason}. \n<i>Current count: {warns}.</i>", 
            parse_mode="HTML", 
            reply_markup=keyboard
        )
        await asyncio.sleep(30)
        await sent_message.delete()

async def main():
    """
    Главная функция, запускающая бота
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    dp.message.middleware(AdminCheckerMiddleware(bot))
    dp.callback_query.middleware(CallbackAdminCheckerMiddleware(bot))
    dp.message.outer_middleware(ForbiddenWordsMiddleware(bot, forbidden_words))
    dp.message.middleware(AntiFloodMiddleware())
    dp.message.outer_middleware(AddUserToDataBase())

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')
