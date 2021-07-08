from pydantic import BaseModel


class TimeSlotBase(BaseModel):
    start_at: int
    end_at: int


class TimeSlotCreate(TimeSlotBase):
    user_id: int


class TimeSlot(TimeSlotBase):
    id: int

    class Config:
        orm_mode = True
