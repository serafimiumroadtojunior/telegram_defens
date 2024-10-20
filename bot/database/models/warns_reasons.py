from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from ..session import Base


class Reasons(Base):
    __tablename__ = "warns_reasons"
    __table_args__ = {"schema" : "warns_system"}

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    reasons: Mapped[int] = mapped_column(String(255))