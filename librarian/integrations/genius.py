import datetime
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

from requests import Session
from requests.auth import AuthBase

from ..settings import Settings
from ..utils.http_client import HttpClient

TextFormatLiterals = Literal["dom", "plain", "html"]


@dataclass
class GeniusReferent:
    id: int

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)

        safe_keys = ("id",)
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        return cls(**defaults, data=data)


@dataclass
class GeniusSearchHit:
    id: int
    full_title: str
    type: str

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        defaults = deepcopy(data)
        defaults_type = defaults.pop("type")
        defaults_result = defaults.pop("result")

        safe_keys = ("id", "full_title", "type")
        to_remove = [k for k in defaults_result.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults_result[key]

        return cls(type=defaults_type, **defaults_result, data=data)


@dataclass
class GeniusSong:
    id: int
    title: str
    artist_names: str
    release_date: Optional[datetime.date] = None

    description_dom: Optional[Dict[str, Any]] = None
    description_html: Optional[str] = None
    description_plain: Optional[str] = None

    data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: Dict[str, Any]):
        try:
            song_data = data["response"]["song"]
        except KeyError:
            raise ValueError("Provided data is not a song response.")

        defaults = deepcopy(song_data)

        safe_keys = (
            "id",
            "title",
            "artist_names",
            "release_date",
            "description",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        if "release_date" in defaults:
            defaults["release_date"] = datetime.date.fromisoformat(
                defaults["release_date"]
            )

        description = defaults.pop("description", {})
        if "dom" in description:
            defaults["description_dom"] = description["dom"]
        elif "html" in description:
            defaults["description_html"] = description["html"]
        elif "plain" in description:
            defaults["description_plain"] = description["plain"]

        return cls(**defaults, data=song_data)


class GeniusAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class GeniusClient(HttpClient):
    def __init__(
        self,
        base_url: Optional[str] = None,
        session: Optional[Session] = None,
    ):
        super().__init__(session=session)

        if Settings.GENIUS_CLIENT_ACCESS_TOKEN is not None:
            self.session.auth = GeniusAuth(
                token=Settings.GENIUS_CLIENT_ACCESS_TOKEN,
            )

        if base_url is None:
            base_url = "https://api.genius.com"

        self.base_url = base_url

    def get_referents(
        self,
        created_by_id: int = None,
        song_id: int = None,
        web_page_id: int = None,
        text_format: Optional[
            Union[TextFormatLiterals, List[TextFormatLiterals]]
        ] = "dom",
        **kwargs,
    ):
        """
        Returns a list of referents from Genius.
        """
        if song_id is not None and web_page_id is not None:
            raise ValueError(
                "You can only pass song_id or web_page_id, not both."
            )

        params: Dict[str, Any] = kwargs.pop("params", {})

        if created_by_id is not None:
            params["created_by_id"] = created_by_id

        if song_id is not None:
            params["song_id"] = song_id

        if web_page_id is not None:
            params["web_page_id"] = web_page_id

        if text_format is not None:
            if isinstance(text_format, str):
                text_format = [text_format]

            params["text_format"] = ",".join(text_format)

        _, response = self.request(
            method="GET",
            url=f"{self.base_url}/referents",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        data = response.json()
        referents = data["response"]["referents"]

        return [GeniusReferent.from_data(referent) for referent in referents]

    def get_song(
        self,
        song_id: int,
        text_format: Optional[
            Union[TextFormatLiterals, List[TextFormatLiterals]]
        ] = "dom",
        **kwargs,
    ) -> GeniusSong:
        """
        Get an artist by their ID from Genius.
        """
        params: Dict[str, Any] = kwargs.pop("params", {})

        if text_format is not None:
            if isinstance(text_format, str):
                text_format = [text_format]

            params["text_format"] = ",".join(text_format)

        _, response = self.request(
            method="GET",
            url=f"{self.base_url}/songs/{song_id}",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        data = response.json()

        return GeniusSong.from_data(data)

    def search(self, query: str, **kwargs) -> List[GeniusSearchHit]:
        """
        Search for artists and songs from Genius.
        """
        params: Dict[str, Any] = kwargs.pop("params", {})
        params["q"] = query

        _, response = self.request(
            method="GET",
            url=f"{self.base_url}/search",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        data = response.json()
        hits = data["response"]["hits"]

        return [GeniusSearchHit.from_data(hit) for hit in hits]
