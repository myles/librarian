from importlib.metadata import version
from typing import Dict, Literal, Optional, Tuple

from requests import PreparedRequest, Request, Response, Session

MethodLiterals = Literal["GET", "POST", "PATCH", "DELETE", "PUT"]


class HttpClient:
    def __init__(self, session: Optional[Session] = None):
        if session is None:
            self.session = Session()
        else:
            self.session = session

        user_agent = (
            f"librarian/{version('librarian')}"
            f" (+https://library.mylesbraithwaite.com/)"
        )
        self.session.headers.update({"User-Agent": user_agent})

    def request(
        self,
        method: MethodLiterals,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Tuple[PreparedRequest, Response]:
        request = Request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            **kwargs,
        )
        prepare_request = self.session.prepare_request(request)
        response = self.session.send(prepare_request, stream=stream)
        return prepare_request, response

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Tuple[PreparedRequest, Response]:
        return self.request(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            stream=stream,
            **kwargs,
        )

    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Tuple[PreparedRequest, Response]:
        return self.request(
            method="POST",
            url=url,
            headers=headers,
            params=params,
            stream=stream,
            **kwargs,
        )

    def patch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Tuple[PreparedRequest, Response]:
        return self.request(
            method="PATCH",
            url=url,
            headers=headers,
            params=params,
            stream=stream,
            **kwargs,
        )

    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Tuple[PreparedRequest, Response]:
        return self.request(
            method="DELETE",
            url=url,
            headers=headers,
            params=params,
            stream=stream,
            **kwargs,
        )

    def put(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Tuple[PreparedRequest, Response]:
        return self.request(
            method="PUT",
            url=url,
            headers=headers,
            params=params,
            stream=stream,
            **kwargs,
        )
