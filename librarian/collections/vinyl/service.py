import datetime
from typing import Any, Dict, Generator, List, Optional, Union

from sqlite_utils.db import Database, Table

from ...integrations import discogs


def build_database(db: Database):
    """
    Build the SQLite database for the vinyl records' library.
    """
    discogs_releases_table: Table = db.table("discogs_releases")  # type: ignore
    discogs_artists_table: Table = db.table("discogs_artists")  # type: ignore

    if discogs_releases_table.exists() is False:
        discogs_releases_table.create(
            columns={
                "id": int,
                "data": str,
                "updated_at": datetime.datetime,
            },
            pk="id",
        )

    if discogs_artists_table.exists() is False:
        discogs_artists_table.create(
            columns={
                "id": int,
                "data": str,
                "updated_at": datetime.datetime,
            },
            pk="id",
        )

    vinyl_records_table: Table = db.table("vinyl_records")  # type: ignore
    styles_table: Table = db.table("styles")  # type: ignore

    artists_table: Table = db.table("artists")  # type: ignore
    vinyl_records_artists_table: Table = db.table(
        "vinyl_records_artists",
    )  # type: ignore
    bands_members_table: Table = db.table("bands_members")  # type: ignore

    if vinyl_records_table.exists() is False:
        vinyl_records_table.create(
            columns={
                "id": int,
                "title": str,
                "year": int,
                "discogs_release_id": int,
                "created_at": datetime.datetime,
                "updated_at": datetime.datetime,
            },
            pk="id",
            foreign_keys=(("discogs_release_id", "discogs_releases", "id"),),
            defaults={"created_at": datetime.datetime.utcnow()},
        )
        vinyl_records_table.enable_fts(["title"], create_triggers=True)

    if styles_table.exists() is False:
        styles_table.create(
            columns={"id": int, "name": str},
            pk="id",
        )
        styles_table.enable_fts(["name"], create_triggers=True)

    if artists_table.exists() is False:
        artists_table.create(
            columns={
                "id": int,
                "name": str,
                "discogs_artist_id": int,
                "created_at": datetime.datetime,
                "updated_at": datetime.datetime,
            },
            pk="id",
            foreign_keys=(("discogs_artist_id", "discogs_artists", "id"),),
            defaults={"created_at": datetime.datetime.utcnow()},
        )
        artists_table.enable_fts(["name"], create_triggers=True)

    if vinyl_records_artists_table.exists() is False:
        vinyl_records_artists_table.create(
            columns={
                "vinyl_record_id": int,
                "artist_id": int,
            },
            pk=("vinyl_record_id", "artist_id"),
            foreign_keys=(
                ("vinyl_record_id", "vinyl_records", "id"),
                ("artist_id", "artists", "id"),
            ),
        )

    if bands_members_table.exists() is False:
        bands_members_table.create(
            columns={
                "artist_band_id": int,
                "artist_member_id": int,
                "is_active": bool,
            },
            pk=("artist_band_id", "artist_member_id"),
            foreign_keys=(
                ("artist_band_id", "artists", "id"),
                ("artist_member_id", "artists", "id"),
            ),
        )


def get_release_from_discogs(
    release_id: int, client: Optional[discogs.DiscogsClient] = None
) -> discogs.DiscogsRelease:
    """
    Get a release from Discogs' API.
    """
    if client is None:
        client = discogs.DiscogsClient()

    return client.get_release(release_id=release_id)


def transform_discogs_artist(
    artist: Union[discogs.DiscogsBasicArtist, discogs.DiscogsArtist],
    existing_artist_id: Optional[int],
) -> Dict[str, Any]:
    """
    Transform a DiscogsArtist or DiscogsBasicArtist dataclass to something
    that can be safely inserted to the vinyl table on the database.
    """
    record: Dict[str, Any] = {
        "id": existing_artist_id,
        "discogs_artist_id": artist.id,
        "updated_at": datetime.datetime.utcnow(),
    }

    if isinstance(artist, discogs.DiscogsBasicArtist) is True:
        record["name"] = artist.name

    return record


def upsert_artist_from_discogs_artist(
    artist: Union[discogs.DiscogsBasicArtist, discogs.DiscogsArtist],
    db: Database,
) -> Dict[str, Any]:
    """
    Upsert an artist into the SQLite database.
    """
    table: Table = db.table("artists")  # type: ignore

    existing_artist_ids = list(
        table.pks_and_rows_where(
            where="discogs_artist_id = :artist_id",
            where_args={"artist_id": artist.id},
        )
    )

    existing_artist_id: Optional[int] = None
    if existing_artist_ids:
        existing_artist_id, _ = existing_artist_ids[0]

    record = transform_discogs_artist(
        artist, existing_artist_id=existing_artist_id
    )

    if record["id"] is None:
        table = table.insert(record=record)
    else:
        table = table.upsert(record, pk="id")

    return table.get(table.last_pk)


def upsert_discogs_artist(
    artist: Union[discogs.DiscogsBasicArtist, discogs.DiscogsArtist],
    db: Database,
) -> Dict[str, Any]:
    """
    Upsert a discogs release into the SQLite database.
    """
    table: Table = db.table("discogs_artists")  # type: ignore
    table = table.upsert(
        {
            "id": artist.id,
            "data": artist.data,
            "updated_at": datetime.datetime.utcnow(),
        },
        pk="id",
    )
    return table.get(table.last_pk)


def transform_discogs_release_to_vinyl_record(
    release: discogs.DiscogsRelease,
    existing_vinyl_id: Optional[int],
) -> Dict[str, Any]:
    """
    Transform a DiscogsRelease dataclass to something that can be safely
    inserted to the vinyl table on the database.
    """
    record = {
        "id": existing_vinyl_id,
        "title": release.title,
        "year": release.year,
        "discogs_release_id": release.id,
        "updated_at": datetime.datetime.utcnow(),
    }

    return record


def upsert_discogs_release(
    release: discogs.DiscogsRelease,
    db: Database,
) -> Dict[str, Any]:
    """
    Upsert a discogs release into the SQLite database.
    """
    table: Table = db.table("discogs_releases")  # type: ignore
    table = table.upsert(
        {
            "id": release.id,
            "data": release.data,
            "updated_at": datetime.datetime.utcnow(),
        },
        pk="id",
    )
    return table.get(table.last_pk)


def upsert_vinyl_from_discogs_release(
    release: discogs.DiscogsRelease,
    artist_rows: List[Dict[str, Any]],
    db: Database,
) -> Dict[str, Any]:
    """
    Upsert a vinyl into the SQLite database.
    """
    table: Table = db.table("vinyl_records")  # type: ignore
    vinyl_records_artists_table: Table = db.table(
        "vinyl_records_artists",
    )  # type: ignore

    existing_vinyl_record_ids = list(
        table.pks_and_rows_where(
            where="discogs_release_id = :release_id",
            where_args={"release_id": release.id},
        )
    )

    existing_vinyl_record_id: Optional[int] = None
    if existing_vinyl_record_ids:
        existing_vinyl_record_id, _ = existing_vinyl_record_ids[0]

    record = transform_discogs_release_to_vinyl_record(
        release, existing_vinyl_id=existing_vinyl_record_id
    )

    if record["id"] is None:
        table = table.insert(record=record)
    else:
        table = table.upsert(record, pk="id")

    row = table.get(table.last_pk)

    vinyl_records_artists_table.upsert_all(
        records=[
            {"vinyl_record_id": row["id"], "artist_id": artist_row["id"]}
            for artist_row in artist_rows
        ],
        pk=["vinyl_record_id", "artist_id"],
    )

    return row


def list_artists(db: Database) -> Generator[Dict[str, Any], None, None]:
    """
    Returns a list of books in the SQLite database.
    """
    table = db.table("artists")
    return table.rows
