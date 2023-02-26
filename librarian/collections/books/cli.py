from typing import Optional

import click
from pandas import DataFrame
from sqlite_utils.db import Database
from tabulate import tabulate

from ...integrations.openlibrary import OpenLibraryClient
from ...settings import Settings
from . import service


@click.group()
def cli():
    """Inventory the library's books collection."""


@cli.command(name="add")
@click.option(
    "--isbn",
    prompt="The ISBN of the book you want to add",
    prompt_required=True,
)
def add_book(isbn: str):
    """Add a book to the library's collection."""
    db = Database(Settings.BOOK_DB_PATH)
    service.build_database(db)

    client = OpenLibraryClient()

    book = service.get_book_from_openlibrary(isbn=isbn, client=client)
    book_row = service.upsert_book_from_open_library(book, db=db)

    authors = [
        service.get_author_from_openlibrary(
            openlibrary_key=author_key, client=client
        )
        for author_key in book.author_keys
    ]
    author_rows = [
        service.upset_author_from_openlibrary(author, db=db)
        for author in authors
    ]

    service.link_book_to_authors(book_row, author_rows, db=db)


@cli.command(name="list")
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["csv", "json", "markdown"]),
    default=None,
    help="Format to output the results.",
)
def list_books(output_format: Optional[str] = None):
    """List the books in the library's collection."""
    db = Database(Settings.BOOK_DB_PATH)
    service.build_database(db)

    books = service.list_books(db)

    if output_format == "csv":
        click.echo(DataFrame(books).to_csv(index=False))
    elif output_format == "json":
        click.echo(DataFrame(books).to_json(orient="records", indent=2))
    else:
        table = tabulate(books, headers="keys", tablefmt="github")
        click.echo(table)
