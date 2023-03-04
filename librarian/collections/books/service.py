import datetime
from typing import Any, Dict, Generator, Iterable, List, Optional, Union

from sqlite_utils.db import Database, Table

from ...integrations import openlibrary


def build_database(db: Database):
    """
    Build the SQLite database for the books' library.
    """
    openlibrary_entities_table: Table = db.table(
        "openlibrary_entities"
    )  # type: ignore

    if openlibrary_entities_table.exists() is False:
        openlibrary_entities_table.create(
            columns={
                "key": str,
                "type": str,
                "data": str,
                "updated_at": datetime.datetime,
            },
            pk="key",
        )

    books_table: Table = db.table("books")  # type: ignore
    authors_table: Table = db.table("authors")  # type: ignore
    books_authors_table: Table = db.table("books_authors")  # type: ignore

    if books_table.exists() is False:
        books_table.create(
            columns={
                "id": int,
                "title": str,
                "cover": str,
                "description": str,
                "first_sentence": str,
                "isbn_10": int,
                "isbn_13": int,
                "openlibrary_key": str,
                "created_at": datetime.datetime,
                "updated_at": datetime.datetime,
            },
            pk="id",
            foreign_keys=(("openlibrary_key", "openlibrary_entities", "key"),),
        )
        books_table.enable_fts(["title"], create_triggers=True)

    if authors_table.exists() is False:
        authors_table.create(
            columns={
                "id": int,
                "name": str,
                "openlibrary_key": str,
                "created_at": datetime.datetime,
                "updated_at": datetime.datetime,
            },
            pk="id",
            foreign_keys=(("openlibrary_key", "openlibrary_entities", "key"),),
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

    db.create_view(
        name="list_books_and_authors",
        sql="""
        select
            books.id,
            books.title,
            iif(books.isbn_13, books.isbn_13, books.isbn_10) as isbn,
            group_concat(authors.name, ', ') as authors
        from
            authors
            left outer join books_authors on books_authors.author_id = authors.id
            left outer join books on books.id = books_authors.book_id
        group by
            books.title
        order by
            books.title
        """,
        replace=True,
    )


def get_openlibrary_book_cover_url(
    book: openlibrary.OpenLibraryBook,
) -> Optional[str]:
    """
    Get the URL for the book's cover from OpenLibrary.
    """
    try:
        cover_id = book.covers[0]
    except IndexError:
        return None

    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"


OpenLibraryEntities = Union[
    openlibrary.OpenLibraryAuthor,
    openlibrary.OpenLibraryBook,
    openlibrary.OpenLibraryWork,
]


def upsert_openlibrary_entities(
    entities: Iterable[OpenLibraryEntities], db: Database
):
    """
    Upsert all the entities from OpenLibrary into the SQLite database.
    """
    table: Table = db.table("openlibrary_entities")  # type: ignore

    records = []
    for entity in entities:
        records.append(
            {
                "key": entity.key,
                "type": entity.type_key,
                "data": entity.data,
                "updated_at": datetime.datetime.utcnow(),
            }
        )

    table.upsert_all(records, pk="key")


def upsert_book_from_open_library(
    book: openlibrary.OpenLibraryBook,
    works: List[openlibrary.OpenLibraryWork],
    db: Database,
) -> Dict[str, Any]:
    """
    Upsert a book into the SQLite database.
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

    record: Dict[str, Any] = {
        "openlibrary_key": book.key,
        "title": book.title,
        "cover": get_openlibrary_book_cover_url(book),
        "first_sentence": book.first_sentence,
        "updated_at": datetime.datetime.utcnow(),
    }

    if book.isbn_10:
        record["isbn_10"] = book.isbn_10[0]

    if book.isbn_13:
        record["isbn_13"] = book.isbn_13[0]

    if len(works) > 0:
        work = works[0]
        record["description"] = work.description

    if existing_book_id is not None:
        record["id"] = existing_book_id
        table = table.upsert(record, pk="id")
    else:
        record["created_at"] = datetime.datetime.utcnow()
        table = table.insert(record)

    return table.get(table.last_pk)  # type: ignore


def get_book_from_openlibrary(
    isbn: str, client: Optional[openlibrary.OpenLibraryClient] = None
) -> openlibrary.OpenLibraryBook:
    """
    Get a book from OpenLibrary's API.
    """
    if client is None:
        client = openlibrary.OpenLibraryClient()

    return client.get_book_from_isbn(isbn=isbn)


def get_work_from_openlibrary(
    openlibrary_key: str,
    client: Optional[openlibrary.OpenLibraryClient] = None,
) -> openlibrary.OpenLibraryWork:
    """
    Get a work from OpenLibrary's API.
    """
    if client is None:
        client = openlibrary.OpenLibraryClient()

    return client.get_work(key=openlibrary_key)


def upset_author_from_openlibrary(
    author: openlibrary.OpenLibraryAuthor, db: Database
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
        "updated_at": datetime.datetime.utcnow(),
    }

    if existing_author_id is not None:
        record["id"] = existing_author_id
        table = table.upsert(record, pk="id")
    else:
        record["created_at"] = datetime.datetime.utcnow()
        table = table.insert(record)

    return table.get(table.last_pk)  # type: ignore


def get_author_from_openlibrary(
    openlibrary_key: str, client: Optional[openlibrary.OpenLibraryClient] = None
) -> openlibrary.OpenLibraryAuthor:
    """
    Add an author to the collection.
    """
    if client is None:
        client = openlibrary.OpenLibraryClient()

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
    table = db.table("list_books_and_authors")
    return table.rows_where(select="id, title, isbn, authors")
