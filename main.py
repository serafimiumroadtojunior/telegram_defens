import asyncio
import re
from datetime import timedelta, datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from api import TOKEN
from midlewares import AdminCheckerMiddleware, CallbackAdminCheckerMiddleware, ForbiddenWordsMiddleware, AntiFloodMiddleware
from models import async_main
from admin_requests import add_warn, reset_warns, check_warns, check_user
from other import forbidden_words

bot = Bot(token=TOKEN)
dp = Dispatcher()

def parse_time_and_reason(args: str) -> tuple[datetime, str, str]:
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
    current_datetime = datetime.utcnow()

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

    new_datetime = current_datetime + time_delta
    if not reason:
        reason = "no reason provided"
    return new_datetime, reason, readable_time

@dp.message(Command("warn"))
async def warn_user(message: Message, command: CommandObject):
    reply = message.reply_to_message

    if not reply:
        await message.answer("This command must be used as a reply to a user's message.", parse_mode='HTML')
        return

    # Parse the reason from the command arguments
    reason = command.args if command.args else "no reason provided"

    # Check and create user if not exists
    await check_user(reply.from_user.id)

    await add_warn(reply.from_user.id)
    warns = await check_warns(reply.from_user.id)
    if warns >= 3:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=reply.from_user.id
        )
        await message.answer(f"👀<b>{reply.from_user.first_name}</b> has been permanently banned for receiving 3 warnings.", parse_mode="HTML")
        await reset_warns(reply.from_user.id)
    else:
        await message.answer(f"👀<b>{reply.from_user.first_name}</b> has received a warning for: {reason}. Current count: {warns}.", parse_mode="HTML")

async def handle_unrestriction_for_callback(callback_query: CallbackQuery, action: str):
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
    await callback_query.answer(f"User has been {action_past}.")
    await callback_query.message.answer(f"<b>👀{user_info.user.first_name}</b> has been {action_past}.", parse_mode='HTML')

async def handle_unrestriction(message: Message, action: str):
    """
    Generic function to handle unmute and unban actions
    """
    reply = message.reply_to_message
    if not reply:
        await message.answer("Error! Reply to a message to use this command</i>.", parse_mode='HTML')
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
    await message.answer(f"<b>{reply.from_user.first_name}</b> has been {action_past}.", parse_mode='HTML')

@dp.message(Command('unmute'))
async def unmute_handler(message: Message):
    """
    Function to unmute a user
    """
    await handle_unrestriction(message, "unmute")

@dp.message(Command('unban'))
async def unban_handler(message: Message):
    """
    Function to unban a user
    """
    await handle_unrestriction(message, "unban")

async def handle_restriction(message: Message, command: CommandObject, action: str):
    """
    Generic function to handle mute and ban actions
    """
    reply = message.reply_to_message
    if not reply:
        await message.answer("🔴Error! Reply to a message to use this command.", parse_mode='HTML')
        return

    until_date, reason, readable_time = parse_time_and_reason(command.args)
    if not until_date:
        await message.answer("🔴Error! Could not parse the time. Correct format: /mute 12h for spam", parse_mode='HTML')
        return

    if action == "mute":
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=reply.from_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
    elif action == "ban":
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

    await message.answer(f"👀<b>{reply.from_user.first_name}</b> has been {action_past} for {readable_time} for the reason: {reason}.", parse_mode="HTML", reply_markup=keyboard)

@dp.message(Command('mute'))
async def mute_handler(message: Message, command: CommandObject):
    """
    Function to mute a user
    """
    await handle_restriction(message, command, "mute")

@dp.message(Command('ban'))
async def ban_handler(message: Message, command: CommandObject):
    """
    Function to ban a user
    """
    await handle_restriction(message, command, "ban")

@dp.callback_query(F.data.startswith('unmute_'))
async def unmute_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(callback_query, "unmute")

@dp.callback_query(F.data.startswith('unban_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(callback_query, "unban")

async def main():
    dp.message.middleware(AdminCheckerMiddleware(bot))
    dp.callback_query.middleware(CallbackAdminCheckerMiddleware(bot))
    dp.message.outer_middleware(ForbiddenWordsMiddleware(bot, forbidden_words))
    dp.message.middleware(AntiFloodMiddleware())

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(async_main())
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')