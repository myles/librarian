from copy import deepcopy

import pytest

from librarian.collections.books import service
from librarian.integrations.openlibrary import OpenLibraryBook

from ...openlibrary_responses import BOOK_RESPONSE


def test_build_database(mock_db):
    service.build_database(mock_db)

    assert mock_db["books"].exists() is True
    assert mock_db["authors"].exists() is True
    assert mock_db["books_authors"].exists() is True


@pytest.mark.parametrize(
    "book_covers, expected_result",
    (
        ([8739161], "https://covers.openlibrary.org/b/id/8739161-L.jpg"),
        (
            [8739161, 1234567890],
            "https://covers.openlibrary.org/b/id/8739161-L.jpg",
        ),
        ([], None),
    ),
)
def test_get_openlibrary_book_cover_url(book_covers, expected_result):
    data = deepcopy(BOOK_RESPONSE)
    data["covers"] = book_covers

    book = OpenLibraryBook.from_data(data)
    result = service.get_openlibrary_book_cover_url(book)
    assert result == expected_result


def test_upsert_book_from_open_library(mock_book, mock_work, mock_db):
    service.build_database(mock_db)

    assert mock_db["books"].count == 0

    row = service.upsert_book_from_open_library(mock_book, [mock_work], mock_db)
    row_id = row["id"]

    assert row["title"] == mock_book.title

    assert mock_db["books"].count == 1

    row = service.upsert_book_from_open_library(mock_book, [mock_work], mock_db)
    assert row["id"] == row_id

    assert mock_db["books"].count == 1


def test_upset_author_from_openlibrary(mock_author, mock_db):
    service.build_database(mock_db)

    assert mock_db["authors"].count == 0

    row = service.upset_author_from_openlibrary(mock_author, mock_db)
    row_id = row["id"]

    assert row["name"] == mock_author.name

    assert mock_db["authors"].count == 1

    row = service.upset_author_from_openlibrary(mock_author, mock_db)
    assert row["id"] == row_id

    assert mock_db["authors"].count == 1


def test_link_book_to_authors(mock_book, mock_work, mock_author, mock_db):
    service.build_database(mock_db)

    book_row = service.upsert_book_from_open_library(
        mock_book, [mock_work], mock_db
    )
    author_row = service.upset_author_from_openlibrary(mock_author, mock_db)

    assert mock_db["books_authors"].count == 0
    service.link_book_to_authors(book_row, [author_row], mock_db)
    assert mock_db["books_authors"].count == 1

    service.link_book_to_authors(book_row, [author_row], mock_db)
    assert mock_db["books_authors"].count == 1
