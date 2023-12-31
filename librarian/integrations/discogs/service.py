import typing as t

from requests import Session
from requests.auth import AuthBase

from ...settings import Settings
from ...utils.http_client import HttpClient
from . import data


class DiscogsAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = f"Discogs token={self.token}"
        return r


class DiscogsClient(HttpClient):
    def __init__(
        self,
        base_url: t.Optional[str] = None,
        session: t.Optional[Session] = None,
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
        currency: t.Optional[data.DiscogsCurrencyLiterals] = None,
        **kwargs,
    ) -> data.DiscogsRelease:
        """
        Get a Discogs release.
        """
        params: t.Dict[str, t.Any] = kwargs.pop("params", {})

        if currency is not None:
            params["curr_abbr"] = currency

        _, response = self.get(
            url=f"{self.base_url}/releases/{release_id}",
            params=params,
            **kwargs,
        )
        response.raise_for_status()
        response_data = response.json()

        return data.DiscogsRelease.from_data(response_data)

    def get_artist(self, artist_id: int, **kwargs) -> data.DiscogsArtist:
        """
        Get a Discogs artist.
        """
        _, response = self.get(
            url=f"{self.base_url}/artists/{artist_id}",
            **kwargs,
        )
        response.raise_for_status()
        response_data = response.json()

        return data.DiscogsArtist.from_data(response_data)

    def search(
        self,
        query: t.Optional[str] = None,
        type: t.Optional[data.DiscogsTypeLiterals] = None,
        barcode: t.Optional[str] = None,
        **kwargs,
    ) -> t.Generator[data.DiscogsSearchResult, None, None]:
        """
        Search Discogs.
        """
        params: t.Dict[str, t.Any] = kwargs.pop("params", {})

        if query is not None:
            params["query"] = query

        if type is not None:
            params["type"] = type

        if barcode is not None:
            params["barcode"] = barcode

        next_url = f"{self.base_url}/database/search"

        while next_url is not None:
            _, response = self.get(
                url=next_url,
                params=params,
                **kwargs,
            )
            response.raise_for_status()
            response_data = response.json()

            # We are going to use the parameters from the pagination next URL,
            # so we need clear the params and update the next_url variables.
            params = {}
            next_url = response_data["pagination"]["urls"].get("next")

            for result in response_data["results"]:
                yield data.DiscogsSearchResult.from_data(result)
