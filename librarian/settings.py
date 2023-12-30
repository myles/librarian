from os import environ
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Settings for the librarian project.
    """

    ROOT_PATH = Path(__file__).parent.parent

    DBS_PATH = ROOT_PATH / "dbs"
    DATA_PATH = ROOT_PATH / "data"

    # Books Collection
    BOOK_DB_PATH = DBS_PATH / "books.db"

    # Vinyl Collection
    VINYL_DB_PATH = DBS_PATH / "vinyl.db"

    # Integrations
    DISCOGS_PERSONAL_ACCESS_TOKEN = environ.get(
        "LIBRARIAN_INTEGRATIONS_DISCOGS_PERSONAL_ACCESS_TOKEN",
        None,
    )
    GENIUS_CLIENT_ACCESS_TOKEN = environ.get(
        "LIBRARIAN_INTEGRATIONS_GENIUS_CLIENT_ACCESS_TOKEN",
        None,
    )
