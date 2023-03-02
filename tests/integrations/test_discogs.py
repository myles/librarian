from copy import deepcopy

import responses

from librarian.integrations import discogs
from librarian.settings import Settings

from .. import discogs_responses


def test_discogs_image__from_data():
    data = deepcopy(discogs_responses.DISCOGS_RELEASE_IMAGE_PRIMARY)

    image = discogs.DiscogsImage.from_data(data)
    assert image.type == data["type"]
    assert image.height == data["height"]
    assert image.width == data["width"]
    assert image.resource_url == data["resource_url"]


def test_discogs_basic_artist__from_data():
    data = deepcopy(discogs_responses.DISCOGS_RELEASE_ARTIST)

    artist = discogs.DiscogsBasicArtist.from_data(data)
    assert artist.id == data["id"]
    assert artist.name == data["name"]


def test_discogs_release__from_data():
    data = deepcopy(discogs_responses.DISCOGS_RELEASE)

    release = discogs.DiscogsRelease.from_data(data)
    assert release.id == data["id"]
    assert release.title == data["title"]
    assert release.year == data["year"]
    assert release.artists[0].id == data["artists"][0]["id"]


def test_discogs_artist__from_data():
    data = deepcopy(discogs_responses.DISCOGS_ARTIST)

    artist = discogs.DiscogsArtist.from_data(data)
    assert artist.id == data["id"]
    assert artist.name_variations == data["namevariations"]
    assert artist.profile == data["profile"]


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

    client = discogs.DiscogsClient()
    request, _ = client.request(method="GET", url=url)

    assert "Authorization" in request.headers
    assert (
        request.headers["Authorization"]
        == f"Discogs token={personal_access_token}"
    )


@responses.activate
def test_discogs_client__get_release():
    response_data = deepcopy(discogs_responses.DISCOGS_RELEASE)
    release_id = response_data["id"]

    url = f"https://api.discogs.com/releases/{release_id}"

    responses.add(
        responses.Response(
            method="GET",
            url=url,
            json=response_data,
        )
    )

    client = discogs.DiscogsClient()
    release = client.get_release(release_id=release_id, currency="CAD")

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

    client = discogs.DiscogsClient()
    atrist = client.get_artist(artist_id=artist_id)

    assert atrist.id == response_data["id"]
