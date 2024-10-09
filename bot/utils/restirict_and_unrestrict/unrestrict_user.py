from typing import List, Optional

from aiogram import Bot
from aiogram.types import CallbackQuery, Chat, InaccessibleMessage, Message

from ..helpers import answer_message, unban_user, unmute_user


async def handle_unmute_for_callback(
    bot: Bot, callback_query: CallbackQuery
) -> None:
    if callback_query.message is None or isinstance(callback_query.message, InaccessibleMessage):
        return

    await callback_query.message.delete()

    if callback_query.message.chat is None or callback_query.data is None:
        return

    data_parts: List[str] = callback_query.data.split("_")
    
    if len(data_parts) < 2:
        return
    
    user_id: int = int(data_parts[1])

    await unmute_user(
        bot=bot,
        chat_id=callback_query.message.chat.id,
        tg_id=user_id,
        permission=True,
    )

    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)

    if user_info is None or user_info.user is None:
        return
    
    await answer_message(
        bot=bot,
        chat_id=callback_query.message.chat.id,
        text=f"<a href='tg://user?id={user_info.user.id}'><b>👀{user_info.user.first_name}</b></a> has been unmuted.",
        delay=30,
    )


async def handle_unban_for_callback(
    bot: Bot, callback_query: CallbackQuery
) -> None:
    if callback_query.message is None or isinstance(callback_query.message, InaccessibleMessage):
        return

    await callback_query.message.delete()

    if callback_query.message.chat is None or callback_query.data is None:
        return

    data_parts: List[str] = callback_query.data.split("_")
    
    if len(data_parts) < 2:
        return
    
    user_id: int = int(data_parts[1])

    await unban_user(bot=bot, chat_id=callback_query.message.chat.id, tg_id=user_id)

    user_info = await bot.get_chat_member(callback_query.message.chat.id, user_id)

    if user_info is None or user_info.user is None:
        return
    
    await answer_message(
        bot=bot,
        chat_id=callback_query.message.chat.id,
        text=f"<a href='tg://user?id={user_info.user.id}'><b>👀{user_info.user.first_name}</b></a> has been unbanned.",
        delay=30,
    )


async def handle_unmute(bot: Bot, message: Message) -> None:
    chat: Optional[Chat] = message.chat
    reply: Optional[Message] = message.reply_to_message

    if reply is None or reply.from_user is None or chat is None:
        return

    await unmute_user(
        bot=bot, tg_id=reply.from_user.id, chat_id=chat.id, permission=True
    )

    await answer_message(
        bot=bot,
        chat_id=chat.id,
        text=f"<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been unmuted.",
        delay=30,
    )


async def handle_unban(bot: Bot, message: Message) -> None:
    chat: Optional[Chat] = message.chat
    reply: Optional[Message] = message.reply_to_message

    if reply is None or reply.from_user is None or chat is None:
        return

    await unban_user(bot=bot, tg_id=reply.from_user.id, chat_id=chat.id)

    await answer_message(
        bot=bot,
        chat_id=chat.id,
        text=f"<a href='tg://user?id={reply.from_user.id}'><b>{reply.from_user.first_name}</b></a> has been unbanned.",
        delay=30,
    )