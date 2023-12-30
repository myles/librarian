from importlib.metadata import version

import pytest
import responses

from librarian.utils import http_client


@responses.activate
@pytest.mark.parametrize("method", ("GET", "POST", "PATCH", "DELETE", "PUT"))
def test_http_client__request(method: http_client.MethodLiterals):
    url = "https://example.com/"

    responses.add(responses.Response(method=str(method), url=url))

    client = http_client.HttpClient()
    client.request(method=method, url=url)

    request = responses.calls[0].request  # type: ignore

    expected_user_agent = (
        f"librarian/{version('librarian')}"
        f" (+https://library.mylesbraithwaite.com/)"
    )
    assert "User-Agent" in request.headers
    assert request.headers["User-Agent"] == expected_user_agent


@responses.activate
@pytest.mark.parametrize(
    "class_function_name, http_method",
    (
        ("get", "GET"),
        ("post", "POST"),
        ("patch", "PATCH"),
        ("delete", "DELETE"),
        ("put", "PUT"),
    ),
)
def test_http_client__class_functions(
    class_function_name: str, http_method: http_client.MethodLiterals
):
    url = "https://example.com/"

    responses.add(responses.Response(method=str(http_method), url=url))

    client = http_client.HttpClient()
    getattr(client, class_function_name)(url=url)

    request = responses.calls[0].request  # type: ignore

    assert request.url == url
    assert request.method == http_method
