import datetime

import pytest

from librarian.integrations.openlibrary import Author, Book

from ...openlibrary_responses import AUTHOR_RESPONSE, BOOK_RESPONSE


@pytest.fixture
def mock_book() -> Book:
    return Book(
        title=BOOK_RESPONSE["title"],
        publish_date=datetime.date(1988, 10, 1),
    )


@pytest.fixture
def mock_author() -> Author:
    return Author(
        key="OL34184A",
        name=AUTHOR_RESPONSE["name"],
        type_key="author",
    )
