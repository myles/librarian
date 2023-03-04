from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from requests import Session
from requests.auth import AuthBase

from ..settings import Settings
from ..utils.http_client import HttpClient

DiscogsCurrencyLiterals = Literal[
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


def transform_duration(value: str) -> Optional[int]:
    """
    Format a Discogs duration type.
    """
    if not value:
        return None

    minutes, seconds = value.split(":")
    return (int(minutes) * 60) + int(seconds)


@dataclass
class DiscogsImage:
    type: Literal["primary", "secondary"]
    height: int
    width: int
    resource_url: str

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
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
    is_active: Optional[bool] = None

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = ("id", "name", "active")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["is_active"] = defaults.pop("active", None)

        return cls(**defaults)


@dataclass
class DiscogsArtist(DiscogsArtistBase):
    name_variations: List[str] = field(default_factory=list)
    profile: str = ""
    members: List[DiscogsArtistMember] = field(default_factory=list)

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = (
            "id",
            "namevariations",
            "profile",
            "members",
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
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = ("id", "name")
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        return cls(**defaults)


@dataclass
class DiscogsReleaseTrackArtist(DiscogsArtistBase):
    name: str
    role: Optional[str] = None

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
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
    position: Optional[str] = None

    artists: List[DiscogsReleaseTrackArtist] = field(default_factory=list)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
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
    artists: List[DiscogsReleaseArtist] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = (
            "id",
            "title",
            "year",
            "artists",
            "styles",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        defaults["artists"] = [
            DiscogsReleaseArtist.from_data(artist)
            for artist in defaults.pop("artists", [])
        ]

        return cls(**defaults, data=data)


class DiscogsAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Discogs token={self.token}"
        return r


class DiscogsClient(HttpClient):
    def __init__(
        self,
        base_url: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        super().__init__(session=session)

        if Settings.DISCOGS_PERSONAL_ACCESS_TOKEN is not None:
            self.session.auth = DiscogsAuth(
                token=Settings.DISCOGS_PERSONAL_ACCESS_TOKEN,
            )

        if base_url is None:
            base_url = "https://api.discogs.com"

        self.base_url = base_url

    def get_release(
        self,
        release_id: int,
        currency: Optional[DiscogsCurrencyLiterals] = None,
        **kwargs,
    ) -> DiscogsRelease:
        """
        Get a Discogs release.
        """
        params: Dict[str, Any] = kwargs.pop("params", {})

        if currency is not None:
            params["curr_abbr"] = currency

        _, response = self.request(
            method="GET",
            url=f"{self.base_url}/releases/{release_id}",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        data = response.json()

        return DiscogsRelease.from_data(data)

    def get_artist(self, artist_id: int, **kwargs) -> DiscogsArtist:
        """
        Get a Discogs artist.
        """
        _, response = self.request(
            method="GET",
            url=f"{self.base_url}/artists/{artist_id}",
            **kwargs,
        )
        response.raise_for_status()
        data = response.json()

        return DiscogsArtist.from_data(data)
