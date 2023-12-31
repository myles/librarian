from copy import deepcopy

import pytest

from librarian.integrations.discogs import data

from . import discogs_responses


@pytest.mark.parametrize(
    "value, expected_result",
    (
        ("1:00", 60),
        ("1:30", 90),
    ),
)
def test_transform_duration(value, expected_result):
    result = data.transform_duration(value)
    assert result == expected_result


def test_discogs_image__from_data():
    payload = deepcopy(discogs_responses.DISCOGS_RELEASE_IMAGE_PRIMARY)

    image = data.DiscogsImage.from_data(payload)
    assert image.type == payload["type"]
    assert image.height == payload["height"]
    assert image.width == payload["width"]
    assert image.resource_url == payload["resource_url"]


def test_discogs_member_artist__from_data():
    payload = deepcopy(discogs_responses.DISCOGS_ARTIST_MEMBER)

    artist = data.DiscogsArtistMember.from_data(payload)
    assert artist.id == payload["id"]
    assert artist.name == payload["name"]
    assert artist.is_active is payload["active"]


def test_discogs_artist__from_data():
    payload = deepcopy(discogs_responses.DISCOGS_ARTIST)

    artist = data.DiscogsArtist.from_data(payload)
    assert artist.id == payload["id"]
    assert artist.name_variations == payload["namevariations"]
    assert artist.profile == payload["profile"]
    assert len(artist.members) == len(payload["members"])


def test_discogs_release_track_artist__from_data():
    payload = deepcopy(discogs_responses.DISCOGS_RELEASE_TRACK_ARTIST)

    artist = data.DiscogsReleaseTrackArtist.from_data(payload)
    assert artist.id == payload["id"]
    assert artist.name == payload["name"]
    assert artist.role == payload["role"]


def test_discogs_release_track__from_data():
    payload = deepcopy(discogs_responses.DISCOGS_RELEASE_TRACK)

    track = data.DiscogsReleaseTrack.from_data(payload)
    assert track.title == payload["title"]
    assert track.duration == data.transform_duration(payload["duration"])
    assert track.position == payload["position"]


@pytest.mark.parametrize(
    "identifiers, expected_barcode",
    (
        ([{"type": "Barcode", "value": "5012394144777"}], "5012394144777"),
        ([{"type": "Barcode", "value": ""}], None),
        ([], None),
    ),
)
def test_discogs_release__from_data(identifiers, expected_barcode):
    payload = deepcopy(discogs_responses.DISCOGS_RELEASE)
    payload["identifiers"] = identifiers

    release = data.DiscogsRelease.from_data(payload)
    assert release.id == payload["id"]
    assert release.title == payload["title"]
    assert release.year == payload["year"]
    assert release.artists[0].id == payload["artists"][0]["id"]
    assert release.barcode == expected_barcode
    assert release.tracks[0].title == payload["tracklist"][0]["title"]


def test_discogs_search_result__from_data():
    payload = deepcopy(discogs_responses.DISCOGS_SEARCH_RESULT_ONE)

    search_result = data.DiscogsSearchResult.from_data(payload)
    assert search_result.id == payload["id"]
    assert search_result.type == payload["type"]
    assert search_result.title == payload["title"]
    assert search_result.url == f"https://discogs.com{payload['uri']}"
