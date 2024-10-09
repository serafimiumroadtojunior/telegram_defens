import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (ChatMember, ChatMemberAdministrator,
                           ChatMemberOwner, ChatPermissions)


def parse_time_and_reason(args: str) -> Union[Tuple[datetime, str, str], Tuple[None, None, None]]:
    if not args:
        return None, None, None
    
    match: Optional[re.Match] = re.match(r"(\d+\s*[mhdw])\s*(.*)", args.lower().strip())
    if not match:
        return None, None, None

    time_string: str = match.group(1).strip()
    reason: str = match.group(2).strip()

    match = re.match(r"(\d+)\s*([mhdw])", time_string)
    if not match:
        return None, None, None

    value, unit = int(match.group(1)), match.group(2)
    current_datetime = datetime.now()

    if unit == "m":
        time_delta: timedelta = timedelta(minutes=value)
        readable_time: str = f"{value} minute{'s' if value > 1 else ''}"
    elif unit == "h":
        time_delta = timedelta(hours=value)
        readable_time = f"{value} hour{'s' if value > 1 else ''}"
    elif unit == "d":
        time_delta = timedelta(days=value)
        readable_time = f"{value} day{'s' if value > 1 else ''}"
    elif unit == "w":
        time_delta = timedelta(weeks=value)
        readable_time = f"{value} week{'s' if value > 1 else ''}"
    else:
        return None, None, None

    until_date: datetime = current_datetime + time_delta
    if not reason:
        reason = "no reason provided"
    return until_date, reason, readable_time


async def mute_user(
    bot: Bot, until_date: datetime, tg_id: int, chat_id: int, permission: bool = False
) -> None:
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=tg_id,
        permissions=ChatPermissions(
            can_send_messages=permission,
            can_send_documents=permission,
            can_send_photos=permission,
            can_send_videos=permission,
        ),
        until_date=until_date,
    )

async def unmute_user(
    bot: Bot, chat_id: int, tg_id: int, permission: bool = True
) -> None:
    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=tg_id,
        permissions=ChatPermissions(
            can_send_messages=permission,
            can_send_documents=permission,
            can_send_photos=permission,
            can_send_videos=permission,
        )
    )

async def ban_user(
    bot: Bot, chat_id: int, tg_id: int, until_date: Optional[datetime] = None
) -> None:
    await bot.ban_chat_member(chat_id=chat_id, user_id=tg_id, until_date=until_date)


async def unban_user(bot: Bot, chat_id: int, tg_id: int) -> None:
    await bot.unban_chat_member(
        chat_id=chat_id,
        user_id=tg_id,
    )

async def check_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member: Optional[ChatMember] = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member is None:
            return False
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)) 
    except TelegramBadRequest:
        return False