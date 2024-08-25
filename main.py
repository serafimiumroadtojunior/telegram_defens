import asyncio
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from midlewares import (AdminCheckerMiddleware, CallbackAdminCheckerMiddleware,
                        ForbiddenWordsMiddleware, AntiFloodMiddleware, WelcomeMiddleware)

from functions import (handle_restriction, handle_unrestriction,
                       handle_unrestriction_for_callback, ban_user,
                       optional_keyboard, send_message_and_delete)

from models import engine, Base
from admin_requests import add_warn, reset_warns, check_warns, del_warn, add_user
from other import forbidden_words

load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

@dp.message(Command('mute'))
async def mute_handler(message: Message, command: CommandObject): 
    await handle_restriction(bot, message, command, "mute")

@dp.message(Command('ban'))
async def ban_handler(message: Message, command: CommandObject):
    await handle_restriction(bot, message, command, "ban")

@dp.callback_query(F.data.startswith('unmute_'))
async def unmute_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(bot, callback_query, "unmute")

@dp.callback_query(F.data.startswith('unban_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(bot, callback_query, "unban")

@dp.callback_query(F.data.startswith('rewarn_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    await callback_query.message.delete()
    
    user_id = int(callback_query.data.split('_')[1])
    await del_warn(user_id)

    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)
    await send_message_and_delete(
        bot=callback_query.bot,
        chat_id=callback_query.message.chat.id,
        text=f"👀The <a href='tg://user?id={user_info.user.id}'><b>{user_info.user.first_name}</b></a> warn has been removed",
        delay=30,
        parse_mode='HTML'
    )

@dp.message(Command('unmute'))
async def unmute_handler(message: Message):
    await handle_unrestriction(bot, message, "unmute")

@dp.message(Command('unban'))
async def unban_handler(message: Message):
    await handle_unrestriction(bot, message, "unban")

@dp.message(Command("warn"))
async def warn_user(message: Message, command: CommandObject):
    reply = message.reply_to_message

    if not reply:
        await send_message_and_delete(
            bot=message.bot,
            chat_id=message.chat.id,
            text="🔴<b>This command must be used as a reply to a user's message.</b>",
            delay=10,
            parse_mode='HTML'
        )
        return

    reason = command.args if command.args else "no reason provided"

    await add_user(reply.from_user.id)
    await add_warn(reply.from_user.id)
    warns = await check_warns(reply.from_user.id)

    if warns >= 3:
        await reset_warns(reply.from_user.id)
        try:
            await ban_user(bot=message.bot, tg_id=reply.from_user.id, chat_id=message.chat.id)

            await send_message_and_delete(
                bot=message.bot,
                chat_id=message.chat.id,
                text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been permanently banned for receiving 3 warnings.",
                delay=30,
                parse_mode="HTML",
                reply_markup=await optional_keyboard('Unban✅',  f'unban_{reply.from_user.id}')
            )

        except TelegramBadRequest:
            await send_message_and_delete(
                bot=message.bot,
                chat_id=message.chat.id,
                text="<b>🔴Error ban!</b>",
                delay=10,
                parse_mode='HTML'
            )
   
    else:
        await send_message_and_delete(
            bot=message.bot,
            chat_id=message.chat.id,
            text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has received a warning for: {reason}. \n<i>Current count: {warns}.</i>", 
            delay=30,
            parse_mode="HTML", 
            reply_markup=await optional_keyboard('Delete Warn✅',  f'rewarn_{reply.from_user.id}')
        )

@dp.message(Command("message_id"))
async def get_id(message: Message):
    reply = message.reply_to_message
    if not reply:
        await send_message_and_delete(
            bot=message.bot,
            chat_id=message.chat.id,
            text="🔴<b>This command must be used as a reply to a user's message.</b>",
            delay=10,
            parse_mode='HTML'
        )
        return
    
    replied_message_id = reply.message_id
    await message.reply(f"Message ID: {replied_message_id}")

@dp.message(Command('set_rules'))
async def help_handler(message: Message, command: CommandObject):
    args = command.args.strip()

    if re.fullmatch(r'\d+', args):
        message_id = int(args)
        
        dp.message.outer_middleware(WelcomeMiddleware(bot, message_id))
        
        await send_message_and_delete(
            bot=message.bot,
            chat_id=message.chat.id,
            text="👀<b>Success!</b> Rules have been successfully added!",
        )
    else:
        await send_message_and_delete(
            bot=message.bot,
            chat_id=message.chat.id,
            text="🔴Error: Please provide a valid message ID containing only digits.",
            delay=10
        )


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    dp.message.middleware(AdminCheckerMiddleware(bot))
    dp.callback_query.middleware(CallbackAdminCheckerMiddleware(bot))
    dp.message.outer_middleware(ForbiddenWordsMiddleware(bot, forbidden_words))
    dp.message.middleware(AntiFloodMiddleware())

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot stopped')
