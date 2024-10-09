from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Chat, Message

from utils import answer_message

common_router: Router = Router()

@common_router.message(Command("help"))
async def help_for_admins(message: Message):
    chat: Optional[Chat] = message.chat
    
    if chat is None or message.bot is None:
        return


    message_admin: str = (
        "/mute - Restricts the user from sending messages\n"
        "/unmute - Allows the user to send messages again\n"
        "/ban - Bans the user (excludes from the group)\n"
        "/unban - Bans the user (excludes from the group)\n"
        "/warn - Gives the user a warning\n"
        "/message_id - Returns the ID of the last replied message\n"
        "/set_rules - Assigns rules"
    )

    await answer_message(
        bot=message.bot, 
        chat_id=chat.id, 
        text=message_admin,
        delay=30
    )
