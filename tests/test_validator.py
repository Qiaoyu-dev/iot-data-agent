import pytest
from pydantic import ValidationError

from api.schemas import ChatRequest


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", 422),
        ("   ", 422),
        ("你好", 200),
        ("a" * 600, 422),
    ],
)
def test_chat_request_validation(raw: str, expected: int):
    try:
        ChatRequest(message=raw)
        got = 200
    except ValidationError:
        got = 422
    assert got == expected


def test_thread_id_has_default():
    assert ChatRequest(message="hi").thread_id == "default"


def test_thread_id_max_length():
    with pytest.raises(ValidationError):
        ChatRequest(message="hi", thread_id="x" * 100)
