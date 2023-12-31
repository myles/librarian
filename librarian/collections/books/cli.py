import click
from sqlite_utils.db import Database

from ...integrations.openlibrary import OpenLibraryClient
from ...settings import Settings
from . import constants, service


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

    book, works, authors = service.fetch_book_and_related_data(
        isbn=isbn,
        client=client,
    )

    service.upsert_book_and_related_data(
        book=book, works=works, authors=authors, db=db
    )


@cli.command(name="add_books")
def add_books():
    """
    Add multiple books to the library's collection through a text editor.
    """
    db = Database(Settings.BOOK_DB_PATH)
    service.build_database(db)

    client = OpenLibraryClient()

    # Capture the user's input from their text editor.
    raw_isbns = click.edit()

    # Split the input into a list of ISBNs, removing any empty lines.
    isbns = filter(lambda item: item, raw_isbns.splitlines())

    for isbn in isbns:
        book, works, authors = service.fetch_book_and_related_data(
            isbn=isbn, client=client
        )

        service.upsert_book_and_related_data(
            book=book, works=works, authors=authors, db=db
        )


@cli.command(name="list")
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(choices=constants.OUTPUT_FORMATS),
    help="Format to output the results.",
)
def list_books(output_format: str = ""):
    """List the books in the library's collection."""
    db = Database(Settings.BOOK_DB_PATH)
    service.build_database(db)

    books = service.list_books(db)

    # If the user specified a format, output the results in that format.
    if output_format in constants.OUTPUT_FORMATS:
        click.echo(service.format_books_as_csv(books))
        return

    click.echo_via_pager(service.format_books_as_table(books))


@cli.command(name="search")
@click.argument("query")
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(choices=constants.OUTPUT_FORMATS),
    help="Format to output the results.",
)
def search_books(query: str, output_format: str = ""):
    """Search the library's collection."""
    db = Database(Settings.BOOK_DB_PATH)
    service.build_database(db)

    books = service.search_books(db=db, query=query)

    # If the user specified a format, output the results in that format.
    if output_format in constants.OUTPUT_FORMATS:
        click.echo(service.format_books_as_csv(books))
        return

    click.echo_via_pager(service.format_books_as_table(books))
