from datetime import datetime

from psycopg2.extras import NumericRange
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

from app import models, schemas, errors
from .base import BaseController


class TimeSlotController(BaseController):

    def _check_basic(self, time_slot: schemas.TimeSlotCreate, now: int):
        if time_slot.start_at >= time_slot.end_at:
            raise errors.TimeFormatError("start_at must less than end_at")
        if time_slot.start_at <= now:
            raise errors.TimeFormatError("start_at must greater than now")
        if (time_slot.end_at - time_slot.start_at) > 86400:
            raise errors.TimeFormatError("range start_at and end_at must in 24 hours")

    def _check_overlap(self, sess: Session, time_slot: schemas.TimeSlotCreate):
        query = sess.execute(
            """
            SELECT * 
            FROM time_slot 
            WHERE user_id=:user_id AND int8range(start_at, end_at) && int8range(:start_at, :end_at) 
            """,
            {"user_id": time_slot.user_id, "start_at": time_slot.start_at, "end_at": time_slot.end_at}
        )
        c = sess.execute(
            """
            EXPLAIN
            SELECT * 
            FROM time_slot 
            WHERE user_id=:user_id AND int8range(start_at, end_at) && int8range(:start_at, :end_at) 
            """,
             {"user_id": time_slot.user_id, "start_at": time_slot.start_at, "end_at": time_slot.end_at}
        )

        print(c.first())
        a = query.first()
        print(a)
        if a:
            raise errors.TimeOverlapError

    def get(self, user_id: int, **kwargs):
        pass

    def list(self, user_id: int, before_timestamp: int = None, after_timestamp: int = None):
        with self.db() as sess:
            query = sess.query(models.TimeSlot).filter_by(user_id=user_id).order_by(models.TimeSlot.start_at)
            if before_timestamp:
                query = query.filter(models.TimeSlot.end_at < before_timestamp)
            if after_timestamp:
                query = query.filter(models.TimeSlot.end_at > after_timestamp)
            return query.all()

    def create(self, time_slot: schemas.TimeSlotCreate, now: int = int(datetime.utcnow().timestamp())):
        with self.db() as sess:
            self._check_basic(time_slot, now)
            self._check_overlap(sess, time_slot)
            db_time_slot = models.TimeSlot(
                user_id=time_slot.user_id,
                start_at=time_slot.start_at,
                end_at=time_slot.end_at
            )
            sess.add(db_time_slot)
            sess.commit()
            sess.refresh(db_time_slot)
        return db_time_slot

    def delete(self, user_id: int, target_id: int, *args):
        with self.db() as sess:
            sess.query(models.TimeSlot).filter_by(user_id=user_id, id=target_id).delete()
            sess.commit()
