from typing import Optional

import click
from sqlite_utils import Database

from ...integrations.discogs import DiscogsClient
from ...settings import Settings
from . import service


@click.group()
def cli():
    """Inventory the library's vinyl record collection."""


@cli.command(name="add")
@click.option(
    "--isbn",
    help="ISBN of the vinyl record.",
    default=None,
    type=str,
)
@click.option(
    "--discogs-release-id",
    help="Discogs release ID of the vinyl record.",
    default=None,
    type=int,
)
def add_vinyl(
    isbn: Optional[str] = None, discogs_release_id: Optional[int] = None
):
    """Add a vinyl record to the library's collection."""
    db = Database(Settings.VINYL_DB_PATH)
    service.build_database(db)

    client = DiscogsClient()

    if isbn is not None:
        search_results = service.query_releases_on_discogs_matching_isbn(
            isbn=isbn, client=client
        )

        for result in search_results:
            release = service.get_release_from_discogs(result.id, client=client)

            if service.does_discogs_release_match_isbn(release, isbn) is True:
                break
        else:
            raise click.ClickException(
                f"We couldn't find a Discogs Release by the ISBN {isbn}."
            )
    elif discogs_release_id is not None:
        release = service.get_release_from_discogs(
            discogs_release_id, client=client
        )
    else:
        raise click.ClickException(
            "Please provided ether an ISBN or Discogs Release ID."
        )

    service.upsert_discogs_release(release, db)

    artist_rows = []
    for artist in release.artists:
        artist_row = service.upsert_artist_from_discogs_artist(
            artist=artist, db=db
        )
        artist_rows.append(artist_row)

    service.upsert_vinyl_from_discogs_release(release, artist_rows, db)


@cli.command()
def update_artists():
    """
    Update all the artists in the DB.
    """
    db = Database(Settings.VINYL_DB_PATH)
    service.build_database(db)

    client = DiscogsClient()

    artist_row = service.list_artists(db)

    artists_band_members = []
    for artist_row in artist_row:
        artist = client.get_artist(artist_row["discogs_artist_id"])
        service.upsert_discogs_artist(artist, db)
        artist_row = service.upsert_artist_from_discogs_artist(artist, db)

        for member in artist.members:
            member_row = service.upsert_artist_from_discogs_artist(member, db)
            artists_band_members.append(
                (artist_row["id"], member_row["id"], member.is_active)
            )

    records = [
        {
            "artist_band_id": artist_band_id,
            "artist_member_id": artist_member_id,
            "is_active": is_active,
        }
        for artist_band_id, artist_member_id, is_active in artists_band_members
    ]
    db["bands_members"].upsert_all(
        records, pk=["artist_band_id", "artist_member_id"]
    )
