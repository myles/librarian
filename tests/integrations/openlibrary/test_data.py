import datetime
from typing import Dict, List

import pytest

from librarian.integrations.openlibrary import data

from . import openlibrary_responses


@pytest.mark.parametrize(
    "value, expected_result",
    (
        ("September 19, 1986", datetime.date(1986, 9, 19)),
        ("September 1986", datetime.date(1986, 9, 1)),
        ("1986", datetime.date(1986, 1, 1)),
        ("", None),
        ("  ", None),
        (None, None),
    ),
)
def test_format_date(value: str, expected_result: datetime.date):
    result = data.format_date(value)
    assert result == expected_result


@pytest.mark.parametrize(
    "value, expected_result",
    (
        ("2023-02-26T21:20:35", datetime.datetime(2023, 2, 26, 21, 20, 35)),
        ("", None),
        ("  ", None),
        (None, None),
    ),
)
def format_datetime(value: str, expected_result: datetime.datetime):
    result = data.format_date(value)
    assert result == expected_result


@pytest.mark.parametrize(
    "string, expected_group_dict",
    (
        ("/works/123abc", {"key_type": "works", "key": "123abc"}),
        ("/authors/456def", {"key_type": "authors", "key": "456def"}),
    ),
)
def test_re_key(string: str, expected_group_dict: Dict[str, str]):
    group_dict = data.RE_KEY.match(string).groupdict()
    assert group_dict == expected_group_dict


@pytest.mark.parametrize(
    "string, expected_result",
    (
        ("/works/123abc", "123abc"),
        ("/authors/456def", "456def"),
    ),
)
def test_format_key(string: str, expected_result: str):
    result = data.format_key(string)
    assert result == expected_result


@pytest.mark.parametrize(
    "payload, expected_result",
    (
        ([], []),
        ([{"key": "/authors/123abc"}], ["123abc"]),
        (
            [{"key": "/authors/123abc"}, {"key": "/authors/456def"}],
            ["123abc", "456def"],
        ),
    ),
)
def test_format_key_list(
    payload: List[Dict[str, str]], expected_result: List[str]
):
    result = data.format_key_list(payload)
    assert result == expected_result


def test_openlibrary_book__from_data():
    payload = openlibrary_responses.BOOK_RESPONSE.copy()
    book = data.OpenLibraryBook.from_data(payload)

    assert book.title == payload["title"]
    assert book.key == "OL7353617M"
    assert book.type_key == "edition"


def test_openlibrary_work__from_data():
    payload = openlibrary_responses.WORK_RESPONSE.copy()
    work = data.OpenLibraryWork.from_data(payload)

    assert work.title == payload["title"]
    assert work.key == "OL45804W"
    assert work.type_key == "work"


@pytest.mark.parametrize(
    "description, expected_description",
    (
        ("I am a work's description!", "I am a work's description!"),
        (
            {"type": "/type/text", "value": "I am a work's description!"},
            "I am a work's description!",
        ),
    ),
)
def test_openlibrary_work__from_data__description(
    description, expected_description
):
    payload = openlibrary_responses.WORK_RESPONSE.copy()
    payload["description"] = description

    work = data.OpenLibraryWork.from_data(payload)

    assert work.description == expected_description


def test_openlibrary_link__from_data():
    payload = {
        "url": "https://exmaple.com/",
        "title": "Example",
        "type": {"key": "/type/link"},
    }
    link = data.OpenLibraryLink.from_data(payload)

    assert link.url == payload["url"]
    assert link.title == payload["title"]
    assert link.type_key == "link"


def test_openlibrary_author__from_data():
    payload = openlibrary_responses.AUTHOR_RESPONSE.copy()
    author = data.OpenLibraryAuthor.from_data(payload)

    assert author.name == payload["name"]
    assert author.key == "OL34184A"
    assert author.type_key == "author"
