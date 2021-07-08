import datetime
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.logger import logger
from typing import List

from app import schemas, errors
from app.controllers.time_slot import TimeSlotController
from app.controllers.base import BaseController
from app.database import SessionLocal

logging.basicConfig(format="%(asctime)s loglevel=%(levelname)-6s msg=\"%(message)s\" logger=%(name)s %(funcName)s() L%(lineno)-4d ", level=logging.INFO)
app = FastAPI()


# Dependency
class ControllerMaker:
    def __init__(self, controller_type: str):
        self.type = controller_type

    def __call__(self):
        if self.type == "time_slot":
            controller = TimeSlotController(SessionLocal)
        else:
            raise Exception("Controller not exist")
        yield controller


Controller = ControllerMaker("time_slot")


@app.get("/users/{user_id}/time-slots", response_model=List[schemas.TimeSlot])
def get_user_time_slots(
        user_id: int, before_timestamp: int = None, after_timestamp: int = None,
        controller: BaseController = Depends(Controller)
):
    time_slots = controller.list(user_id, before_timestamp=before_timestamp, after_timestamp=after_timestamp)
    if not time_slots:
        raise HTTPException(status_code=404, detail="result not found")
    return time_slots


@app.post("/users/{user_id}/time-slots", response_model=schemas.TimeSlot)
def create_user_time_slot(
        user_id: int, time_slot: schemas.TimeSlotBase, controller: BaseController = Depends(Controller)
):
    now = int(datetime.datetime.utcnow().timestamp())
    slot = schemas.TimeSlotCreate(
        user_id=user_id,
        start_at=time_slot.start_at,
        end_at=time_slot.end_at
    )
    try:
        obj = controller.create(slot, now=now)
    except errors.TimeOverlapError:
        logger.warning(f"User {user_id} sent overlapped time range")
        raise HTTPException(status_code=400, detail="time range overlap")
    except errors.TimeFormatError as e:
        logger.warning(f"User {user_id} sent time format error {e}")
        raise HTTPException(status_code=400, detail=str(e))
    return obj


@app.delete("/users/{user_id}/time-slots/{time_slot_id}")
def delete_user_time_slot(user_id: int, time_slot_id: int, controller: BaseController = Depends(Controller)):
    return controller.delete(user_id, time_slot_id)
