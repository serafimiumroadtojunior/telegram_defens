from typing import Any, Callable, Dict, Awaitable, List
from datetime import timedelta, datetime
import re
import asyncio

from aiogram.types import Message, ChatMember, CallbackQuery, ChatMemberUpdated
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
        if not await self.check_admin(event.chat.id, user_id ):
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
        if not await self.check_admin(event.message.chat.id, user_id):
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

    def create_pattern(self) -> str:
        escaped_words = [re.escape(word) for word in self.forbidden_words]
        pattern = r'\b(?:' + '|'.join(escaped_words) + r')\b'
        return pattern

    async def mute_user(self, chat_id: int, user_id: int):
        await mute_and_unmute(bot=self.bot, chat_id=chat_id, tg_id=user_id, permission=False, until_date=self.until_date)

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        pattern = self.create_pattern()
        if event.text and re.search(pattern, event.text, re.IGNORECASE):
            try:
                await self.mute_user(event.chat.id, event.from_user.id)

                await send_message_and_delete(
                    bot=self.bot,
                    chat_id=event.chat.id,
                    text=self.response_message.format(
                        username=event.from_user.first_name,
                        user_id=event.from_user.id
                    ),
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
    
class WelcomeMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot, rules_message_id: int):
        self.bot = bot
        self.rules_message_id = rules_message_id

    async def __call__(self,
                       handler: Callable[[ChatMemberUpdated, Dict[str, Any]], Awaitable[Any]],
                       event: ChatMemberUpdated,
                       data: Dict[str, Any]
                       ) -> Any:
        if not self.rules_message_id:
            return await handler(event, data)

        chat_name= event.chat.username
        chat_id = event.chat.id
        new_chat_members = event.new_chat_members

        if new_chat_members:
            for new_member in new_chat_members:
                user_name = new_member.first_name

                rules_url = f"https://t.me/{chat_name}/{self.rules_message_id}"
                text = (
                    f"👀<b>Welcome {user_name}!</b>\nBefore writing in the chat, we recommend that you read the <a href='{rules_url}'><b>rules</b></a>."
                )

                await send_message_and_delete(
                    bot=self.bot,
                    chat_id=chat_id,
                    text=text
                )

        return await handler(event, data)
