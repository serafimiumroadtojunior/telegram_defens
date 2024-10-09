import asyncio
from collections import Counter
from datetime import datetime, timedelta
from typing import List

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from spacy.language import Language
from spacy.tokens import Doc

from ..helpers import answer_message, mute_user, send_unrestriction_message


async def check_message_to_https_links(
    bot: Bot,
    message: Message,
    nlp_model: Language,
    https_message: str
) -> None:
    if message.chat and message.from_user is None:
        return
    
    if message.text is None:
        return
    
    doc: Doc = nlp_model(message.text)  
    links: List[str] = [token.text for token in doc if token.like_url]

    for link in links:
        if not link.startswith("https://"):
            try:
                await message.delete()
            except TelegramBadRequest:
                await answer_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    text="🔴Error deleting message!"
                )
                return

            if message.from_user: 
                await answer_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    text=https_message.format(username=message.from_user.first_name),
                    delay=30
                )
            return  


async def check_message_to_bad_words(
    bot: Bot,
    message: Message,
    nlp_model: Language,
    forbidden_words: List[str],
    until_date: datetime,
    forbidden_message: str
) -> None:
    if not message.chat or not message.from_user:
        return

    if message.text is None:  
        return
    
    doc: Doc = nlp_model(message.text)  
    for token in doc:
        if token.text.lower() in forbidden_words:
            try:
                await mute_user(
                    bot=bot,
                    chat_id=message.chat.id,
                    tg_id=message.from_user.id,
                    until_date=until_date
                )

                await answer_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    text=forbidden_message.format(
                        user_id=message.from_user.id,
                        username=message.from_user.first_name,
                        duration=30
                    ),
                    button_text="Unmute✅",
                    callback_data=f"unmute_{message.from_user.id}",
                    delay=30
                )

            except TelegramBadRequest:
                await answer_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    text="🔴Error mute!"
                )

            asyncio.create_task(
                send_unrestriction_message(
                    bot, message.chat.id, message.from_user.id, until_date
                )
            )
            return  


async def check_message_to_spam_words(
    bot: Bot,
    message: Message,
    nlp_model: Language,
    count_spam_words: int,
    mute_duration: int
) -> None:
    if not message.chat or not message.from_user:
        return

    if message.text is None:  
        return
    
    doc: Doc = nlp_model(message.text)
    lemmas: List[str] = [token.lemma_ for token in doc]
    lemma_counts: Counter[str] = Counter(lemmas)

    for lemma, count in lemma_counts.items():
        if count >= count_spam_words:
            try:
                await message.delete()
                await mute_user(
                    bot=bot,
                    chat_id=message.chat.id,
                    tg_id=message.from_user.id,
                    until_date=datetime.now() + timedelta(minutes=mute_duration)
                )

                await answer_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    text=(f"<b>Spam detected! {message.from_user.first_name} has used the same word '{lemma}' more than {count_spam_words} times. Muted for {mute_duration} minutes.</b>"),
                    button_text="Unmute✅",
                    callback_data=f"unmute_{message.from_user.id}",
                    delay=30
                )

            except TelegramBadRequest:
                await answer_message(
                    bot=bot,
                    chat_id=message.chat.id,
                    text="<b>🔴Error muting user!</b>"
                )

            asyncio.create_task(
                send_unrestriction_message(
                    bot, message.chat.id, message.from_user.id, datetime.now() + timedelta(minutes=mute_duration)
                )
            )
            return 