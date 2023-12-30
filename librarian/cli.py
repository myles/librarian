import click

from .collections.books.cli import cli as books_cli
from .collections.vinyl.cli import cli as vinyl_cli


@click.group()
@click.version_option()
def cli():
    """
    Translate the library's collection into a SQLite database.
    """


cli.add_command(books_cli, name="books")  # type: ignore
cli.add_command(vinyl_cli, name="vinyl")  # type: ignore
