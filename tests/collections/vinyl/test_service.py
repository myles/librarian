import pytest

from librarian.collections.vinyl import service
from librarian.integrations.discogs import (
    DiscogsArtist,
    DiscogsArtistMember,
    DiscogsRelease,
    DiscogsReleaseArtist,
)

from ...integrations.discogs import discogs_responses


def test_build_database(mock_db):
    service.build_database(mock_db)

    assert mock_db["vinyl_records"].exists() is True
    assert mock_db["styles"].exists() is True

    assert mock_db["artists"].exists() is True
    assert mock_db["vinyl_records_artists"].exists() is True
    assert mock_db["bands_members"].exists() is True

    assert mock_db["discogs_releases"].exists() is True
    assert mock_db["discogs_artists"].exists() is True


@pytest.mark.parametrize(
    "release_barcode, isbn, expected_result",
    (
        ("6 5660-50401-3 4", "566050401", True),
        ("7 69791 98182 9", "6979198182", True),
        (None, "123456789", False),
    ),
)
def test_does_discogs_release_match_isbn(
    release_barcode, isbn, expected_result
):
    release = DiscogsRelease(
        id=1234567890,
        title="Hello, World!",
        year=2023,
        barcode=release_barcode,
    )

    result = service.does_discogs_release_match_isbn(release=release, isbn=isbn)
    assert result == expected_result


def test_transform_discogs_artist__discogs_artist():
    artist = DiscogsArtist.from_data(discogs_responses.DISCOGS_ARTIST)

    transformed_artist = service.transform_discogs_artist(
        artist, existing_artist_id=123
    )
    assert len(transformed_artist.keys()) == 4
    assert transformed_artist["id"] == 123
    assert transformed_artist["discogs_artist_id"] == artist.id
    assert "updated_at" in transformed_artist
    assert transformed_artist["profile"] == artist.profile


def test_transform_discogs_artist__discogs_release_member():
    artist = DiscogsReleaseArtist.from_data(
        discogs_responses.DISCOGS_RELEASE_ARTIST
    )

    transformed_artist = service.transform_discogs_artist(
        artist, existing_artist_id=None
    )
    assert len(transformed_artist.keys()) == 4
    assert transformed_artist["id"] is None
    assert transformed_artist["discogs_artist_id"] == artist.id
    assert "updated_at" in transformed_artist
    assert transformed_artist["name"] == artist.name


def test_transform_discogs_artist__discogs_artist_member():
    artist = DiscogsArtistMember.from_data(
        discogs_responses.DISCOGS_ARTIST_MEMBER
    )

    transformed_artist = service.transform_discogs_artist(
        artist, existing_artist_id=None
    )
    assert len(transformed_artist.keys()) == 4
    assert transformed_artist["id"] is None
    assert transformed_artist["discogs_artist_id"] == artist.id
    assert "updated_at" in transformed_artist
    assert transformed_artist["name"] == artist.name
