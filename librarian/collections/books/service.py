from typing import Any, Dict, Generator, List, Optional

from sqlite_utils.db import Database, Table

from ...integrations.openlibrary import Author, Book, OpenLibraryClient


def build_database(db: Database):
    """
    Build the SQLite database for the books' library.
    """
    books_table: Table = db.table("books")  # type: ignore
    authors_table: Table = db.table("authors")  # type: ignore
    books_authors_table: Table = db.table("books_authors")  # type: ignore

    if books_table.exists() is False:
        books_table.create(
            columns={
                "id": int,
                "title": str,
                "isbn_10": int,
                "isbn_13": int,
                "openlibrary_key": str,
            },
            pk="id",
        )
        books_table.enable_fts(["title"], create_triggers=True)

    if authors_table.exists() is False:
        authors_table.create(
            columns={
                "id": int,
                "name": str,
                "openlibrary_key": str,
            },
            pk="id",
        )
        authors_table.enable_fts(["name"], create_triggers=True)

    if books_authors_table.exists() is False:
        books_authors_table.create(
            columns={
                "book_id": int,
                "author_id": int,
            },
            pk=("book_id", "author_id"),
            foreign_keys=(
                ("book_id", "books", "id"),
                ("author_id", "authors", "id"),
            ),
        )


def upsert_book_from_open_library(book: Book, db: Database) -> Dict[str, Any]:
    """
    Upsert a book from OpenLibrary in the SQLite database.
    """
    table: Table = db.table("books")  # type: ignore

    existing_book_ids = list(
        table.pks_and_rows_where(
            where="openlibrary_key = :key", where_args={"key": book.key}
        )
    )

    existing_book_id: Optional[int] = None
    if existing_book_ids:
        existing_book_id, _ = existing_book_ids[0]

    record: Dict[str, Any] = {"openlibrary_key": book.key, "title": book.title}

    if book.isbn_10:
        record["isbn_10"] = book.isbn_10[0]

    if book.isbn_13:
        record["isbn_13"] = book.isbn_13[0]

    if existing_book_id is not None:
        record["id"] = existing_book_id
        table = table.upsert(record, pk="id")
    else:
        table = table.insert(record)

    return table.get(table.last_pk)  # type: ignore


def get_book_from_openlibrary(
    isbn: str, client: Optional[OpenLibraryClient] = None
) -> Book:
    """
    Get a book from OpenLibrary's API.
    """
    if client is None:
        client = OpenLibraryClient()

    return client.get_book_from_isbn(isbn=isbn)


def upset_author_from_openlibrary(
    author: Author, db: Database
) -> Dict[str, Any]:
    """
    Upsert an author from OpenLibrary an SQLite database.
    """
    table: Table = db.table("authors")  # type: ignore

    existing_author_ids = list(
        table.pks_and_rows_where(
            where="openlibrary_key = :key", where_args={"key": author.key}
        )
    )

    existing_author_id: Optional[int] = None
    if existing_author_ids:
        existing_author_id, _ = existing_author_ids[0]

    record: Dict[str, Any] = {
        "openlibrary_key": author.key,
        "name": author.name,
    }

    if existing_author_id is not None:
        record["id"] = existing_author_id
        table = table.upsert(record, pk="id")
    else:
        table = table.insert(record)

    return table.get(table.last_pk)  # type: ignore


def get_author_from_openlibrary(
    openlibrary_key: str, client: Optional[OpenLibraryClient] = None
) -> Author:
    """
    Add an author to the collection.
    """
    if client is None:
        client = OpenLibraryClient()

    return client.get_author(key=openlibrary_key)


def link_book_to_authors(
    book_row: Dict[str, Any], author_rows: List[Dict[str, Any]], db: Database
):
    """
    Upsert the M2M connection between a book and it's authors.
    """
    table: Table = db.table("books_authors")  # type: ignore

    records = [
        {"book_id": book_row["id"], "author_id": author_row["id"]}
        for author_row in author_rows
    ]

    table.upsert_all(records, pk=["book_id", "author_id"])


def list_books(db: Database) -> Generator[Dict[str, Any], None, None]:
    """
    Returns a list of books in the SQLite database.
    """
    table = db.table("books")
    return table.rows_where(
        select="id, title, iif(isbn_13, isbn_13, isbn_10) as isbn"
    )
