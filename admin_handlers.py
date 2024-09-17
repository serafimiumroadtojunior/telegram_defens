import re

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from midlewares import WelcomeMiddleware
from functions import (handle_restriction, handle_unrestriction,
                       handle_unrestriction_for_callback, ban_user,
                       optional_keyboard, send_message_and_delete,
                       check_object)
from admin_requests import add_warn, reset_warns, check_warns, del_warn, add_user


admin_router = Router()


@admin_router.message(Command('mute'))
async def mute_handler(message: Message, command: CommandObject): 
    await handle_restriction(message.bot, message, command, "mute")

@admin_router.message(Command('ban'))
async def ban_handler(message: Message, command: CommandObject):
    await handle_restriction(message.bot, message, command, "ban")

@admin_router.callback_query(F.data.startswith('unmute_'))
async def unmute_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(callback_query.message.bot, callback_query, "unmute")

@admin_router.callback_query(F.data.startswith('unban_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    await handle_unrestriction_for_callback(callback_query.message.bot, callback_query, "unban")

@admin_router.callback_query(F.data.startswith('rewarn_'))
async def unban_callback_handler(callback_query: CallbackQuery):
    await callback_query.message.delete()

    bot = callback_query.message.bot
    user_id = int(callback_query.data.split('_')[1])

    await del_warn(user_id)

    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)
    await send_message_and_delete(
        bot=bot,
        chat_id=callback_query.message.chat.id,
        text=f"👀The <a href='tg://user?id={user_info.user.id}'><b>{user_info.user.first_name}</b></a> warn has been removed",
        delay=30,
        parse_mode='HTML'
    )

@admin_router.message(Command('unmute'))
async def unmute_handler(message: Message):
    await handle_unrestriction(message.bot, message, "unmute")

@admin_router.message(Command('unban'))
async def unban_handler(message: Message):
    await handle_unrestriction(message.bot, message, "unban")

@admin_router.message(Command("warn"))
async def warn_user(message: Message, command: CommandObject):
    reply = message.reply_to_message
    bot = message.bot

    await check_object(
        bot=bot,
        error_object=reply,
        chat_id=message.chat.id,
        text="🔴Error! Reply to a message to use this command.",
        delay=10
    )

    reason = command.args if command.args else "no reason provided"

    await add_user(reply.from_user.id)
    await add_warn(reply.from_user.id)
    warns = await check_warns(reply.from_user.id)

    if warns >= 3:
        await reset_warns(reply.from_user.id)
        try:
            await ban_user(bot=bot, tg_id=reply.from_user.id, chat_id=message.chat.id)

            await send_message_and_delete(
                bot=bot,
                chat_id=message.chat.id,
                text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been permanently banned for receiving 3 warnings.",
                delay=30,
                parse_mode="HTML",
                reply_markup=await optional_keyboard('Unban✅',  f'unban_{reply.from_user.id}')
            )

        except TelegramBadRequest:
            await send_message_and_delete(
                bot=bot,
                chat_id=message.chat.id,
                text="<b>🔴Error ban!</b>",
                delay=10,
                parse_mode='HTML'
            )
   
    else:
        await send_message_and_delete(
            bot=bot,
            chat_id=message.chat.id,
            text=f"👀<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has received a warning for: {reason}. \n<i>Current count: {warns}.</i>", 
            delay=30,
            parse_mode="HTML", 
            reply_markup=await optional_keyboard('Delete Warn✅',  f'rewarn_{reply.from_user.id}')
        )

@admin_router.message(Command("message_id"))
async def get_id(message: Message):
    reply = message.reply_to_message

    await check_object(
        bot=message.bot,
        error_object=reply,
        chat_id=message.chat.id,
        text="🔴Error! Reply to a message to use this command.",
        delay=10
    )
    
    replied_message_id = reply.message_id
    await message.reply(f"Message ID: {replied_message_id}")

@admin_router.message(Command('set_rules'))
async def help_handler(message: Message, command: CommandObject):
    bot = message.bot
    args = command.args.strip()

    await check_object(
        bot=bot,
        error_object=args,
        chat_id=message.chat.id,
        text="🔴Error! No arguments.",
        delay=10
    )

    if re.fullmatch(r'\d+', args):
        message_id = int(args)
        
        admin_router.message.outer_middleware(WelcomeMiddleware(bot, message_id))
        
        await send_message_and_delete(
            bot=bot,
            chat_id=message.chat.id,
            text="👀<b>Success!</b> Rules have been successfully added!",
        )
    else:
        await send_message_and_delete(
            bot=bot,
            chat_id=message.chat.id,
            text="🔴Error: Please provide a valid message ID containing only digits.",
            delay=10
        )
