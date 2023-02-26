import responses

from librarian.collections.books import cli

from ...openlibrary_responses import AUTHOR_RESPONSE, BOOK_RESPONSE


@responses.activate
def test_add_book(mocker, cli_runner, mock_db):
    mocker.patch(
        "librarian.collections.books.cli.Database",
        return_value=mock_db,
    )

    responses.add(
        responses.Response(
            method="GET",
            url="https://openlibrary.org/isbn/0140328726.json",
            json=BOOK_RESPONSE,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url="https://openlibrary.org/authors/OL34184A.json",
            json=AUTHOR_RESPONSE,
        )
    )

    assert mock_db["books"].exists() is False
    assert mock_db["authors"].exists() is False

    cli_runner.invoke(cli.add_book, "--isbn=0140328726")

    assert mock_db["books"].count == 1
    assert mock_db["authors"].count == 1
