import responses

from librarian.integrations.openlibrary import service

from . import openlibrary_responses


@responses.activate
def test_open_library_client__get_book_from_isbn():
    response_data = openlibrary_responses.BOOK_RESPONSE.copy()

    # Querying OpenLibrary's ISBN endpoint will redirect you to the Books
    # endpoint.
    first_url = "https://openlibrary.org/isbn/0140328726.json"
    second_url = "https://openlibrary.org/books/OL7353617M.json"

    first_response = responses.Response(
        method="GET",
        url=first_url,
        status=301,
        headers={"Location": second_url},
    )
    responses.add(first_response)

    second_response = responses.Response(
        method="GET",
        url=second_url,
        json=response_data,
    )
    responses.add(second_response)

    client = service.OpenLibraryClient()
    book = client.get_book_from_isbn(isbn="0140328726")

    assert book.title == response_data["title"]


@responses.activate
def test_open_library_client__get_author():
    response_data = openlibrary_responses.AUTHOR_RESPONSE.copy()

    url = "https://openlibrary.org/authors/OL34184A.json"

    response = responses.Response(
        method="GET",
        url=url,
        json=response_data,
    )
    responses.add(response)

    client = service.OpenLibraryClient()
    author = client.get_author(key="OL34184A")

    assert author.name == response_data["name"]


@responses.activate
def test_open_library_client__get_work():
    response_data = openlibrary_responses.WORK_RESPONSE.copy()

    url = "https://openlibrary.org/works/OL45804W.json"

    response = responses.Response(
        method="GET",
        url=url,
        json=response_data,
    )
    responses.add(response)

    client = service.OpenLibraryClient()
    work = client.get_work(key="OL45804W")

    assert work.title == response_data["title"]
