from typing import Any, Callable, Dict, Awaitable, List
from datetime import timedelta, datetime
import asyncio

from aiogram.types import Message, ChatMember, CallbackQuery
from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from cachetools import TTLCache

from functions import mute_and_unmute, optional_keyboard, send_message_and_delete, send_unrestriction_message

class AdminCheckerMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    async def check_admin(self, chat_id: int, user_id: int) -> bool:
        member: ChatMember = await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['administrator', 'creator']

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        if not await self.check_admin(event.chat.id, user_id) and user_id != 5720349640:
            await send_message_and_delete(
                bot=self.bot,
                chat_id=event.chat.id,
                text="You do not have sufficient rights to perform this function.",
                delay=10,
                parse_mode='HTML'
            )
            return
        return await handler(event, data)

class CallbackAdminCheckerMiddleware(AdminCheckerMiddleware):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        if not await self.check_admin(event.message.chat.id, user_id) and user_id != 5720349640:
            await event.answer("You do not have sufficient rights to perform this function.", show_alert=True)
            return
        return await handler(event, data)

class ForbiddenWordsMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot, forbidden_words: List[str], response_message: str = "🔴 <a href='tg://user?id={user_id}'><b>{username}</b></a> was muted for 30 minutes for using offensive language."):
        self.bot: Bot = bot
        self.forbidden_words: List[str] = forbidden_words
        self.response_message: str = response_message
        self.until_date = datetime.now() + timedelta(minutes=30)
        super().__init__()

    async def mute_user(self, chat_id: int, user_id: int):
        await mute_and_unmute(bot=self.bot, chat_id=chat_id, tg_id=user_id, permission=False, until_date=self.until_date)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.text and any(word in event.text.lower() for word in self.forbidden_words):
            try:
                await self.mute_user(event.chat.id, event.from_user.id)

                await send_message_and_delete(
                    bot=self.bot,
                    chat_id=event.chat.id,
                    text=self.response_message.format(
                        username=event.from_user.first_name,
                        user_id=event.from_user.id
                    ),
                    delay=30,
                    parse_mode='HTML',
                    reply_markup=await optional_keyboard('Unmute✅', f'unmute_{event.from_user.id}')
                )
            except TelegramBadRequest:
                await send_message_and_delete(
                    bot=self.bot,
                    chat_id=event.chat.id,
                    text="🔴Error mute!",
                    delay=10,
                    parse_mode='HTML'
                )

            asyncio.create_task(send_unrestriction_message(self.bot, event.chat.id, event.from_user.id, self.until_date))

        return await handler(event, data)

    
class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, time_limit: int = 5) -> None:
        super().__init__()
        self.limit = TTLCache(maxsize=10_000, ttl=time_limit)

    async def __call__(self,
                     handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                     event: Message,
                     data: Dict[str, Any]
                     ) -> Any:
        
        if event.chat.id in self.limit:
            return
        else:
            self.limit[event.chat.id] = None
        return await handler(event, data)
