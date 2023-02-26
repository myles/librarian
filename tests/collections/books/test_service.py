from librarian.collections.books import service


def test_build_database(mock_db):
    service.build_database(mock_db)

    assert mock_db["books"].exists() is True
    assert mock_db["authors"].exists() is True
    assert mock_db["books_authors"].exists() is True


def test_upsert_book_from_open_library(mock_book, mock_db):
    service.build_database(mock_db)

    assert mock_db["books"].count == 0

    row = service.upsert_book_from_open_library(mock_book, mock_db)
    row_id = row["id"]

    assert row["title"] == mock_book.title

    assert mock_db["books"].count == 1

    row = service.upsert_book_from_open_library(mock_book, mock_db)
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


def test_link_book_to_authors(mock_book, mock_author, mock_db):
    service.build_database(mock_db)

    book_row = service.upsert_book_from_open_library(mock_book, mock_db)
    author_row = service.upset_author_from_openlibrary(mock_author, mock_db)

    assert mock_db["books_authors"].count == 0
    service.link_book_to_authors(book_row, [author_row], mock_db)
    assert mock_db["books_authors"].count == 1

    service.link_book_to_authors(book_row, [author_row], mock_db)
    assert mock_db["books_authors"].count == 1
