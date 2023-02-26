from importlib.metadata import version
from typing import Dict, Literal, Optional, Tuple

from requests import PreparedRequest, Request, Response, Session

RequestReturn = Tuple[PreparedRequest, Response]
MethodType = Literal["GET", "POST", "PATCH", "DELETE", "PUT"]


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
        method: MethodType,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> RequestReturn:
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
