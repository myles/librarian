import datetime
import re
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytz
from dateutil.parser import parse as dateutil_parse
from requests import Session

from ..utils.http_client import HttpClient


def format_date(value: Optional[str]) -> Optional[datetime.date]:
    """
    Convert an Open Library date to a Python date object.
    """
    if value is None or value.strip() == "":
        return None

    try:
        return datetime.datetime.strptime(value, "%B %d, %Y").date()
    except ValueError:
        default = datetime.datetime(2023, 1, 1)
        return dateutil_parse(value, default=default).date()


def format_datetime(value: Optional[str]) -> Optional[datetime.datetime]:
    """
    Convert an Open Library datetime to a Python timezone aware datetime
    object.
    """
    if value is None or value.strip() == "":
        return None

    return pytz.UTC.fromutc(datetime.datetime.fromisoformat(value))


RE_KEY = re.compile(r"^/(?P<key_type>\w+)/(?P<key>\w+)$")


def format_key(string: str) -> str:
    """
    Convert an Open Library key object to Python string.
    """
    match = RE_KEY.match(string)

    if match is None:
        raise ValueError(
            "Cannot extract the key because the provided string is malformed."
        )

    return match.groupdict()["key"]


def format_key_list(data: List[Dict[str, str]]) -> List[str]:
    """
    Convert a list of Open Library key objects to a Python list of strings.
    """
    return [format_key(key["key"]) for key in data]


@dataclass
class OpenLibraryBook:
    title: str
    key: str
    publish_date: datetime.date

    isbn_10: List[str] = field(default_factory=list)
    isbn_13: List[str] = field(default_factory=list)

    type_key: str = ""
    author_keys: List[str] = field(default_factory=list)
    language_keys: List[str] = field(default_factory=list)
    work_keys: List[str] = field(default_factory=list)

    publishers: List[str] = field(default_factory=list)
    number_of_pages: Optional[int] = None
    covers: List[int] = field(default_factory=list)
    ocaid: Optional[str] = None
    contributions: List[str] = field(default_factory=list)
    classifications: Dict[str, Any] = field(default_factory=dict)
    source_records: List[str] = field(default_factory=list)
    identifiers: Dict[str, List[str]] = field(default_factory=dict)
    local_id: List[str] = field(default_factory=list)
    first_sentence: str = ""
    latest_revision: Optional[int] = None
    revision: Optional[int] = None
    created: Optional[datetime.datetime] = None
    last_modified: Optional[datetime.datetime] = None

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = (
            "title",
            "publish_date",
            "isbn_10",
            "isbn_13",
            "key",
            "type",
            "authors",
            "languages",
            "works",
            "publishers",
            "number_of_pages",
            "covers",
            "ocaid",
            "contributions",
            "classifications",
            "source_records",
            "identifiers",
            "local_id",
            "first_sentence",
            "latest_revision",
            "revision",
            "created",
            "last_modified",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["key"] = format_key(defaults.pop("key"))
        defaults["publish_date"] = format_date(defaults.pop("publish_date"))
        defaults["type_key"] = format_key(defaults.pop("type")["key"])
        defaults["author_keys"] = format_key_list(defaults.pop("authors", []))
        defaults["language_keys"] = format_key_list(
            defaults.pop("languages", [])
        )

        if "works" in defaults:
            defaults["work_keys"] = format_key_list(defaults.pop("works"))

        if "first_sentence" in defaults:
            defaults["first_sentence"] = defaults.pop("first_sentence")["value"]

        defaults["created"] = format_datetime(defaults.pop("created")["value"])
        defaults["last_modified"] = format_datetime(
            defaults.pop("last_modified")["value"]
        )

        return cls(**defaults, data=data)


@dataclass
class OpenLibraryWork:
    title: str
    key: str
    type_key: str = "work"

    author_keys: List[str] = field(default_factory=list)
    description: str = ""
    covers: List[int] = field(default_factory=list)

    subjects: List[str] = field(default_factory=list)
    subject_people: List[str] = field(default_factory=list)
    subject_places: List[str] = field(default_factory=list)
    subject_times: List[str] = field(default_factory=list)

    location: Optional[str] = None
    latest_revision: Optional[int] = None
    revision: Optional[int] = None
    created: Optional[datetime.datetime] = None
    last_modified: Optional[datetime.datetime] = None

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = (
            "title",
            "key",
            "type",
            "authors",
            "description",
            "covers",
            "subject_places",
            "subjects",
            "subject_people",
            "subject_times",
            "location",
            "latest_revision",
            "revision",
            "created",
            "last_modified",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["key"] = format_key(defaults.pop("key"))
        defaults["type_key"] = format_key(defaults.pop("type")["key"])

        authors = defaults.pop("authors", [])
        defaults["author_keys"] = []
        for author in authors:
            defaults["author_keys"].append(format_key(author["author"]["key"]))

        description = defaults.pop("description", "")
        if isinstance(description, dict) is True:
            defaults["description"] = description["value"]
        elif isinstance(description, str) is True:
            defaults["description"] = description

        if "location" in defaults:
            defaults["location"] = format_key(defaults.pop("location"))

        return cls(**defaults, data=data)


@dataclass
class OpenLibraryLink:
    url: str
    title: str
    type_key: str

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        data["type_key"] = format_key(data.pop("type")["key"])

        safe_keys = ("url", "title", "type_key")
        to_remove = [k for k in data.keys() if k not in safe_keys]
        for key in to_remove:
            del data[key]

        return cls(**data)


@dataclass
class OpenLibraryAuthor:
    key: str
    name: str
    type_key: str = "author"

    personal_name: str = ""
    bio: str = ""
    birth_date: Optional[datetime.date] = None
    death_date: Optional[datetime.date] = None
    remote_ids: Dict[str, List[str]] = field(default_factory=dict)
    links: List[OpenLibraryLink] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)
    source_records: List[str] = field(default_factory=list)
    latest_revision: Optional[int] = None
    revision: Optional[int] = None
    created: Optional[datetime.datetime] = None
    last_modified: Optional[datetime.datetime] = None

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = (
            "key",
            "name",
            "personal_name",
            "bio",
            "birth_date",
            "death_date",
            "remote_ids",
            "links",
            "type",
            "photos",
            "source_records",
            "latest_revision",
            "revision",
            "created",
            "last_modified",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["key"] = format_key(defaults.pop("key"))
        defaults["type_key"] = format_key(defaults.pop("type")["key"])

        if "birth_date" in defaults:
            defaults["birth_date"] = format_date(defaults.pop("birth_date"))

        if "death_date" in defaults:
            defaults["death_date"] = format_date(defaults.pop("death_date"))

        if "created" in defaults:
            defaults["created"] = format_datetime(
                defaults.pop("created")["value"]
            )

        if "last_modified" in defaults:
            defaults["last_modified"] = format_datetime(
                defaults.pop("last_modified")["value"]
            )

        if "links" in defaults:
            defaults["links"] = [
                OpenLibraryLink.from_data(link) for link in defaults["links"]
            ]

        return cls(**defaults, data=data)


class OpenLibraryClient(HttpClient):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(session=session)

        self.base_url = "https://openlibrary.org"

    def get_book_from_isbn(self, isbn: str, **kwargs) -> OpenLibraryBook:
        """
        Get a book from the OpenLibrary API using its ISBN.
        """
        url = f"{self.base_url}/isbn/{isbn}.json"

        _request, response = self.request(method="GET", url=url, **kwargs)
        response.raise_for_status()
        data = response.json()

        return OpenLibraryBook.from_data(data)

    def get_author(self, key: str, **kwargs) -> OpenLibraryAuthor:
        """
        Get an author from the OpenLibrary API using its key.
        """
        url = f"{self.base_url}/authors/{key}.json"

        _request, response = self.request(method="GET", url=url, **kwargs)
        response.raise_for_status()
        data = response.json()

        return OpenLibraryAuthor.from_data(data)

    def get_work(self, key: str, **kwargs) -> OpenLibraryWork:
        """
        Get a work from OpenLibrary API using its key.
        """
        url = f"{self.base_url}/works/{key}.json"

        _request, response = self.request(method="GET", url=url, **kwargs)
        response.raise_for_status()
        data = response.json()

        return OpenLibraryWork.from_data(data)
