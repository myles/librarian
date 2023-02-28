import datetime
from typing import Dict, List

import pytest
import responses

from librarian.integrations import openlibrary

from .. import openlibrary_responses


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
    result = openlibrary.format_date(value)
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
    result = openlibrary.format_date(value)
    assert result == expected_result


@pytest.mark.parametrize(
    "string, expected_group_dict",
    (
        ("/works/123abc", {"key_type": "works", "key": "123abc"}),
        ("/authors/456def", {"key_type": "authors", "key": "456def"}),
    ),
)
def test_re_key(string: str, expected_group_dict: Dict[str, str]):
    group_dict = openlibrary.RE_KEY.match(string).groupdict()
    assert group_dict == expected_group_dict


@pytest.mark.parametrize(
    "string, expected_result",
    (
        ("/works/123abc", "123abc"),
        ("/authors/456def", "456def"),
    ),
)
def test_format_key(string: str, expected_result: str):
    result = openlibrary.format_key(string)
    assert result == expected_result


@pytest.mark.parametrize(
    "data, expected_result",
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
    data: List[Dict[str, str]], expected_result: List[str]
):
    result = openlibrary.format_key_list(data)
    assert result == expected_result


def test_openlibrary_book__from_data():
    data = openlibrary_responses.BOOK_RESPONSE.copy()
    book = openlibrary.OpenLibraryBook.from_data(data)

    assert book.title == data["title"]
    assert book.key == "OL7353617M"
    assert book.type_key == "edition"


def test_openlibrary_work__from_data():
    data = openlibrary_responses.WORK_RESPONSE.copy()
    work = openlibrary.OpenLibraryWork.from_data(data)

    assert work.title == data["title"]
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
    data = openlibrary_responses.WORK_RESPONSE.copy()
    data["description"] = description

    work = openlibrary.OpenLibraryWork.from_data(data)

    assert work.description == expected_description


def test_openlibrary_link__from_data():
    data = {
        "url": "https://exmaple.com/",
        "title": "Example",
        "type": {"key": "/type/link"},
    }
    link = openlibrary.OpenLibraryLink.from_data(data)

    assert link.url == data["url"]
    assert link.title == data["title"]
    assert link.type_key == "link"


def test_openlibrary_author__from_data():
    data = openlibrary_responses.AUTHOR_RESPONSE.copy()
    author = openlibrary.OpenLibraryAuthor.from_data(data)

    assert author.name == data["name"]
    assert author.key == "OL34184A"
    assert author.type_key == "author"


@responses.activate
def test_open_library_client__get_book_from_isbn():
    response_data = openlibrary_responses.BOOK_RESPONSE.copy()

    # Querying OpenLibrary's ISBN endpoint will redirect you to the Books
    # endpoint.
    first_url = "https://openlibrary.org/isbn/0140328726.json"
    second_url = "https://openlibrary.org/books/OL7353617M.json"

    first_response = responses.Response(
        method="GET",
        url=first_url,
        status=301,
        headers={"Location": second_url},
    )
    responses.add(first_response)

    second_response = responses.Response(
        method="GET",
        url=second_url,
        json=response_data,
    )
    responses.add(second_response)

    client = openlibrary.OpenLibraryClient()
    book = client.get_book_from_isbn(isbn="0140328726")

    assert book.title == response_data["title"]


@responses.activate
def test_open_library_client__get_author():
    response_data = openlibrary_responses.AUTHOR_RESPONSE.copy()

    url = "https://openlibrary.org/authors/OL34184A.json"

    response = responses.Response(
        method="GET",
        url=url,
        json=response_data,
    )
    responses.add(response)

    client = openlibrary.OpenLibraryClient()
    author = client.get_author(key="OL34184A")

    assert author.name == response_data["name"]


@responses.activate
def test_open_library_client__get_work():
    response_data = openlibrary_responses.WORK_RESPONSE.copy()

    url = "https://openlibrary.org/works/OL45804W.json"

    response = responses.Response(
        method="GET",
        url=url,
        json=response_data,
    )
    responses.add(response)

    client = openlibrary.OpenLibraryClient()
    work = client.get_work(key="OL45804W")

    assert work.title == response_data["title"]
