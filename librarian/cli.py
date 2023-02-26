import click

from .collections.books.cli import cli as books_cli


@click.group()
@click.version_option()
def cli():
    """
    Translate the library's collection into a SQLite database.
    """


cli.add_command(books_cli, name="books")
