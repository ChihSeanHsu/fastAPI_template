from sqlalchemy import Column, Integer, DateTime, Index
from sqlalchemy.sql import func

from app.database import Base


class TimeSlot(Base):
    __tablename__ = "time_slot"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    start_at = Column(Integer, nullable=False)
    end_at = Column(Integer, nullable=False)

    __table_args__ = (
        Index("user_id__id", "user_id", "id"),
        Index("user_id__start_at__end_at", "user_id", "start_at", "end_at"),
    )
