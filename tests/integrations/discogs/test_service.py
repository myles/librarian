from copy import deepcopy
from urllib.parse import urlencode

import pytest
import responses
from responses.matchers import query_param_matcher

from librarian.integrations.discogs import service
from librarian.settings import Settings

from . import discogs_responses


@responses.activate
def test_discogs_client(mocker):
    url = "https://api.discogs.com/example"
    personal_access_token = "123abc456def789ghi"

    mocker.patch.object(
        Settings,
        "DISCOGS_PERSONAL_ACCESS_TOKEN",
        personal_access_token,
    )

    responses.add(responses.Response(method="GET", url=url))

    client = service.DiscogsClient()
    request, _ = client.request(method="GET", url=url)

    assert "Authorization" in request.headers
    assert (
        request.headers["Authorization"]
        == f"Discogs token={personal_access_token}"
    )


@responses.activate
@pytest.mark.parametrize("currency", (None, "USD", "CAD"))
def test_discogs_client__get_release(currency):
    response_data = deepcopy(discogs_responses.DISCOGS_RELEASE)
    release_id = response_data["id"]

    url = f"https://api.discogs.com/releases/{release_id}"

    match = []
    if currency is not None:
        match.append(
            query_param_matcher({"curr_abbr": currency}, strict_match=True)
        )

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            json=response_data,
            match=match,
        )
    )

    client = service.DiscogsClient()
    release = client.get_release(release_id=release_id, currency=currency)

    assert release.id == response_data["id"]
    assert release.title == response_data["title"]


@responses.activate
def test_discogs_client__get_artist():
    response_data = deepcopy(discogs_responses.DISCOGS_ARTIST)
    artist_id = response_data["id"]

    url = f"https://api.discogs.com/artists/{artist_id}"

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            json=response_data,
        )
    )

    client = service.DiscogsClient()
    atrist = client.get_artist(artist_id=artist_id)

    assert atrist.id == response_data["id"]


@responses.activate
@pytest.mark.parametrize(
    "query, type, barcode, request_query",
    (
        (
            "nirvana",
            None,
            None,
            {"query": "nirvana"},
        ),
        (
            "nirvana",
            "release",
            None,
            {"query": "nirvana", "type": "release"},
        ),
        (
            None,
            None,
            "i-am-a-barcode",
            {"barcode": "i-am-a-barcode"},
        ),
    ),
)
def test_discogs_client__search(query, type, barcode, request_query):
    result_one = deepcopy(discogs_responses.DISCOGS_SEARCH_RESULT_ONE)
    result_two = deepcopy(discogs_responses.DISCOGS_SEARCH_RESULT_TWO)

    first_response_url = "https://api.discogs.com/database/search"
    second_response_url = f"https://api.discogs.com/database/search?per_page=1&page=2&{urlencode(request_query)}"

    responses.add(
        responses.Response(
            method="GET",
            url=first_response_url,
            json={
                "pagination": {
                    "per_page": 1,
                    "pages": 2,
                    "page": 1,
                    "urls": {"next": second_response_url},
                },
                "results": [result_one],
            },
            match=[query_param_matcher(request_query, strict_match=True)],
        )
    )
    responses.add(
        responses.Response(
            method="GET",
            url=second_response_url,
            json={
                "pagination": {
                    "per_page": 1,
                    "pages": 2,
                    "page": 2,
                    "urls": {},
                },
                "results": [result_two],
            },
            match=[
                query_param_matcher(
                    {**request_query, "per_page": 1, "page": 2},
                    strict_match=True,
                )
            ],
        )
    )

    client = service.DiscogsClient()
    results = list(client.search(query=query, type=type, barcode=barcode))

    assert len(results) == 2
    first_result, second_result = results
    assert first_result.id == result_one["id"]
    assert second_result.id == result_two["id"]
