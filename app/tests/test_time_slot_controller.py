import datetime
import pytest

from sqlalchemy.orm.exc import NoResultFound

from app.tests import TestingSessionLocal, setup_function, teardown_function

from app.controllers.time_slot import TimeSlotController
from app.errors import TimeOverlapError, TimeFormatError
from app.models import TimeSlot
from app.schemas import TimeSlotCreate


def _get_controller():
    return TimeSlotController(TestingSessionLocal)


def test_create_timeslot():
    controller = _get_controller()

    expected_user_id = 1
    now = int(datetime.datetime.utcnow().replace(microsecond=0).timestamp())
    expected_start_at = now + 1
    expected_end_at = expected_start_at + 600
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at, end_at=expected_end_at)
    new_item = controller.create(new_slot, now)

    with TestingSessionLocal() as sess:
        obj = sess.query(TimeSlot).filter_by(user_id=expected_user_id).one()
        assert obj.user_id == expected_user_id
        assert obj.start_at == expected_start_at
        assert obj.end_at == expected_end_at


def test_create_timeslot__time_format_error():
    controller = _get_controller()

    expected_user_id = 1
    now = int(datetime.datetime.utcnow().replace(microsecond=0).timestamp())
    expected_start_at = now + 1
    expected_end_at = expected_start_at + 600

    # start_at less than now
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at - 100, end_at=expected_end_at)
    with pytest.raises(TimeFormatError):
        new_item = controller.create(new_slot, now)

    # end_at less equal than start_at
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at, end_at=expected_start_at)
    with pytest.raises(TimeFormatError):
        new_item = controller.create(new_slot, now)

    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at, end_at=expected_start_at - 100)
    with pytest.raises(TimeFormatError):
        new_item = controller.create(new_slot, now)

    # range of start_at and end_at must be in 24 hours
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at, end_at=expected_start_at + 86401)
    with pytest.raises(TimeFormatError):
        new_item = controller.create(new_slot, now)


def test_create_timeslot__overlap():
    controller = _get_controller()

    expected_user_id = 1
    now = int(datetime.datetime.utcnow().replace(microsecond=0).timestamp())
    expected_start_at = now + 200
    expected_end_at = expected_start_at + 600
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at, end_at=expected_end_at)
    new_item = controller.create(new_slot)

    # start1(start2) -- end1(end2)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    # start_at1 -- start_at2  -- end_at1 -- end_at2
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at, end_at=expected_end_at + 1)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    # start_at1 -- start_at2  -- end_at1 -- end_at2
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at + 1, end_at=expected_end_at + 1)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    # start_at2 -- start_at1 -- end_at2 -- end_at1
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at - 1, end_at=expected_end_at - 1)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    # start_at1 -- start_at2 -- end_at2 -- end_at1
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at + 1, end_at=expected_end_at - 1)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    # start_at2 -- start_at1 -- end_at1 -- end_at2
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at - 1, end_at=expected_end_at + 1)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    # start_at1(start_at2) -- end_at1 -- end_at2
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at, end_at=expected_end_at + 1)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    # start_at2 -- start_at1 -- end_at1(end_at2)
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at - 1, end_at=expected_end_at)
    with pytest.raises(TimeOverlapError):
        new_item = controller.create(new_slot, now)

    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_start_at - 2, end_at=expected_start_at)
    new_item = controller.create(new_slot, now)
    new_slot = TimeSlotCreate(user_id=expected_user_id, start_at=expected_end_at, end_at=expected_end_at + 1)
    new_item = controller.create(new_slot, now)
    raise Exception()

    with TestingSessionLocal() as sess:
        objs = sess.query(TimeSlot).filter_by(user_id=expected_user_id).all()
        assert len(objs) == 1
        assert objs[0].start_at == expected_start_at
        assert objs[0].end_at == expected_end_at


def test_get_user_time_slots():
    controller = _get_controller()

    now = int(datetime.datetime.utcnow().replace(microsecond=0).timestamp())
    start = now + 1
    users_and_slots = {
        1: [
            (start, start + 600),
            (start + 600, start + 1200),
            (start + 1200, start + 1800),
        ],
        2: [
            (start, start + 600),
            (start + 600, start + 1200),
            (start + 1200, start + 1800),
        ],
    }

    for user_id, slots in users_and_slots.items():
        for slot in slots:
            new_slot = TimeSlotCreate(user_id=user_id, start_at=slot[0], end_at=slot[1])
            new_item = controller.create(new_slot, now)

    for user_id in (1, 2):
        slots = controller.list(user_id)
        for idx, slot in enumerate(slots):
            assert users_and_slots[user_id][idx][0] == slot.start_at, slot.id
            assert users_and_slots[user_id][idx][1] == slot.end_at


def test_get_user_time_slots__filter():
    controller = _get_controller()

    now = int(datetime.datetime.utcnow().replace(microsecond=0).timestamp())
    start1 = now + 1
    end1 = start1 + 600

    start2 = start1 + 1200
    end2 = start2 + 600

    start3 = start2 + 1200
    end3 = start3 + 600
    user_id = 1
    expected_slots = [
        (start1, end1),
        (start2, end2),
        (start3, end3),
    ]
    for slot in expected_slots:
        new_slot = TimeSlotCreate(user_id=user_id, start_at=slot[0], end_at=slot[1])
        new_item = controller.create(new_slot, now)

    # before_timestamp
    slots = controller.list(user_id, before_timestamp=start1)
    assert len(slots) == 0

    slots = controller.list(user_id, before_timestamp=start2 + 1)
    assert len(slots) == 1
    assert slots[0].start_at == start1
    assert slots[0].end_at == end1

    # after_timestamp
    slots = controller.list(user_id, after_timestamp=end3)
    assert len(slots) == 0

    slots = controller.list(user_id, after_timestamp=end3 - 1)
    assert len(slots) == 1
    assert slots[0].start_at == start3
    assert slots[0].end_at == end3

    # before and after
    slots = controller.list(user_id, before_timestamp=end3, after_timestamp=end1)
    assert len(slots) == 1
    assert slots[0].start_at == start2
    assert slots[0].end_at == end2


def test_delete_user_time_slot():
    controller = _get_controller()

    user_id = 1
    now = int(datetime.datetime.utcnow().replace(microsecond=0).timestamp())
    start_at = now + 1
    end_at = start_at + 600
    new_slot = TimeSlotCreate(user_id=user_id, start_at=start_at, end_at=end_at)
    new_item = controller.create(new_slot, now)

    controller.delete(user_id, new_item.id)

    with TestingSessionLocal() as sess:
        with pytest.raises(NoResultFound):
            obj = sess.query(TimeSlot).filter_by(user_id=user_id, id=new_item.id).one()
