import datetime
import re
from itertools import islice
from typing import Any, Dict, Generator, List, Optional

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
    tracks_table: Table = db.table("tracks")  # type: ignore
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
                "isbn": str,
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

    if tracks_table.exists() is False:
        tracks_table.create(
            columns={
                "id": int,
                "vinyl_record_id": int,
                "title": str,
                "position": str,
                "duration": int,
                "created_at": datetime.datetime,
                "updated_at": datetime.datetime,
            },
            pk="id",
            foreign_keys=(("vinyl_record_id", "vinyl_records", "id"),),
            defaults={"created_at": datetime.datetime.utcnow()},
        )
        tracks_table.enable_fts(["title"], create_triggers=True)

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
                "profile": str,
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


def query_releases_on_discogs_matching_isbn(
    isbn: str, client: Optional[discogs.DiscogsClient] = None
) -> List[discogs.DiscogsSearchResult]:
    """
    Query all the releases on Discogs matching an ISBN and return the top 10
    matching results.
    """
    if client is None:
        client = discogs.DiscogsClient()

    return list(islice(client.search(type="release", barcode=isbn), 10))


def does_discogs_release_match_isbn(
    release: discogs.DiscogsRelease, isbn: str
) -> bool:
    """
    Does the Discogs release's barcode match the given ISBN?
    """
    # If the release does not have a known barcode then return False.
    if release.barcode is None:
        return False

    barcode = re.sub(r"[^.0-9]", "", release.barcode)
    return isbn in barcode


def get_discogs_release_by_isbn(
    isbn: str, client: Optional[discogs.DiscogsClient] = None
) -> Optional[discogs.DiscogsRelease]:
    """
    Get a Discogs release by an ISBN.
    """
    search_results = query_releases_on_discogs_matching_isbn(
        isbn=isbn, client=client
    )

    for result in search_results:
        release = get_release_from_discogs(result.id, client=client)
        if does_discogs_release_match_isbn(release, isbn) is True:
            return release


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
    artist: discogs.DiscogsArtistBase,
    existing_artist_id: Optional[int],
) -> Dict[str, Any]:
    """
    Transform a DiscogsArtist or DiscogsArtistMember dataclass to something
    that can be safely inserted to the vinyl table on the database.
    """
    record: Dict[str, Any] = {
        "id": existing_artist_id,
        "discogs_artist_id": artist.id,
        "updated_at": datetime.datetime.utcnow(),
    }

    if hasattr(artist, "name"):
        record["name"] = artist.name

    if hasattr(artist, "profile"):
        record["profile"] = artist.profile

    return record


def upsert_artist_from_discogs_artist(
    artist: discogs.DiscogsArtistBase,
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

    return table.get(table.last_pk)  # type: ignore


def upsert_discogs_artist(
    artist: discogs.DiscogsArtist,
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
    return table.get(table.last_pk)  # type: ignore


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
        "isbn": release.barcode,
        "title": release.title,
        "year": release.year,
        "discogs_release_id": release.id,
        "updated_at": datetime.datetime.utcnow(),
    }
    return record


def transform_discogs_release_track(
    track: discogs.DiscogsReleaseTrack,
    existing_track_id: Optional[int],
    vinyl_record_id: int,
) -> Dict[str, Any]:
    """
    Transform a DiscogsReleaseTrack to something that can be safely
    inserted to the vinyl table on the database.
    """
    record = {
        "id": existing_track_id,
        "vinyl_record_id": vinyl_record_id,
        "title": track.title,
        "position": track.position,
        "duration": track.duration,
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
    return table.get(table.last_pk)  # type: ignore


def upsert_vinyl_from_discogs_release(
    release: discogs.DiscogsRelease,
    artist_rows: List[Dict[str, Any]],
    db: Database,
) -> Dict[str, Any]:
    """
    Upsert a vinyl into the SQLite database.
    """
    vinyl_records_table: Table = db.table("vinyl_records")  # type: ignore
    vinyl_records_artists_table: Table = db.table(
        "vinyl_records_artists",
    )  # type: ignore

    existing_vinyl_record_ids = list(
        vinyl_records_table.pks_and_rows_where(
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
        table = vinyl_records_table.insert(record=record)
    else:
        table = vinyl_records_table.upsert(record, pk="id")

    row = table.get(table.last_pk)  # type: ignore

    vinyl_records_artists_table.upsert_all(
        records=[
            {"vinyl_record_id": row["id"], "artist_id": artist_row["id"]}
            for artist_row in artist_rows
        ],
        pk=["vinyl_record_id", "artist_id"],
    )

    return row


def upsert_tracks_from_discogs_release(
    release: discogs.DiscogsRelease,
    vinyl_record_id: int,
    db: Database,
):
    """
    Upset tracks rows into the SQLite database.
    """
    tracks_table: Table = db.table("tracks")  # type: ignore

    existing_track_rows = list(
        tracks_table.rows_where(
            where="vinyl_record_id = :vinyl_record_id",
            where_args={"vinyl_record_id": vinyl_record_id},
        )
    )

    insert_records = []
    upsert_records = []

    for track in release.tracks:
        existing_track = next(
            filter(
                lambda row: row["position"] == track.position,
                existing_track_rows,
            ),
            None,
        )
        transformed_track = transform_discogs_release_track(
            track,
            existing_track_id=existing_track["id"] if existing_track else None,
            vinyl_record_id=vinyl_record_id,
        )

        if transformed_track["id"] is None:
            insert_records.append(transformed_track)
        else:
            upsert_records.append(transformed_track)

    if insert_records:
        tracks_table.insert_all(records=insert_records)

    if upsert_records:
        tracks_table.upsert_all(records=upsert_records, pk="id")


def list_artists(db: Database) -> Generator[Dict[str, Any], None, None]:
    """
    Returns a list of books in the SQLite database.
    """
    table = db.table("artists")
    return table.rows
