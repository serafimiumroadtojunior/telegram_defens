from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, TelegramObject
from spacy import load
from spacy.language import Language

from utils import (check_message_to_bad_words, check_message_to_https_links,
                   check_message_to_spam_words, mute_user)


class FilterWordsMiddleware(BaseMiddleware):
    def __init__(
        self,
        bot: Bot,
        file_path: Optional[str],
        mute_duration_minutes: int = 30,
        forbidden_message: str = "🔴<a href='tg://user?id={user_id}'><b>{username}</b></a> was muted for {duration} minutes for using offensive language.",
        https_message: str = "🔴Only HTTPS links are allowed, <b>{username}</b>."
    ):
        super().__init__()
        self.bot = bot
        self.forbidden_words_file = file_path
        self.forbidden_words: List[str] = self._load_forbidden_words()
        self.until_date: datetime = datetime.now() + timedelta(minutes=mute_duration_minutes)
        self.nlp: Language = load("ru_core_news_sm")
        self.forbidden_message = forbidden_message
        self.https_message = https_message

    def _load_forbidden_words(self) -> List[str]:
        if self.forbidden_words_file is None:
            raise ValueError("forbidden_words_file is None")
        with open(self.forbidden_words_file, "r", encoding="utf-8") as file:
            return [word.strip().lower() for word in file if word.strip()]

    async def mute(self, chat_id: int, user_id: int):
        await mute_user(
            bot=self.bot,
            chat_id=chat_id,
            tg_id=user_id,
            permission=False,
            until_date=self.until_date,
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.from_user and event.text and event.chat:
                await check_message_to_bad_words(bot=self.bot, 
                                                 message=event, 
                                                 nlp_model=self.nlp, 
                                                 forbidden_words=self.forbidden_words,
                                                 until_date=self.until_date,
                                                 forbidden_message=self.forbidden_message)
                
                await check_message_to_spam_words(bot=self.bot, 
                                                  message=event, 
                                                  nlp_model=self.nlp, 
                                                  count_spam_words=3,
                                                  mute_duration=30)

                
                await check_message_to_https_links(bot=self.bot,
                                                   message=event,
                                                   nlp_model=self.nlp,
                                                   https_message=self.https_message)
                

        return await handler(event, data)