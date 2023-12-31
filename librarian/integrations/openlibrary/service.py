from typing import Optional

from requests import Session

from ...utils.http_client import HttpClient
from . import data


class OpenLibraryClient(HttpClient):
    def __init__(self, session: Optional[Session] = None):
        super().__init__(session=session)

        self.base_url = "https://openlibrary.org"

    def get_book_from_isbn(self, isbn: str, **kwargs) -> data.OpenLibraryBook:
        """
        Get a book from the OpenLibrary API using its ISBN.
        """
        url = f"{self.base_url}/isbn/{isbn}.json"

        _request, response = self.get(url=url, **kwargs)
        response.raise_for_status()
        response_data = response.json()

        return data.OpenLibraryBook.from_data(response_data)

    def get_author(self, key: str, **kwargs) -> data.OpenLibraryAuthor:
        """
        Get an author from the OpenLibrary API using its key.
        """
        url = f"{self.base_url}/authors/{key}.json"

        _request, response = self.get(url=url, **kwargs)
        response.raise_for_status()
        response_data = response.json()

        return data.OpenLibraryAuthor.from_data(response_data)

    def get_work(self, key: str, **kwargs) -> data.OpenLibraryWork:
        """
        Get a work from OpenLibrary API using its key.
        """
        url = f"{self.base_url}/works/{key}.json"

        _request, response = self.get(url=url, **kwargs)
        response.raise_for_status()
        response_data = response.json()

        return data.OpenLibraryWork.from_data(response_data)
