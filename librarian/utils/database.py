from pathlib import Path

from sqlite_utils.db import Database, Table, View


def get_database(path: Path) -> Database:
    """Get the database object from the path."""
    return Database(path)


def get_table(table_name: str, *, db: Database) -> Table:
    """Get the table object from the database."""
    if table_name not in db.table_names():
        raise ValueError(f"Table {table_name} does not exist in database")

    return db.table(table_name)  # type: ignore


def get_view(view_name: str, *, db: Database) -> View:
    """Get the view object from the database."""
    if view_name not in db.view_names():
        raise ValueError(f"View {view_name} does not exist in database")

    return db.table(view_name)  # type: ignore
