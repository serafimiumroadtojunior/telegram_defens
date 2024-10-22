import asyncio
from contextlib import suppress
from datetime import datetime
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (ChatMember, ChatMemberMember, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)


async def send_unrestriction_message(
    bot: Bot, 
    chat_id: int,
    user_id: int, 
    new_datetime: Optional[datetime]
    ) -> None:
    if new_datetime is None:
        return
    
    wait_time: float = (new_datetime - datetime.now()).total_seconds() + 0.5

    if wait_time <= 0:
        await answer_message(
            bot=bot,
            chat_id=chat_id,
            text="🔴Error! Time less than zero"
        )
        return
    
    await asyncio.sleep(wait_time)

    chat_member: Optional[ChatMember] = await bot.get_chat_member(
        chat_id=chat_id, user_id=user_id
    )
    
    if chat_member is None:
        await answer_message(
            bot=bot,
            chat_id=chat_id,
            text="🔴Error! User not found"
        )  
        return
    
    if isinstance(chat_member, ChatMemberMember):
        await answer_message(
            bot=bot,
            chat_id=chat_id,
            text=f"<a href='tg://user?id={user_id}'><b>👀{chat_member.user.first_name}</b></a> has been unmuted",
            delay=30
        )
        return


async def answer_message(
    bot: Bot,
    chat_id: int,
    text: str,
    delay: int = 10,
    callback_data: Optional[str] = None,
    button_text: Optional[str] = None,
    parse_mode: str = "HTML"
    ) -> Message:
    response_message: Message = await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        reply_markup=await optional_keyboard(
            text=button_text,
            callback_data=callback_data
        )
    )
    
    asyncio.create_task(
        delayed_delete(
            message=response_message,
            delay=delay
        )
    )
    return response_message


async def optional_keyboard(
    text: Optional[str] = None,
    callback_data: Optional[str] = None
    ) -> Optional[InlineKeyboardMarkup]:
    if text and callback_data:
        keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text=text, callback_data=callback_data
            )]]
        )
        return keyboard
    return None


async def delayed_delete(
    delay: int, 
    message: Message
    ) -> None:
    with suppress(TelegramBadRequest, AttributeError):
        await asyncio.sleep(delay)
        await message.delete()