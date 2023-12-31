import typing as t

from requests import Session
from requests.auth import AuthBase

from ...settings import Settings
from ...utils.http_client import HttpClient
from . import data


class GeniusAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class GeniusClient(HttpClient):
    def __init__(
        self,
        base_url: t.Optional[str] = None,
        session: t.Optional[Session] = None,
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
        created_by_id: t.Optional[int] = None,
        song_id: t.Optional[int] = None,
        web_page_id: t.Optional[int] = None,
        text_format: t.Optional[
            t.Union[data.TEXT_FORMAT_LITERAL, t.List[data.TEXT_FORMAT_LITERAL]]
        ] = "dom",
        **kwargs,
    ) -> t.List[data.GeniusReferent]:
        """
        Returns a list of referents from Genius.
        """
        if song_id is not None and web_page_id is not None:
            raise ValueError(
                "You can only pass song_id or web_page_id, not both."
            )

        params: t.Dict[str, t.Any] = kwargs.pop("params", {})

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

        _, response = self.get(
            url=f"{self.base_url}/referents",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        response_data = response.json()
        referents = response_data["response"]["referents"]

        return [
            data.GeniusReferent.from_data(referent) for referent in referents
        ]

    def get_song(
        self,
        song_id: int,
        text_format: t.Optional[
            t.Union[data.TEXT_FORMAT_LITERAL, t.List[data.TEXT_FORMAT_LITERAL]]
        ] = "dom",
        **kwargs,
    ) -> data.GeniusSong:
        """
        Get an artist by their ID from Genius.
        """
        params: t.Dict[str, t.Any] = kwargs.pop("params", {})

        if text_format is not None:
            if isinstance(text_format, str):
                text_format = [text_format]

            params["text_format"] = ",".join(text_format)

        _, response = self.get(
            url=f"{self.base_url}/songs/{song_id}",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        response_data = response.json()

        return data.GeniusSong.from_data(response_data)

    def search(self, query: str, **kwargs) -> t.List[data.GeniusSearchHit]:
        """
        Search for artists and songs from Genius.
        """
        params: t.Dict[str, t.Any] = kwargs.pop("params", {})
        params["q"] = query

        _, response = self.get(
            url=f"{self.base_url}/search",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        response_data = response.json()
        hits = response_data["response"]["hits"]

        return [data.GeniusSearchHit.from_data(hit) for hit in hits]
