import datetime

from fastapi.testclient import TestClient

from . import TestingSessionLocal, setup_function, teardown_function
from app.main import app, Controller
from app.controllers.time_slot import TimeSlotController


# Dependency
class OverrideControllerMaker:
    def __init__(self, controller_type: str):
        self.type = controller_type

    def __call__(self):
        if self.type == "time_slot":
            controller = TimeSlotController(TestingSessionLocal)
        else:
            raise Exception("Controller not exist")
        yield controller


override_controller = OverrideControllerMaker("time_slot")


app.dependency_overrides[Controller] = override_controller
client = TestClient(app)


def _create_user_time_slot(user_id: int, start_at: int, end_at: int):
    resp = client.post(
        f"/users/{user_id}/time-slots",
        json={
            "start_at": start_at,
            "end_at": end_at
        }
    )
    return resp


def _check_get_response(user_id: int, expected: list, query_string: str = None, status: int = 200):
    if query_string:
        uri = f"/users/{user_id}/time-slots{query_string}"
    else:
        uri = f"/users/{user_id}/time-slots"

    resp = client.get(
        uri
    )
    assert resp.status_code == status
    assert resp.json() == expected


def test_get_user_time_slots__not_found():
    user_id = 1
    resp = client.get(
        f"/users/{user_id}/time-slots"
    )
    assert resp.status_code == 404
    assert resp.json() == {"detail": "result not found"}


def test_get_user_time_slots__normal():

    # one user one slot
    user_id = 1
    start_at = int(datetime.datetime.utcnow().timestamp()) + 10
    end_at = start_at + 120
    _create_user_time_slot(user_id, start_at, end_at)

    expected = [
        {
            "id": 1,
            "start_at": start_at,
            "end_at": end_at,
        }
    ]
    _check_get_response(
        user_id,
        expected
    )

    # one user two slot
    start_at2 = start_at + 200
    end_at2 = start_at2 + 300
    _create_user_time_slot(user_id, start_at2, end_at2)

    expected = [
        {
            "id": 1,
            "start_at": start_at,
            "end_at": end_at,
        },
        {
            "id": 2,
            "start_at": start_at2,
            "end_at": end_at2,
        }
    ]
    _check_get_response(
        user_id,
        expected
    )

    # two user, one is two slots and another is one slot
    user_id2 = 2
    start_at2 = start_at + 200
    end_at2 = start_at2 + 300
    _create_user_time_slot(user_id2, start_at2, end_at2)

    expected = [
        {
            "id": 1,
            "start_at": start_at,
            "end_at": end_at,
        },
        {
            "id": 2,
            "start_at": start_at2,
            "end_at": end_at2,
        }
    ]
    _check_get_response(
        user_id,
        expected
    )

    expected = [
        {
            "id": 3,
            "start_at": start_at2,
            "end_at": end_at2,
        }
    ]
    _check_get_response(
        user_id2,
        expected
    )


def test_get_user_time_slots__query_filter():

    # one user one slot
    user_id = 1
    start_at = int(datetime.datetime.utcnow().timestamp()) + 10
    end_at = start_at + 120
    start_at2 = start_at + 200
    end_at2 = start_at2 + 100
    start_at3 = start_at2 + 100
    end_at3 = start_at3 + 100
    _create_user_time_slot(user_id, start_at, end_at)
    _create_user_time_slot(user_id, start_at2, end_at2)
    _create_user_time_slot(user_id, start_at3, end_at3)

    query_string = f"?before_timestamp={end_at - 1}"
    _check_get_response(
        user_id,
        {"detail": "result not found"},
        query_string=query_string,
        status=404
    )

    query_string = f"?before_timestamp={end_at + 1}"
    _check_get_response(
        user_id,
        [{"id": 1, "start_at": start_at, "end_at": end_at}],
        query_string=query_string,
    )

    query_string = f"?after_timestamp={end_at3 + 1}"
    _check_get_response(
        user_id,
        {"detail": "result not found"},
        query_string=query_string,
        status=404
    )

    query_string = f"?after_timestamp={end_at3 - 1}"
    _check_get_response(
        user_id,
        [{"id": 3, "start_at": start_at3, "end_at": end_at3}],
        query_string=query_string,
    )

    query_string = f"?before_timestamp={end_at3}&after_timestamp={end_at}"
    _check_get_response(
        user_id,
        [{"id": 2, "start_at": start_at2, "end_at": end_at2}],
        query_string=query_string,
    )


def test_create_user_time_slot():
    user_id = 1
    start_at = int(datetime.datetime.utcnow().timestamp()) + 10
    end_at = start_at + 120
    resp = _create_user_time_slot(user_id, start_at, end_at)
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "start_at": start_at, "end_at": end_at}


def test_create_user_time_slot__overlap():
    user_id = 1
    start_at = int(datetime.datetime.utcnow().timestamp()) + 10
    end_at = start_at + 120
    resp = _create_user_time_slot(user_id, start_at, end_at)
    assert resp.status_code == 200
    assert resp.json() == {"id": 1, "start_at": start_at, "end_at": end_at}

    resp = _create_user_time_slot(user_id, start_at, end_at)
    assert resp.status_code == 400
    assert resp.json() == {"detail": "time range overlap"}


def test_create_user_time_slot__format_error():
    user_id = 1
    start_at = int(datetime.datetime.utcnow().timestamp()) + 10
    end_at = start_at + 120

    resp = _create_user_time_slot(user_id, end_at, start_at)
    assert resp.status_code == 400
    assert resp.json() == {"detail": "start_at must less than end_at"}

    resp = _create_user_time_slot(user_id, start_at - 1000, end_at)
    assert resp.status_code == 400
    assert resp.json() == {"detail": "start_at must greater than now"}

    resp = _create_user_time_slot(user_id, start_at, start_at + 86401)
    assert resp.status_code == 400
    assert resp.json() == {"detail": "range start_at and end_at must in 24 hours"}


def test_delete_user_time_slot():
    user_id = 1
    start_at = int(datetime.datetime.utcnow().timestamp()) + 10
    end_at = start_at + 120
    resp = _create_user_time_slot(user_id, start_at, end_at)
    resp_json = resp.json()

    resp = client.delete(
        f"/users/{user_id}/time-slots/{resp_json['id']}"
    )
    assert resp.status_code == 200
