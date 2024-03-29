import pytest
import responses
from responses.matchers import query_param_matcher

from librarian.integrations.genius import service
from librarian.settings import Settings

from . import genius_responses


@responses.activate
def test_genius_client(mocker):
    url = "https://api.genius.com/example"
    client_access_token = "123abc456def789ghi"

    mocker.patch.object(
        Settings,
        "GENIUS_CLIENT_ACCESS_TOKEN",
        client_access_token,
    )

    responses.add(responses.Response(method="GET", url=url))

    client = service.GeniusClient()
    request, _ = client.request(method="GET", url=url)

    assert "Authorization" in request.headers
    assert request.headers["Authorization"] == f"Bearer {client_access_token}"


@responses.activate
@pytest.mark.parametrize(
    "text_format, expected_text_format_parma",
    (("html", "html"), (["dom", "plain", "html"], "dom,plain,html")),
)
def test_genius_client__get_song(text_format, expected_text_format_parma):
    song_id = 378195

    responses.add(
        responses.Response(
            method="GET",
            url=f"https://api.genius.com/songs/{song_id}",
            match=[
                query_param_matcher(
                    {"text_format": expected_text_format_parma},
                    strict_match=True,
                )
            ],
            json=genius_responses.GENIUS_SONG,
        )
    )

    client = service.GeniusClient()
    song = client.get_song(song_id, text_format=text_format)

    assert song.id == song_id
