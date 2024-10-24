from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..session import Base


class AntiSpam(Base):
    __tablename__ = "message_control"
    __table_args__ = {"schema": "anti_spam"}

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.now())