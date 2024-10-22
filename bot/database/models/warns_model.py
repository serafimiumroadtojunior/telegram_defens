from typing import Annotated

from sqlalchemy import BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..session import Base

primary_key = Annotated[int, mapped_column(primary_key=True)]
warn_int = Annotated[int, mapped_column(Integer, default=0)]

class Warns(Base):
    __tablename__ = "users_moderations"
    __table_args__ = {"schema" : "warns_system"}

    id: Mapped[primary_key]
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    warns: Mapped[warn_int]