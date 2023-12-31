import pytest
import responses

from librarian.collections.books import cli

from ...integrations.openlibrary import openlibrary_responses


@responses.activate
def test_add_book(mocker, cli_runner, mock_db):
    mocker.patch(
        "librarian.collections.books.cli.get_database",
        return_value=mock_db,
    )

    responses.add(
        responses.Response(
            method="GET",
            url="https://openlibrary.org/isbn/0140328726.json",
            json=openlibrary_responses.BOOK_RESPONSE,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url="https://openlibrary.org/works/OL45804W.json",
            json=openlibrary_responses.WORK_RESPONSE,
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url="https://openlibrary.org/authors/OL34184A.json",
            json=openlibrary_responses.AUTHOR_RESPONSE,
        )
    )

    assert mock_db["books"].exists() is False
    assert mock_db["authors"].exists() is False

    cli_runner.invoke(cli.add_book, "--isbn=0140328726")
    cli_runner.invoke(cli.add_book, "--isbn=0140328726")

    assert mock_db["books"].count == 1
    assert mock_db["authors"].count == 1


@pytest.mark.parametrize("output_format", ("csv", "json", "markdown"))
def test_list_books(output_format, mocker, cli_runner, mock_db):
    mocker.patch(
        "librarian.collections.books.cli.get_database",
        return_value=mock_db,
    )

    cli_runner.invoke(cli.list_books, f"--format {output_format}")
