from typing import Any, Callable, Dict, Awaitable, List
from datetime import timedelta, datetime

from aiogram.types import Message, ChatMember, CallbackQuery, ChatPermissions
from aiogram import BaseMiddleware
from cachetools import TTLCache

class AdminCheckerMiddleware(BaseMiddleware):
    """
    Этот мидлварь проверяет, является ли пользователь администратором или создателем чата. 
    Если нет, то он получает отказ в выполнении команды.
    """
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def check_admin(self, chat_id, user_id):
        member: ChatMember = await self.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['administrator', 'creator']

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not await self.check_admin(event.chat.id, event.from_user.id):
            await event.answer("You do not have sufficient rights to perform this function.")
            return
        return await handler(event, data)


class ForbiddenWordsMiddleware(BaseMiddleware):
    """
    Этот мидлварь проверяет наличие запрещенных слов в сообщении, мутит пользователя на 30 минут
    и отправляет предупреждение, если такие слова найдены.
    """
    def __init__(self, bot, forbidden_words: List[str], response_message: str = "🔴 <b>{username}</b> was muted for 30 minutes for using offensive language."):
        self.bot = bot
        self.forbidden_words = forbidden_words
        self.response_message = response_message
        super().__init__()

    async def mute_user(self, chat_id, user_id, duration: timedelta):
        until_date = datetime.utcnow() + duration
        await self.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.text and any(word in event.text.lower() for word in self.forbidden_words):
            await self.mute_user(event.chat.id, event.from_user.id, timedelta(minutes=30))
            await event.reply(self.response_message.format(username=event.from_user.first_name), parse_mode='HTML')
        return await handler(event, data)


class CallbackAdminCheckerMiddleware(AdminCheckerMiddleware):
    """
    This middleware checks if the user is an admin or the chat creator for callback queries.
    If not, they are denied execution of the command.
    """
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if not await self.check_admin(event.message.chat.id, event.from_user.id):
            await event.answer("You do not have sufficient rights to perform this function.", show_alert=True)
            return
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