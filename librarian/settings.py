from pathlib import Path


class Settings:
    """
    Settings for the librarian project.
    """

    ROOT_PATH = Path(__file__).parent.parent

    DBS_PATH = ROOT_PATH / "dbs"
    DATA_PATH = ROOT_PATH / "data"

    # Books Collection
    BOOK_DB_PATH = DBS_PATH / "books.db"
    BOOKS_DATA_PATH = DATA_PATH / "books.json"
