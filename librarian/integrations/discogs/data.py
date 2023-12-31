import typing as t
from copy import deepcopy
from dataclasses import dataclass, field

DiscogsCurrencyLiterals = t.Literal[
    "USD",
    "GBP",
    "EUR",
    "CAD",
    "AUD",
    "JPY",
    "CHF",
    "MXN",
    "BRL",
    "NZD",
    "SEK",
    "ZAR",
]

DiscogsTypeLiterals = t.Literal["release", "master", "artist", "label"]


def transform_duration(value: str) -> t.Optional[int]:
    """
    Format a Discogs duration type.
    """
    if not value:
        return None

    minutes, seconds = value.split(":")
    return (int(minutes) * 60) + int(seconds)


@dataclass
class DiscogsImage:
    type: t.Literal["primary", "secondary"]
    height: int
    width: int
    resource_url: str

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = ("type", "height", "width", "resource_url")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        return cls(**defaults)


@dataclass
class DiscogsArtistBase:
    """
    Base dataclass for all the Discogs Artist response and attribute.
    """

    id: int


@dataclass
class DiscogsArtistMember(DiscogsArtistBase):
    name: str
    is_active: t.Optional[bool] = None

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = ("id", "name", "active")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["is_active"] = defaults.pop("active", None)

        return cls(**defaults)


@dataclass
class DiscogsArtist(DiscogsArtistBase):
    name_variations: t.List[str] = field(default_factory=list)
    profile: str = ""
    members: t.List[DiscogsArtistMember] = field(default_factory=list)
    images: t.List[DiscogsImage] = field(default_factory=list)

    data: t.Dict[str, t.Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = (
            "id",
            "namevariations",
            "profile",
            "members",
            "images",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["name_variations"] = defaults.pop("namevariations", None)

        defaults["members"] = [
            DiscogsArtistMember.from_data(member)
            for member in defaults.pop("members", [])
        ]

        return cls(**defaults, data=data)


@dataclass
class DiscogsReleaseArtist(DiscogsArtistBase):
    name: str

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = ("id", "name")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        return cls(**defaults)


@dataclass
class DiscogsReleaseTrackArtist(DiscogsArtistBase):
    name: str
    role: t.Optional[str] = None

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = ("id", "name", "role")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        return cls(**defaults)


@dataclass
class DiscogsReleaseTrack:
    title: str
    duration: int
    position: t.Optional[str] = None

    artists: t.List[DiscogsReleaseTrackArtist] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = ("title", "duration", "position", "extraartists")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        if "duration" in defaults:
            defaults["duration"] = transform_duration(defaults.pop("duration"))

        artists = defaults.pop("extraartists", [])
        defaults["artists"] = [
            DiscogsReleaseTrackArtist.from_data(artist) for artist in artists
        ]

        return cls(**defaults)


@dataclass
class DiscogsRelease:
    id: int
    title: str
    year: int
    artists: t.List[DiscogsReleaseArtist] = field(default_factory=list)
    tracks: t.List[DiscogsReleaseTrack] = field(default_factory=list)
    styles: t.List[str] = field(default_factory=list)

    # Identifiers
    barcode: t.Optional[str] = None

    data: t.Dict[str, t.Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = (
            "id",
            "title",
            "year",
            "artists",
            "styles",
            "identifiers",
            "tracklist",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["artists"] = [
            DiscogsReleaseArtist.from_data(artist)
            for artist in defaults.pop("artists", [])
        ]

        defaults["tracks"] = [
            DiscogsReleaseTrack.from_data(track)
            for track in defaults.pop("tracklist", [])
        ]

        identifiers = defaults.pop("identifiers")

        # Extract the barcode identifier.
        barcode_identifier: t.Dict[str, str] = next(
            filter(lambda x: x["type"] == "Barcode", identifiers), {}
        )
        defaults["barcode"] = barcode_identifier.get("value") or None

        return cls(**defaults, data=data)


@dataclass
class DiscogsSearchResult:
    id: int
    type: DiscogsTypeLiterals
    title: str = ""
    url: t.Optional[str] = None

    data: t.Dict[str, t.Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = ("id", "type", "title", "uri")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        if "uri" in defaults:
            defaults["url"] = f"https://discogs.com{defaults.pop('uri')}"

        return cls(**defaults, data=data)
