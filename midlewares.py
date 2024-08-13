from typing import Any, Callable, Dict, Awaitable, List
from datetime import timedelta, datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ChatMember, CallbackQuery, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import BaseMiddleware, Bot
from cachetools import TTLCache

from admin_requests import check_user

class AdminCheckerMiddleware(BaseMiddleware):
    """
    Этот мидлварь проверяет, является ли пользователь администратором или создателем чата. 
    Если нет, то он получает отказ в выполнении команды.
    """
    def __init__(self, bot):
        self.bot = bot
        super().__init__()

    async def check_admin(self, chat_id, user_id):
        """
        Функция для проверки на админа
        """
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

class CallbackAdminCheckerMiddleware(AdminCheckerMiddleware):
    """
    Этот мидлварь проверяет является ли юзер админом и если все хорошо
    то мы разрешаем юзеру пользоваться каллбеками
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

class ForbiddenWordsMiddleware(BaseMiddleware):
    """
    Этот мидлварь проверяет наличие запрещенных слов в сообщении, мутит пользователя на 30 минут
    и отправляет предупреждение, если такие слова найдены.
    """
    def __init__(self, bot: Bot, forbidden_words: List[str], response_message: str = "🔴 <a href='tg://user?id={user_id}'><b>{username}</b></a> was muted for 30 minutes for using offensive language."):
        self.bot = bot
        self.forbidden_words = forbidden_words
        self.response_message = response_message
        super().__init__()

    async def mute_user(self, chat_id: int, user_id: int, duration: timedelta):
        until_date = datetime.now() + duration
        try:
            await self.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
        except TelegramBadRequest:
            await self.bot.send_message(chat_id, '<b>🔴Error muting user</b>', parse_mode='HTML')

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        
        if event.text and any(word in event.text.lower() for word in self.forbidden_words):
            await self.mute_user(event.chat.id, event.from_user.id, timedelta(minutes=30))

            button = InlineKeyboardButton(text='Unmute✅', callback_data=f'unmute_{event.from_user.id}')
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
            
            await event.reply(
                self.response_message.format(
                    username=event.from_user.first_name,
                    user_id=event.from_user.id
                ),
                parse_mode='HTML',
                reply_markup=keyboard
            )

        return await handler(event, data)

class AddUserToDataBase(BaseMiddleware):
    """
    Этот мидлварь добавляет пользователя в базу данных по сообщению
    """
    async def __call__(self,
                     handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                     event: Message,
                     data: Dict[str, Any]
                     ) -> Any:
        
        await check_user(event.from_user.id)
        return await handler(event, data)
    
class AntiFloodMiddleware(BaseMiddleware):
    """
    Этот мидлварь проверяет наличие превышения лимита отправленных сообщений в течении определенного времени
    и отправляет предупреждение, если такое происходит.
    """
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
