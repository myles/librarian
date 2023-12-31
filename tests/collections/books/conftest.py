import datetime

import pytest

from librarian.integrations import openlibrary

from ...integrations.openlibrary import openlibrary_responses


@pytest.fixture
def mock_book() -> openlibrary.OpenLibraryBook:
    return openlibrary.OpenLibraryBook(
        key="IAmAnOpenLibraryKey",
        title=openlibrary_responses.BOOK_RESPONSE["title"],
        publish_date=datetime.date(1988, 10, 1),
    )


@pytest.fixture
def mock_work() -> openlibrary.OpenLibraryWork:
    return openlibrary.OpenLibraryWork(
        key="IAmAnOpenLibraryKey",
        title=openlibrary_responses.WORK_RESPONSE["title"],
    )


@pytest.fixture
def mock_author() -> openlibrary.OpenLibraryAuthor:
    return openlibrary.OpenLibraryAuthor(
        key="IAmAnOpenLibraryKey",
        name="I Am An Author's Name",
    )
