import asyncio
import os
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv

from midlewares import (AdminCheckerMiddleware, CallbackAdminCheckerMiddleware,
                        ForbiddenWordsMiddleware, AntiFloodMiddleware,
                        AddUserToDataBase)
from functions import (handle_restriction, handle_unrestriction,
                       handle_unrestriction_for_callback)
from models import engine, Base
from admin_requests import add_warn, reset_warns, check_warns, del_warn
from other import forbidden_words

load_dotenv()

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

@dp.message(Command('mute'))
async def mute_handler(message: Message, command: CommandObject): 
    """
    Эта функция мутит юзера в чате
    :param message: Объект Message
    :param command: Объект CommandObject
    """   
    await handle_restriction(bot, message, command, "mute")

@dp.message(Command('ban'))
async def ban_handler(message: Message, command: CommandObject):
    """
    Эта функция банит юзера в чате
    :param message: Объект Message
    :param command: Объект CommandObject
    """
    await handle_restriction(bot, message, command, "ban")

@dp.callback_query(F.data.startswith('unmute_'))
async def unmute_callback_handler(callback_query: CallbackQuery):
    """
    Отлавливает специальный каллбек по которому понимает что надо размутить юзера
    :param callback_query: Объект CallbackQuery
    """
    await handle_unrestriction_for_callback(bot, callback_query, "unmute")

@dp.callback_query(F.data.startswith('unban_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    """
    Отлавливает специальный каллбек по которому понимает что надо разбанить юзера
    :param callback_query: Объект CallbackQuery
    """
    await handle_unrestriction_for_callback(bot, callback_query, "unban")

@dp.callback_query(F.data.startswith('rewarn_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    """
    Отлавливает специальный каллбек по которому понимает что надо удалить варн юзера
    :param callback_query: Объект CallbackQuery
    """
    user_id = int(callback_query.data.split('_')[1])
    await del_warn(user_id)

    await callback_query.message.delete()

    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)
    sent_message = await callback_query.message.answer(f"👀The <a href='tg://user?id={user_info.user.id}'><b>{user_info.user.first_name}</b></a> warn has been removed", parse_mode='HTML')
    await asyncio.sleep(30)
    await sent_message.delete()

@dp.message(Command('unmute'))
async def unmute_handler(message: Message):
    """
    Эта функция размутит юзера в чате
    :param message: Объект Message
    """
    await handle_unrestriction(bot, message, "unmute")

@dp.message(Command('unban'))
async def unban_handler(message: Message):
    """
    Эта функция разбанит юзера в чате
    :param message: Объект Message
    """
    await handle_unrestriction(bot, message, "unban")

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
