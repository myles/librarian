import datetime
import typing as t

from pandas import DataFrame
from sqlite_utils.db import Database, Table, View
from tabulate import tabulate

from ...integrations import openlibrary
from . import constants


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

    # Views
    list_books_and_authors_view: View = db.table(
        "list_books_and_authors"
    )  # type: ignore

    db.create_view(
        name=list_books_and_authors_view.name,
        sql="""
        select
            books.id,
            books.title,
            books.description,
            iif(books.isbn_13, books.isbn_13, books.isbn_10) as isbn,
            group_concat(authors.name, ', ') as authors
        from
            authors
        left outer join books_authors
            on books_authors.author_id = authors.id
        left outer join books
            on books.id = books_authors.book_id
        group by
            books.title
        order by
            books.title
        """,
        replace=True,
    )


def get_openlibrary_book_cover_url(
    book: openlibrary.OpenLibraryBook,
) -> t.Optional[str]:
    """
    Get the URL for the book's cover from OpenLibrary.
    """
    try:
        cover_id = book.covers[0]
    except IndexError:
        return None

    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"


OpenLibraryEntities = t.Union[
    openlibrary.OpenLibraryAuthor,
    openlibrary.OpenLibraryBook,
    openlibrary.OpenLibraryWork,
]


def upsert_openlibrary_entities(
    entities: t.Iterable[OpenLibraryEntities], db: Database
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
    works: t.List[openlibrary.OpenLibraryWork],
    db: Database,
) -> t.Dict[str, t.Any]:
    """
    Upsert a book into the SQLite database.
    """
    table: Table = db.table("books")  # type: ignore

    existing_book_ids = list(
        table.pks_and_rows_where(
            where="openlibrary_key = :key", where_args={"key": book.key}
        )
    )

    existing_book_id: t.Optional[int] = None
    if existing_book_ids:
        existing_book_id, _ = existing_book_ids[0]

    record: t.Dict[str, t.Any] = {
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
    isbn: str, client: t.Optional[openlibrary.OpenLibraryClient] = None
) -> openlibrary.OpenLibraryBook:
    """
    Get a book from OpenLibrary's API.
    """
    if client is None:
        client = openlibrary.OpenLibraryClient()

    return client.get_book_from_isbn(isbn=isbn)


def get_work_from_openlibrary(
    openlibrary_key: str,
    client: t.Optional[openlibrary.OpenLibraryClient] = None,
) -> openlibrary.OpenLibraryWork:
    """
    Get a work from OpenLibrary's API.
    """
    if client is None:
        client = openlibrary.OpenLibraryClient()

    return client.get_work(key=openlibrary_key)


def upset_author_from_openlibrary(
    author: openlibrary.OpenLibraryAuthor, db: Database
) -> t.Dict[str, t.Any]:
    """
    Upsert an author from OpenLibrary an SQLite database.
    """
    table: Table = db.table("authors")  # type: ignore

    existing_author_ids = list(
        table.pks_and_rows_where(
            where="openlibrary_key = :key", where_args={"key": author.key}
        )
    )

    existing_author_id: t.Optional[int] = None
    if existing_author_ids:
        existing_author_id, _ = existing_author_ids[0]

    record: t.Dict[str, t.Any] = {
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
    openlibrary_key: str,
    client: t.Optional[openlibrary.OpenLibraryClient] = None,
) -> openlibrary.OpenLibraryAuthor:
    """
    Add an author to the collection.
    """
    if client is None:
        client = openlibrary.OpenLibraryClient()

    return client.get_author(key=openlibrary_key)


def link_book_to_authors(
    book_row: t.Dict[str, t.Any],
    author_rows: t.List[t.Dict[str, t.Any]],
    db: Database,
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


FETCH_BOOK_AND_RELATED_DATA_RETURN = t.Tuple[
    openlibrary.OpenLibraryBook,
    t.List[openlibrary.OpenLibraryWork],
    t.List[openlibrary.OpenLibraryAuthor],
]


def fetch_book_and_related_data(
    isbn: str,
    client: t.Optional[openlibrary.OpenLibraryClient] = None,
) -> FETCH_BOOK_AND_RELATED_DATA_RETURN:
    """
    Fetch a book and all it's related data from OpenLibrary.
    """
    if client is None:
        client = openlibrary.OpenLibraryClient()

    book = get_book_from_openlibrary(isbn=isbn, client=client)
    works = [
        get_work_from_openlibrary(work_key, client=client)
        for work_key in book.work_keys
    ]

    if works:
        author_keys = [
            author_key for work in works for author_key in work.author_keys
        ]
    else:
        author_keys = book.author_keys

    authors = [
        get_author_from_openlibrary(openlibrary_key=author_key, client=client)
        for author_key in author_keys
    ]

    return book, works, authors


def upsert_book_and_related_data(
    book: openlibrary.OpenLibraryBook,
    works: t.List[openlibrary.OpenLibraryWork],
    authors: t.List[openlibrary.OpenLibraryAuthor],
    db: Database,
) -> None:
    """
    Upsert a book and all it's related data from OpenLibrary.
    """
    # Save everything to our first class tables.
    book_row = upsert_book_from_open_library(book, works, db=db)
    author_rows = [
        upset_author_from_openlibrary(author, db=db) for author in authors
    ]
    link_book_to_authors(book_row, author_rows, db=db)

    # Save the API responses from Openlibrary.
    upsert_openlibrary_entities(
        entities=[book] + authors + works,  # type: ignore
        db=db,
    )


def list_books(db: Database) -> t.Generator[t.Dict[str, t.Any], None, None]:
    """
    Returns a list of books in the SQLite database.
    """
    table = db.table("list_books_and_authors")
    return table.rows_where(select="isbn, title, authors")


def search_books(
    db: Database, query: str
) -> t.Generator[t.Dict[str, t.Any], None, None]:
    """
    Search the SQLite database for books.
    """
    books_table: Table = db.table("books")  # type: ignore

    view: View = db.table("list_books_and_authors")  # type: ignore

    book_ids = [
        row["id"] for row in books_table.search(q=query, columns=("id",))
    ]

    return view.rows_where(
        select="isbn, title, authors",
        where="id in ({})".format(",".join("?" * len(book_ids))),
        where_args=book_ids,
    )


def format_books_as_csv(
    books: t.Generator[t.Dict[str, t.Any], None, None]
) -> str:
    """
    Format a list of books as CSV.
    """
    return DataFrame(books).to_csv(index=False)


def format_books_as_json(
    books: t.Generator[t.Dict[str, t.Any], None, None]
) -> str:
    """
    Format a list of books as JSON.
    """
    return DataFrame(books).to_json(orient="records", indent=2)


def format_books_as_markdown(
    books: t.Generator[t.Dict[str, t.Any], None, None]
) -> str:
    """
    Format a list of books as Markdown.
    """
    return tabulate(books, headers="keys", tablefmt="github")


def format_books_as_table(
    books: t.Generator[t.Dict[str, t.Any], None, None]
) -> str:
    """
    Format a list of books as a table.
    """
    return tabulate(
        books,
        headers={"isbn": "ISBN", "title": "Title", "authors": "Author(s)"},
        tablefmt="grid",
        maxcolwidths=[None, 24, 24],
    )


def format_books(
    books: t.Generator[t.Dict[str, t.Any], None, None],
    output_format: str,
) -> str:
    """
    Format a list of books.
    """
    if output_format == constants.OUTPUT_FORMAT_CSV:
        return format_books_as_csv(books)
    elif output_format == constants.OUTPUT_FORMAT_JSON:
        return format_books_as_json(books)
    elif output_format == constants.OUTPUT_FORMAT_MARKDOWN:
        return format_books_as_markdown(books)

    raise ValueError(
        f"Invalid output format: {output_format}. Must be one of: "
        f"{', '.join(constants.OUTPUT_FORMATS)}"
    )
